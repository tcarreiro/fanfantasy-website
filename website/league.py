from flask import Blueprint, render_template, request
import fetchESPN as fetch
import datetime
import pandas as pd
import request_folder.nfl_requests as espnrequest
import os


def format_date(year=0, week=0):
    current_year = datetime.date.today().isocalendar().year
    current_week = datetime.date.today().isocalendar().week-35
    weekday = datetime.date.today().isocalendar().weekday
    time = datetime.datetime.now()
    hour= time.hour

    if weekday < 2:
        current_week = current_week-1 # Só passa a semana depois da terça feira
    elif weekday == 2:
        if hour <= 3:
            current_week = current_week-1 # Só passa a semana depois da terça feira 03:00
    if current_week < 1:
        current_year = current_year-1 # Só passa o ano no começo da temporada

    if (year != 0):
        current_year = year
    
    if (week != 0):
        current_week=week

    return [current_week, weekday, current_year, time]
def home():
    print('Home carregada')
    # League está como global. Se ainda não tiver sido definida, será na primeira vez que home for carregada (talvez seja necessário fazer esse check em todos os endpoints)
    if not fetch.league:
        fetch.league = fetch.connect_league(os.getenv("league_id"), 2023)
        print('Conexão com API feita')
    else:
        print('Conexão já existia')

    [current_week, weekday, current_year, time] = format_date()

    if request.method == "GET":
        matchup_data = fetch.league.get_schedule_data(week=current_week)

    return [matchup_data, current_week, weekday, current_year, time]

#def classificacao():
    #[league, current_week, weekday, current_year, time] = load_info()
    #matchup_data = league.get_schedule_data(week=current_week)

    #if request.method == 'POST':
    #    if (request.form.get('form_selector') == 'tabs'):
    #        tab = request.form.get('action')
    #        year = int(request.form.get('selected_season'))
    #    elif (request.form.get('form_selector') == 'year'):
    #        tab = request.form.get('standing_tab')
    #        year = int(request.form.get('season'))
    #    if (year != current_year):
    #        [league, week, day, league_year, time] = load_info(year=year)
    #    else:
    #        league_year=current_year
    #else:
    #    tab = 'group'
    #    league_year = current_year

    #if tab == 'group':
    #    teams_data = league.get_division_standings()
    #if tab == 'overall':
    #    teams_data = league.get_overall_standings()

    #teams_data['%'] = teams_data['%'].round(3)
    #teams_data['PF'] = teams_data['PF'].round(1)
    #teams_data['PA'] = teams_data['PA'].round(1)
    
    #return [matchup_data, teams_data, tab, current_year, current_week, weekday, league_year, time]

#def fanfastats():
    #[league, current_week, weekday, current_year, time] = load_info()

    #teams_data = league.get_division_standings()
    #if request.method=='POST':
    #    texto=request.form.get('name')
    #else:
    #    texto = 'Liga'
    #matchup_data = league.get_schedule_data(week=current_week)

    #return [matchup_data, teams_data, current_year, current_week, weekday, time]

#def rankings():
    # Matchup header
    #[league, current_week, weekday, current_year, time] = load_info()
    #matchup_data = league.get_schedule_data(week=current_week)

    # Persistent handlers
    #if request.method == 'POST':
    #    tab = 'rankings' # Put inside "if" in case more than 1 tab available
    #    if (request.form.get('form_selector') == 'parameters_search'):
    #        week = int(request.form.get('week'))
    #        year = int(request.form.get('season'))
    #    #elif for handling "tab" if needed
    #    #elif (request.form.get('form_selector') == 'tabs'):
    #    #    week = int(request.form.get('selected_week'))
    #    #    year = int(request.form.get('selected_season'))
    #    if (year != current_year or week != current_week):
    #        [league, league_week, day, league_year, time] = load_info(year=year, week=week)
    #        print('ok')
            
    #    else:
    #        tab = 'rankings'
    #        league_year=current_year
    #        league_week=current_week
    #else:
    #    # Initi default "tab"
    #    tab = 'rankings'
    #    league_year = current_year
    #    league_week = current_week

    # "tab" handlers and data acquisition
    #if tab == 'rankings':
    #    teams_data = league.get_overall_standings()

    #teams_data['%'] = teams_data['%'].round(3)
    #teams_data['PF'] = teams_data['PF'].round(1)
    #teams_data['PA'] = teams_data['PA'].round(1)
    
    #return [matchup_data, teams_data, tab, current_year, current_week, weekday, league_year,league_week, time]