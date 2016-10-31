import threading
from slackbot.bot import respond_to
from slackbot.bot import listen_to
import nflgame
import re
import json

# car -> carolina
# gb -> gbay

play_by_play_loop = False
loop = None
index = 0
prev_desc = ""
year = 2016
week = 1
home = 'WAS'
away = 'PIT'
season = 'REG'

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

def set_interval(func, sec, arg):
    def func_wrapper():
        set_interval(func, sec, arg)
        func(arg)
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

@respond_to('hi', re.IGNORECASE)
def hi(message):
    message.reply('I can understand hi or HI!')
    # react with thumb up emoji
    message.react('+1')

@respond_to('I love you')
def love(message):
    message.reply('I love you too!')

@listen_to('Can someone help me?')
def help(message):
    # Message is replied to the sender (prefixed with @user)
    message.reply('Yes, I can!')

    # Message is sent on the channel
    # message.send('I can help everybody!')

def bold(substr, string):
    return re.sub(substr, r"*\1*", string)

@listen_to('score')
def score(message):
    game = nflgame.one(year, week, home, away, season)
    message.send_webapi(':' + away + ': *' + str(game.score_away) + ' - ' + str(game.score_home) + '* :' + home + ':')


@listen_to('stop')
def stop_play_by_play(message):
    global play_by_play_loop
    if play_by_play_loop:
        message.send_webapi('Stopping play-by-play.')
        play_by_play_loop = False
        loop.cancel()
    else:
        message.send_webapi('Nothin to stop.')

@listen_to('start')
def start_play_by_play(message):
    global play_by_play_loop
    global loop

    if play_by_play_loop:
        message.send_webapi('I\'ve already been started. Say \'stop\' first to start a different game.')
    else:
        message.send_webapi('Starting play-by-play for :' + away + ': @ :' + home + ':')
        play_by_play_loop = True
        loop = set_interval(say_play, 5, message)


def say_play(message):
    global index
    global prev_desc

    game = nflgame.one(year, week, home, away, season)

    # desc = list(reversed(list(game.drives.plays())))[0].__str__()

    # if game.has_started
    play = list(reversed(list(game.drives.plays())))[0]
    # else
    # play = list(game.drives.plays())[index]
    desc = play.desc

    print(desc)

    index = index + 1
    if desc != prev_desc:
        print('different')
        prev_desc = desc

        # Team with posession
        posteam = play.data['posteam']

        time = play.data['time']
        # 'END QUARTER 1' etc, returns u'' for time
        if time == u'': time = u'0:00'

        quarter = str(play.data['qtr'])
        down = play.data['down']
        yards_to_go = str(play.data['ydstogo'])
        note = play.data['note']
        if note != None and note != u'PENALTY':
            note = note + ' - '
        else:
            note = u''

        if down == 0:
            down_and_yards = u''
        else:
            down_and_yards = ordinal(down) + ' and ' + yards_to_go

        yard_line = play.data['yrdln']
        prefix = u''
        if yard_line != u'':
            team_yard_line = re.search("(\w+) \d+", yard_line).group(1)
            yard_line_int = int(re.search("\w+ (\d+)", yard_line).group(1))
            if team_yard_line == posteam:
                raw_yards = str((50 - yard_line_int) + 50) + ' yards'
            else:
                raw_yards = str(yard_line_int) + ' yards'

            relative_yard_line = ':' + team_yard_line.lower() + ': ' + str(yard_line_int)
        else:
            raw_yards = u''
            relative_yard_line = u''


        if yard_line != u'' and down != 0:
            prefix = u' @ '

        # TODO: Add flair for when play is in RED ZONE
        
        # TODO: Account for odd messages:
        # Timeout #1 by DET at 08:53.
        # END QUARTER 1
        # Timeout #2 by BAL at 01:28. BAL charged with final time out due to injured player.
        # Two-Minute Warning
        # END GAME

        # meta = re.search("\(\w+, ([^\)]*)\)", last_play).group(1)
        # meta = re.sub("\(\w+, ([^\)]*)\) ", "", last_play)

        desc = re.sub("\(\w+, ([^\)]*)\) ", "", desc)

        desc = re.sub("\((\d{0,2}:\d{0,2})\) ", "", desc)

        # Names
        desc = re.sub("([A-Z]{1}\.[A-Z]+[a-zA-Z]+)", r"_\1_", desc)

        # Yard
        desc = bold("(-*\d{1,2} yards*)", desc)
        # desc = re.sub("(-*\d{1,2} yards*)", r"*\1*", desc)

        # Injured
        desc = bold("(injured)", desc)
        # desc = re.sub("(injured)", r"*\1*", desc)

        # Incomplete
        desc = bold("(incomplete)", desc)
        # desc = re.sub("(incomplete)", r"*\1*", desc)

        # Intercepted
        desc = bold("(INTERCEPTED)", desc)
        # desc = re.sub("(INTERCEPTED)", r"*\1*", desc)

        # Touchdown
        desc = bold("(TOUCHDOWN)", desc)
        # desc = re.sub("(TOUCHDOWN)", r"*\1*", desc)

        # Good
        desc = bold("(GOOD)", desc)
        # desc = re.sub("(GOOD)", r"*\1*", desc)

        # Muff
        desc = bold("(MUFFS)", desc)
        # desc = re.sub("(MUFFS)", r"*\1*", desc)

        # Recovered
        desc = bold("(RECOVERED)", desc)
        # desc = re.sub("(RECOVERED)", r"*\1*", desc)

        # Nullified
        desc = bold("(NULLIFIED)", desc)
        # desc = re.sub("(NULLIFIED)", r"*\1*", desc)

        # Penalty
        # penalty = re.search(" (Penalty .*)", desc, re.IGNORECASE)
        # only_penalty = re.search("PENALTY", desc)

        parts = re.split('\. ', desc)
        parts = [p + '.' if not p.endswith('.') else p for p in parts]

        attachments = []

        for i, part in enumerate(parts):
            if i == 0:
                attachment = {
                    'author_name': time + ' - Q' + quarter,
                    # 'title': meta,
                    'title': note + down_and_yards + prefix + relative_yard_line,
                }
            else:
                attachment = {}

            attachment['mrkdwn_in'] = ['text']

            penalty = re.search("Penalty", part, re.IGNORECASE)
            injured = re.search("injured", part, re.IGNORECASE)
            recovered = re.search("recovered", part, re.IGNORECASE)

            if penalty != None:
                attachment['color'] = '#F2D300'
                part = re.sub("([^A-Z])([A-Z]{2,3})([^A-Z])", lambda m: m.group(1) + ':' + m.group(2).lower() + ': ', part, 1)

            if recovered != None:
                part = re.sub("([^A-Z])([A-Z]{2,3})(-)", lambda m: m.group(1) + ':' + m.group(2).lower() + ': ', part, 1)

            if injured != None:
                attachment['color'] = '#B4161D'

            attachment['text'] = part

            attachments.append(attachment)

        message.send_webapi(':' + posteam.lower() + ':', json.dumps(attachments))
