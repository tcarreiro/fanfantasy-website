import pandas as pd
#import espnfantasyfootball as espn
#import espnsecrets
import espnfanfanstasy as espn
import os


def connect_league(year):
  league = espn.FantasyLeague(league_id=270838,
                              year=year,
                              swid=os.getenv("swid"),
                              espn_s2=os.getenv("espn_s2"))
  return league
