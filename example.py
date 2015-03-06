#!/usr/bin/env python

"""
TimerBot can manage multiple stopwatch-style timers from Slack.

Usage:
  timerbot  [--start_fmt=<start_fmt>] [--stop_fmt=<stop_fmt>] <slack_token>
  timerbot --help

Options:
  --start_fmt=<start_fmt>  Format string for start responses (given a datetime) [default: {}]
  --stop_fmt=<stop_fmt>  Format string for start responses (given a timedelta) [default: {}]
  --help       Show this screen.
"""

import datetime
import logging
import sys

from docopt import docopt
from slouch import Bot, help


class TimerBot(Bot):
    def prepare_bot(self, config):
        # It's fine to start implementation-specific state directly on the bot.
        self.start_fmt = config['start_fmt']
        self.stop_fmt = config['stop_fmt']
        self.timers = {}


# This is optional; it provides a help command that lists and gives details on other commands.
TimerBot.command(help)


@TimerBot.command
def start(opts, bot, event):
    """Usage: start [--name=<name>]

    Start a timer.

    Without _name_, start the default timer.
    To run more than one timer at once, pass _name_ to start and stop.
    """

    name = opts['--name']

    now = datetime.datetime.now()
    bot.timers[name] = now

    return bot.start_fmt.format(now)


@TimerBot.command
def stop(opts, bot, event):
    """Usage: stop [--name=<name>] [--notify=<slack_username>]

    Stop a timer.

    _name_ works the same as for `start`.
    If given _slack_username_, reply with an at-mention to the given user.
    """

    name = opts['--name']
    slack_username = opts['--notify']

    now = datetime.datetime.now()
    delta = now - bot.timers.pop(name)

    response = bot.stop_fmt.format(delta)

    if slack_username:
        mention = ''

        # The slack api (provided by https://github.com/os/slacker) is available on all bots.
        users = bot.slack.users.list().body['members']
        for user in users:
            if user['name'] == slack_username:
                mention = "<@%s>" % user['id']
                break
        response = "%s: %s" % (mention, response)

    return response

if __name__ == '__main__':
    args = docopt(__doc__)
    slack_token = args['<slack_token>']
    config = {
        'start_fmt': args['--start_fmt'],
        'stop_fmt': args['--stop_fmt'],
    }

    log = logging.getLogger('slouch')
    log.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        fmt=('%(asctime)s %(name)s'
             ' (%(filename)s:%(lineno)s)'
             ' %(levelname)s:'
             ' %(message)s'),
        datefmt='%H:%M:%S'))
    log.addHandler(console_handler)

    bot = TimerBot(slack_token, config)
    bot.run_forever()
