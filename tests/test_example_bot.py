from libfaketime import fake_time

import context


class TestExample(context.slouch.testing.CommandTestCase):

    bot_class = context.TimerBot
    config = {'start_fmt': '{:%Y}', 'stop_fmt': '{.days}'}

    def test_help(self):
        res = self.send_message('help')
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
            res = self.send_message('start')
            self.assertEqual(res, '2016')

        with fake_time('2017'):
            res = self.send_message('stop')
            self.assertEqual(res, '365')

    def test_named_timer(self):
        with fake_time('2016'):
            res = self.send_message('start --name=mytimer')
            self.assertEqual(res, '2016')

        with fake_time('2017'):
            res = self.send_message('stop --name=mytimer')
            self.assertEqual(res, '365')

    def test_missing_timer(self):
        res = self.send_message('stop --name=mytimer')
        self.assertTrue(res.startswith("KeyError: u'mytimer'"), res)

    def test_notify(self):
        res = self.send_message('start')

        self.bot.slack.users.list().body = {'members': [{'name': 'user', 'id': 'U123'}]}
        res = self.send_message('stop --notify=user')
        self.assertTrue(res.startswith('<@U123>'), res)
