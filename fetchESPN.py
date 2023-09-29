import pandas as pd
#import espnfantasyfootball as espn
#import espnsecrets
import espnfanfanstasy as espn
import os

league = None
def connect_league(league_id, year):
  global league
  league = espn.FantasyLeague(league_id=league_id,
                              year=year,
                              swid=os.getenv("swid"),
                              espn_s2=os.getenv("espn_s2"))
  return league
