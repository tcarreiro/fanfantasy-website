import pandas as pd
#import espnfantasyfootball as espn
#import espnsecrets
import espnfanfanstasy as espn
import os


def connect_league(year):
  league = espn.FantasyLeague(
      league_id=270838,
      year=year,
      swid='{EF48DE5F-1F0E-48AE-88DE-5F1F0E48AE49}',
      espn_s2=
      'AECwbeUHvzCBW2qUIrKziD1vvKrWIRnNTX3Vx6tq9hzh4OQrJxkacrU%2B2vXzdA2Ay6zzfcsGg66OSelPd3G8pQ62EshzmwGSZtADIaawOiryrlHg4s3yfQQBFvQN2SVOTK8QCDnStvLyxEvQ3RJ6EMdUMlM%2FU6YWuvbqPgcxWYKfnm8UxZrOhsXto26WO%2FdhpvB%2BebWzBggkQv3EkZieDQUSF9WRTuaXGgjvp90r7XagTWPCgrDCzIxbGuUPyU9pDaTPMFom7U2V62gNKa55o%2FxvKpDemIrh3OeSEeXpf95E62WQwMA81hjtw3rLrXCmk7Q%3D'
  )
  return league
