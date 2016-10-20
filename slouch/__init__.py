import functools
import inspect
import json
import logging
import pprint
import sys
import traceback

from docopt import docopt, DocoptExit
from slacker import Slacker
import websocket

from . import testing  # noqa
from ._version import __version__  # noqa


def _dual_decorator(func):
    """This is a decorator that converts a paramaterized decorator for
    no-param use.

    source: http://stackoverflow.com/questions/3888158
    """

    @functools.wraps(func)
    def inner(*args, **kwargs):
        if ((len(args) == 1 and not kwargs and callable(args[0])
             and not (type(args[0]) == type and issubclass(args[0], BaseException)))):
            return func()(args[0])
        elif len(args) == 2 and inspect.isclass(args[0]) and callable(args[1]):
            return func(args[0], **kwargs)(args[1])
        else:
            return func(*args, **kwargs)
    return inner


def help(opts, bot, _):
    """Usage: help [<command>]

    With no arguments, print the form of all supported commands.
    With an argument, print a detailed explanation of a command.
    """
    command = opts['<command>']
    if command is None:
        return bot.help_text()

    if command not in bot.commands:
        return "%r is not a known command" % command

    return bot.commands[command].__doc__


class _CommandMeta(type):
    """
    If the commands dict is a class field on Bot, then all subclasses will share one registry.

    This metaclass initializes a separate registry on each class.
    """

    def __new__(cls, name, bases, dct):
        new_cls = super(_CommandMeta, cls).__new__(cls, name, bases, dct)
        new_cls.commands = {}

        return new_cls


