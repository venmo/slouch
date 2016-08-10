import json
from unittest import TestCase

from libfaketime import fake_time
from mock import Mock, patch, create_autospec

from context import TimerBot


class CommandTestCase(TestCase):
    """A TestCase for unit testing bot requests and responses.

    To use it:

      * provide your bot in *bot_class* (and optionally a config).
      * use self.send_test_message inside your test cases.
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

    def send_test_message(self, command, **event):
        """Return the bot's response to a given command."""

        _event = {
            'type': 'message',
            'text': "%s: %s" % (self.bot.name, command),
            'channel': None,
        }
        _event.update(event)

        self.bot._on_message(self.ws, json.dumps(_event))

        args, _ = self.bot._handle_command_response.call_args
        return args[0]


class TestExample(CommandTestCase):

    bot_class = TimerBot
    config = {'start_fmt': '{:%Y}', 'stop_fmt': '{.days}'}

    def test_help(self):
        res = self.send_test_message('help')
        self.assertEqual(
            res,
            '\n'.join(['Available commands:',
                       '',
                       'help [<command>]',
                       'start [--name=<name>]',
                       'stop [--name=<name>] [--notify=<slack_username>]',
                       ]))

    def test_default_timer(self):
        with fake_time('2016'):
            res = self.send_test_message('start')
            self.assertEqual(res, '2016')

        with fake_time('2017'):
            res = self.send_test_message('stop')
            self.assertEqual(res, '365')

    def test_named_timer(self):
        with fake_time('2016'):
            res = self.send_test_message('start --name=mytimer')
            self.assertEqual(res, '2016')

        with fake_time('2017'):
            res = self.send_test_message('stop --name=mytimer')
            self.assertEqual(res, '365')

    def test_missing_timer(self):
        res = self.send_test_message('stop --name=mytimer')
        self.assertTrue(res.startswith("KeyError: u'mytimer'"), res)

    def test_notify(self):
        res = self.send_test_message('start')

        self.bot.slack.users.list().body = {'members': [{'name': 'user', 'id': 'U123'}]}
        res = self.send_test_message('stop --notify=user')
        self.assertTrue(res.startswith('<@U123>'), res)
