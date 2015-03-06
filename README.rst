slouch
======

Slouch is a lightweight Python framework for building cli-inspired Slack bots.

Here's an example bot built with Slouch::

    from slouch import Bot, help

    class PingBot(Bot):
        pass

    @PingBot.command
    def pingme(opts, bot, event):
        """Usage: pingme [--message=<message>]

        Respond with an at-mention to the sender.

        Pass _message_ to include a message in the response.
        """

        sender_slack_id = event['user']
        message = opts['<message>']
        response = ""

        if message is not None:
            response = message

        return "<@%s> %s" % (sender_slack_id, response)


Implementation overview:

    * communication with Slack uses the `Real Time Messaging api <https://api.slack.com/rtm>`__
    * usage docstrings use `docopt <https://github.com/docopt/docopt>`__


TODO:

    * docs
    * full example file, with how to run, help builtin, etc
    * testing (include things to make integration testing easy?)