class Bot(object):
    """
    A Bot connects to Slack using the `RTM API <https://api.slack.com/rtm>`__
    and responds to public messages that are directed to it with username-
    or at-mentions.

    Manage the Bot's channels in Slack itself with the `/join` command.
    A Bot can be in multiple Slack channels (though state is not isolated by channel).
    """

    __metaclass__ = _CommandMeta

    @classmethod
    @_dual_decorator
    def command(cls, name=None):
        """
        A decorator to convert a function to a command.

        A command's docstring must be a docopt usage string.
        See docopt.org for what it supports.

        Commands receive three arguments:

          * opts: a dictionary output by docopt
          * bot: the Bot instance handling the command (eg for storing state between commands)
          * event: the Slack event that triggered the command (eg for finding the message's sender)

        Additional options may be passed in as keyword arguments:

          * name: the string used to execute the command (no spaces allowed)

        They must return one of three things:

          * a string of response text. It will be sent via the RTM api to the channel where
            the bot received the message. Slack will format it as per https://api.slack.com/docs/message-formatting.
          * None, to send no response.
          * a dictionary of kwargs representing a message to send via https://api.slack.com/methods/chat.postMessage.
            Use this to send more complex messages, such as those with custom link text or DMs.
            For example, to respond with a DM containing custom link text, return
            `{'text': '<http://example.com|my text>', 'channel': event['user'], 'username': bot.name}`.
            Note that this api has higher latency than the RTM api; use it only when necessary.
        """
        # adapted from https://github.com/docopt/docopt/blob/master/examples/interactive_example.py

        def decorator(func):

            @functools.wraps(func)
            def _cmd_wrapper(rest, *args, **kwargs):
                try:
                    usage = _cmd_wrapper.__doc__.partition('\n')[0]
                    opts = docopt(usage, rest)
                except (SystemExit, DocoptExit) as e:
                    # opts did not match
                    return str(e)

                return func(opts, *args, **kwargs)

            cls.commands[name or func.__name__] = _cmd_wrapper

            return _cmd_wrapper
        return decorator

    @classmethod
    def help_text(cls):
        """Return a slack-formatted list of commands with their usage."""
        docs = [cmd_func.__doc__ for cmd_func in cls.commands.values()]

        # Don't want to include 'usage: ' or explanation.
        usage_lines = [doc.partition('\n')[0] for doc in docs]
        terse_lines = [line[len('Usage: '):] for line in usage_lines]
        terse_lines.sort()
        return '\n'.join(['Available commands:\n'] + terse_lines)

    def __init__(self, slack_token, config):
        """
        Do not override this to perform implementation-specific setup;
        use :func:`prepare_bot` instead.

        No IO will be done until :func:`run_forever` is called (unless :func:`prepare_bot`
        is overridden to perform some).

        :param slack_token: a Slack api token.
        :param config: an arbitrary dictionary for implementation-specific configuration.
          The same object is stored as the `config` attribute and passed to prepare methods.
        """
        #: the same config dictionary passed to init.
        self.config = config
        self._current_message_id = 0

        #: a Logger (``logging.getLogger(__name__)``).
        self.log = logging.getLogger(__name__)

        # This doesn't perform IO.
        #: a `Slacker <https://github.com/os/slacker>`__ instance created with `slack_token`.
        self.slack = Slacker(slack_token)

        #: the bot's Slack id.
        #: Not available until :func:`prepare_connection`.
        self.id = None

        #: the bot's Slack name.
        #: Not available until :func:`prepare_connection`.
        self.name = None

        #: the bot's Slack mention, equal to ``<@%s> % self.id`` .
        #: Not available until :func:`prepare_connection`.
        self.my_mention = None

        #: a `WebSocketApp <https://github.com/liris/websocket-client>`__ instance.
        #: Not available until :func:`prepare_connection`.
        self.ws = None

        self.prepare_bot(self.config)

    def prepare_bot(self, config):
        """
        Override to perform implementation-specific setup.

        This is called once by :func:`__init__` and is not called on connection restarts.
        """
        pass

    def prepare_connection(self, config):
        """
        Override to perform per-connection setup.

        This is called by run_forever and on connection restarts.
        """
        pass

    def run_forever(self):
        """Run the bot, blocking forever."""
        res = self.slack.rtm.start()
        self.log.info("current channels: %s",
                      ','.join(c['name'] for c in res.body['channels']
                               if c['is_member']))
        self.id = res.body['self']['id']
        self.name = res.body['self']['name']
        self.my_mention = "<@%s>" % self.id

        self.ws = websocket.WebSocketApp(
            res.body['url'],
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open)
        self.prepare_connection(self.config)
        self.ws.run_forever()

    def _bot_identifier(self, message):
        """Return the identifier used to address this bot in this message.
        If one is not found, return None.

        :param message: a message dict from the slack api.
        """

        text = message['text']

        formatters = [
            lambda identifier: "%s " % identifier,
            lambda identifier: "%s:" % identifier,
        ]
        my_identifiers = [formatter(identifier) for identifier in [self.name, self.my_mention] for formatter in formatters]

        for identifier in my_identifiers:
            if text.startswith(identifier):
                self.log.debug("sent to me:\n%s", pprint.pformat(message))
                return identifier

        return None

    def _handle_command_response(self, res, event):
        """Either send a message (choosing between rtm and postMessage) or ignore the response.

        :param event: a slacker event dict
        :param res: a string, a dict, or None.
          See the command docstring for what these represent.
        """

        response_handler = None

        if isinstance(res, basestring):
            response_handler = functools.partial(self._send_rtm_message, event['channel'])
        elif isinstance(res, dict):
            response_handler = self._send_api_message

        if response_handler is not None:
            response_handler(res)

    def _send_rtm_message(self, channel_id, text):
        """Send a Slack message to a channel over RTM.

        :param channel_id: a slack channel id.
        :param text: a slack message. Serverside formatting is done
          in a similar way to normal user message; see
          `Slack's docs <https://api.slack.com/docs/formatting>`__.
        """

        message = {
            'id': self._current_message_id,
            'type': 'message',
            'channel': channel_id,
            'text': text,
        }
        self.ws.send(json.dumps(message))

        self._current_message_id += 1

    def _send_api_message(self, message):
        """Send a Slack message via the chat.postMessage api.

        :param message: a dict of kwargs to be passed to slacker.
        """

        self.slack.chat.post_message(**message)
        self.log.debug("sent api message %r", message)

    # Websocket callbacks.
    def _on_message(self, ws, raw_event):
        try:
            event = json.loads(raw_event)
            if 'type' not in event or event['type'] != 'message':
                return

            if 'text' not in event:
                # These are mostly changed messages, which we don't respond to right now.
                return

            identifier = self._bot_identifier(event)
            if not identifier:
                return

            body = event['text'].partition(identifier)[2].strip()
            cmd, _, rest = body.partition(' ')

            if cmd in self.commands:
                try:
                    res = self.commands[cmd](rest, self, event)
                except Exception as e:
                    self.log.exception("%s while handling %r", e, body)

                    # Send the exception and the final line of the traceback.
                    # TODO this doesn't always pick out the right line.
                    t, v, tb = sys.exc_info()
                    res = ''.join(traceback.format_exception_only(t, v))
                    tb_entries = traceback.extract_tb(tb, 3)
                    res += ''.join(traceback.format_list(tb_entries[2:]))
            else:
                res = "Unrecognized command.\n%s" % self.help_text()

            self.log.debug("received command response %r", res)
            self._handle_command_response(res, event)

        except Exception as e:
            # websocket-client swallows exceptions in callbacks
            self.log.exception("%s during _on_message. event:\n%s", e, pprint.pformat(raw_event))

    def _on_error(self, ws, error):
        self.log.error(error)

    def _on_close(self, ws, code, reason):
        self.log.warning("websocket closed. code: %r, reason: %r", code, reason)

        # Attempt to reconnect.
        # No need to reset _current_message_id: slack just requires ids that are unique per session.
        self.run_forever()

    def _on_open(self, ws):
        self.log.info("websocket opened")
