import json
from unittest import TestCase

from mock import Mock, patch, create_autospec


class CommandTestCase(TestCase):
    """A TestCase for unit testing bot requests and responses.

    To use it:

      * provide your bot in *bot_class* (and optionally a config).
      * use self.send_message inside your test cases.
        It returns what your command returns.
    """

    bot_class = None
    config = {}

    def setUp(self):
        self.bot = self.bot_class('slack_token', self.config.copy())
        self.bot.name = str(self.bot_class)
        self.bot.my_mention = None  # we'll just send test messages by name, not mention.

        # This patch is introspected to find command responses (and also prevents interaction with slack).
        self.bot._handle_command_response = create_autospec(self.bot._handle_command_response)

        self.ws = Mock()

        self.slack_patcher = patch.object(self.bot, 'slack', autospec=True)
        self.slack_mock = self.slack_patcher.start()

    def tearDown(self):
        self.slack_patcher.stop()

    def send_message(self, command, message_delimiter=':', **event):
        """Return the bot's response to a given command.

        :param command: the message to the bot.
          Do not include the bot's name, just the part after the colon.
        :param event: kwargs that will override the event sent to the bot.
          Useful when your bot expects message from a certain user or channel.
        """

        _event = {
            'type': 'message',
            'text': "%s%s%s" % (self.bot.name, message_delimiter, command),
            'channel': None,
        }

        self.assertTrue(_event['text'].startswith("%s%s" % (self.bot.name, message_delimiter)))

        _event.update(event)

        self.bot._on_message(self.ws, json.dumps(_event))

        args, _ = self.bot._handle_command_response.call_args
        return args[0]
