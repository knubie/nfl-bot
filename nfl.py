import willie
import nflgame
import threading
import re

def set_interval(func, sec):
  def func_wrapper():
    set_interval(func, sec)
    func()
  t = threading.Timer(sec, func_wrapper)
  t.start()
  return t

play_by_play_loop = False
last_play = ""

@willie.module.commands('scores')
def scores(bot, trigger):
  games = nflgame.live.current_games(kind='REG')
  if games:
    for game in games:
      bot.say(game.nice_score())
  else:
    bot.say('No games in progress.')

@willie.module.commands('score')
def score(bot, trigger):
  teams = re.match(r"(\w+) @ (\w+)", trigger.group(2))
  away, home = teams.group(1, 2)
  year, week = nflgame.live.current_year_and_week()
  away = away.upper()
  home = home.upper()
  game = nflgame.one(year, week, home, away, kind='REG', started=True)
  if game:
    bot.say(game.nice_score())
  else:
    bot.say('No games found.')

@willie.module.commands('play')
def play(bot, trigger):
  global play_by_play_loop
  teams = re.match(r"(\w+) @ (\w+)", trigger.group(2))
  away, home = teams.group(1, 2)
  away = away.upper()
  home = home.upper()
  year, week = nflgame.live.current_year_and_week()
  def say_play():
    global last_play
    game = nflgame.one(year, week, home, away, started=True)
    current_play = list(reversed(list(game.drives.plays().sort("gameclock", descending=True))))[0].__str__()
    if current_play != last_play:
      last_play = current_play
      formatted = re.sub("\((\w+), ", r"http://i.nflcdn.com/static/site/6.0/img/teams/\1/\1_logo-20x20.gif **", last_play)
      formatted = formatted.replace(")", "** -", 1)
      formatted = re.sub("\((\d{1,2}:\d{1,2})\)", r"*\1* - ", formatted)
      bot.say(formatted)

  if not play_by_play_loop:
    bot.say('starting play by play')
    say_play()
    play_by_play_loop = True
    set_interval(say_play, 20)

@willie.module.commands('stop')
def stop(bot, trigger):
  global play_by_play_loop
  play_by_play_loop = False
