import context


class TestSendMessage(context.slouch.testing.CommandTestCase):

    bot_class = context.TimerBot
    config = {'start_fmt': '{:%Y}', 'stop_fmt': '{.days}'}

    def test_message_colon_delimiter(self):
        res = self.send_message('help start')
        self.assertIn('Start a timer.', res)

    def test_message_space_delimiter(self):
        res = self.send_message('help start', delimiter=' ')
        self.assertIn('Start a timer.', res)
