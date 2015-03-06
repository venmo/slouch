slouch: build cli-inspired Slack bots
=====================================

Here's an example Slack bot built with slouch:

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


For more details, see the :ref:`api reference <api>` or the `full example bot <https://github.com/venmo/slouch/blob/master/example.py>`__.
