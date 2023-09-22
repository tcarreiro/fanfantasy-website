from flask import Blueprint, render_template, request
import fetchESPN as fetch
from datetime import date
import pandas as pd

views = Blueprint('views', __name__)


def load_info(year=0, week=0):
    current_year = date.today().isocalendar().year
    current_week = date.today().isocalendar().week-35
    weekday = date.today().isocalendar().weekday
    if weekday < 2:
        current_week = current_week-1 # Só passa a semana depois da terça feira
    if current_week < 1:
        current_year = current_year-1 # Só passa o ano no começo da temporada

    if (year != 0):
        current_year = year
    
    if (week != 0):
        current_week=week

    league = fetch.connect_league(current_year)
    
    return [league, current_week, weekday, current_year]


##############################
##### ROUTES
##############################

@views.route('/')
def home():
    current_year = date.today().isocalendar().year
    current_week = date.today().isocalendar().week-35
    weekday = date.today().isocalendar().weekday
    if weekday < 2:
        current_week = current_week-1 # Só passa a semana depois da terça feira
    if current_week < 1:
        current_year = current_year-1 # Só passa o ano no começo da temporada

    league = fetch.connect_league(current_year)
    print(type(league))

    matchup_data = league.get_schedule_data(week=current_week)
    #pd.DataFrame(columns=['Week', 'Logo1', 'Name1', 'Abbrev1', 'Record1',
    #                                 'Score1', 'Logo2', 'Name2', 'Abbrev2', 'Record2', 'Score2', 'Type'])
    teams_data = league.get_division_standings()
    #pd.DataFrame(columns=['id 1', 'Division 2', 'Logo 3', 'Name', 'Wins', 'Losses', 'Ties', '%', 'PF', 'PA'])

    return render_template("home.html", matchup_data=matchup_data, teams_data=teams_data, current_year=current_year, current_week=current_week, weekday=weekday)
    