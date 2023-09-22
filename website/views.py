from flask import Blueprint, render_template, request
import fetchESPN as fetch
import datetime
import pandas as pd

views = Blueprint('views', __name__)

def load_info(year=0, week=0):
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

    league = fetch.connect_league(current_year)
    
    return [league, current_week, weekday, current_year, time]

##############################
##### ROUTES
##############################

@views.route('/')
def home():
    [league, current_week, weekday, current_year, time] = load_info()

    matchup_data = league.get_schedule_data(week=current_week)
    teams_data = league.get_division_standings()

    return render_template("home.html", matchup_data=matchup_data, teams_data=teams_data, current_year=current_year, current_week=current_week, weekday=weekday, time=time)

@views.route('/classificacao', methods=['GET', 'POST'])
def classificacao():
    [league, current_week, weekday, current_year, time] = load_info()
    matchup_data = league.get_schedule_data(week=current_week)

    if request.method == 'POST':
        if (request.form.get('form_selector') == 'tabs'):
            tab = request.form.get('action')
            year = int(request.form.get('selected_season'))
        elif (request.form.get('form_selector') == 'year'):
            tab = request.form.get('standing_tab')
            year = int(request.form.get('season'))
        if (year != current_year):
            [league, week, day, league_year] = load_info(year=year)
        else:
            league_year=current_year
    else:
        tab = 'group'
        league_year = current_year

    if tab == 'group':
        teams_data = league.get_division_standings()
    if tab == 'overall':
        teams_data = league.get_overall_standings()

    teams_data['%'] = teams_data['%'].round(3)
    teams_data['PF'] = teams_data['PF'].round(1)
    teams_data['PA'] = teams_data['PA'].round(1)
    
    return render_template("classificacao.html", matchup_data=matchup_data, teams_data=teams_data,
                           tab=tab, current_year=current_year, current_week=current_week, weekday=weekday, league_year=league_year, time=time)

@views.route('/fanfastats', methods=['GET', 'POST'])
def fanfastats():
    [league, current_week, weekday, current_year, time] = load_info()

    teams_data = league.get_division_standings()
    if request.method=='POST':
        texto=request.form.get('name')
    else:
        texto = 'Liga'
    matchup_data = league.get_schedule_data(week=current_week)

    return render_template("fanfastats.html", matchup_data=matchup_data, teams_data=teams_data,
                           current_year=current_year, current_week=current_week, weekday=weekday, time=time)

@views.route('/rankings', methods=['GET', 'POST'])
def rankings():
    # Matchup header
    [league, current_week, weekday, current_year, time] = load_info()
    matchup_data = league.get_schedule_data(week=current_week)

    # Persistent handlers
    if request.method == 'POST':
        tab = 'rankings' # Put inside "if" in case more than 1 tab available
        if (request.form.get('form_selector') == 'parameters_search'):
            week = int(request.form.get('week'))
            year = int(request.form.get('season'))
        #elif for handling "tab" if needed
        #elif (request.form.get('form_selector') == 'tabs'):
        #    week = int(request.form.get('selected_week'))
        #    year = int(request.form.get('selected_season'))
        if (year != current_year or week != current_week):
            [league, league_week, day, league_year] = load_info(year=year, week=week)
            print('ok')
            
        else:
            tab = 'rankings'
            league_year=current_year
            league_week=current_week
    else:
        # Initi default "tab"
        tab = 'rankings'
        league_year = current_year
        league_week = current_week

    # "tab" handlers and data acquisition
    if tab == 'rankings':
        teams_data = league.get_overall_standings()

    teams_data['%'] = teams_data['%'].round(3)
    teams_data['PF'] = teams_data['PF'].round(1)
    teams_data['PA'] = teams_data['PA'].round(1)
    
    return render_template("rankings.html", matchup_data=matchup_data, teams_data=teams_data, tab=tab,
                           current_year=current_year, current_week=current_week, weekday=weekday, league_year=league_year, league_week=league_week, time=time)

