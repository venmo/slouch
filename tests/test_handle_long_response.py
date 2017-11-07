import context

class TestHandleLongResponse(context.slouch.testing.CommandTestCase):
    bot_class = context.TimerBot
    config = {'start_fmt': '{:%Y}', 'stop_fmt': '{.days}'}
    normal_text = (
                "@genericmention: this is generic mention message contains a URL <http://foo.com/>"
                "\n@genericmention: this generic mention message contains a :fast_parrot: and :nyancat_big:"
                "\n"
            )
    over_limit_text = normal_text * 50 # 8550 chars


    def test_handle_long_message_api(self):
        _res = {
            'type': 'message',
            'text': self.normal_text,
            'channel': None,
        }
        responses = self.bot._handle_long_response(_res)
        self.assertEqual(len(responses), 1)
        self.assertEqual(responses, [{
            'type': 'message',
            'text': self.normal_text,
            'channel': None
            }])

    def test_handle_long_message_over_limit_api(self):

        _res = {
            'type': 'message',
            'text': self.over_limit_text,
            'channel': None,
        }
        responses = self.bot._handle_long_response(_res)
        self.assertEqual([len(r['text']) for r in responses], [3932, 3933, 685])
        self.assertEqual(len(responses), 3)

    def test_handle_long_message_rtm(self):
        responses = self.bot._handle_long_response(self.normal_text)
        self.assertEqual(responses, [self.normal_text])
        self.assertEqual(len(responses), 1)

    def test_handle_long_message_over_limit_rtm(self):
        responses = self.bot._handle_long_response(self.over_limit_text)

        self.assertEqual([len(r) for r in responses], [3932, 3933, 685])
        self.assertEqual(len(responses), 3)


