slouch
======

Slouch is a lightweight Python framework for building cli-inspired Slack bots.

Here's an example bot built with Slouch:

.. code-block:: python

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


For more details, check out the docs at https://slouch.readthedocs.org or see a `full example bot <https://github.com/venmo/slouch/blob/master/example.py>`__.
