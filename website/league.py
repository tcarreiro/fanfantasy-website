from flask import Blueprint, render_template, request, jsonify
import fetchESPN as fetch
import datetime
import pandas as pd
import request_folder.nfl_requests as espnrequest
import os

def check_if_update_needed(current_week, current_year):
    fetch.league = fetch.connect_league(os.getenv("league_id"), current_year)

    control_panel = get_last_updated_week()
    # Se a diferença de semanas chegar em 2, devemos atualizar os DataFrames até a semana anterior
    if (current_week > control_panel['last_standing_update_week'][0] + 1):
        delete_standings_from_season(current_year)
        fetch.league.season_standings_history_to_csv()
        fetch.league.add_matchup_to_csv(fetch.league.get_matchup_data_by_week(week=current_week-1))

        att_control_panel(week=current_week-1)

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

    check_if_update_needed(current_week, current_year)

    return [current_week, weekday, current_year, time]

# Reimportar matchups
def reimport_matchup_history_from_API(lastSeason):
    # Zerar .csv atual
    new_matchup_df = pd.DataFrame()
    new_matchup_df.to_csv(os.getenv('csv_path')+os.getenv('matchup_history'))

    for season in range(2018,lastSeason+1):
        fetch.league = fetch.connect_league(os.getenv("league_id"), season)
        fetch.league.season_matchup_history_to_csv()

def get_matchup_by_week_season(week, season):
    matchup_df = pd.read_csv(os.getenv('csv_path')+os.getenv('matchup_history'))
    matchup_df.drop(matchup_df.columns[0], axis=1, inplace=True)

    # Retirar todas as season não selecionadas
    matchup_df.drop(matchup_df[matchup_df['Season'] != season].index, inplace=True)
    # Retirar todas as semanas não selecionadas
    matchup_df.drop(matchup_df[matchup_df['Week'] != week].index, inplace=True)
    
    return matchup_df

# Essa função só será necessária caso eu queira importar o calendário inteiro da season em andamento e ir atualizando
# A outra opção é importar apenas as já finalizadas e ir adicionando quando uma rodada acaba É ASSIM QUE ESTÁ NO MOMENTO
#def att_matchup(id:int, profile_pic:str, first_name:str, last_name:str, team:str, position, is_rookie, draft_board_list):
#    matchup_df = pd.read_csv(os.getenv("csv_path")+os.getenv('matchup_history'))
#    matchup_df.drop(matchup_df.columns[0], axis=1, inplace=True)

#    matchup_df['profile_pic'][id] = profile_pic
#    matchup_df['team'][id] = team.replace(' ','_').lower()
#    matchup_df['position'][id] = position
#    matchup_df['first_name'][id] = first_name

#    matchup_df.to_csv(os.getenv("csv_path")+os.getenv('matchup_history'))

# Reimportar standings
def reimport_standings_history_from_API(lastSeason):
    # Zerar .csv atual
    new_standings_df = pd.DataFrame()
    new_standings_df.to_csv(os.getenv('csv_path')+os.getenv('standings_history'))

    for season in range(2018,lastSeason+1):
        fetch.league = fetch.connect_league(os.getenv("league_id"), season)
        fetch.league.season_standings_history_to_csv()

def get_standings_from_season(season):
    standings_df = pd.read_csv(os.getenv('csv_path')+os.getenv('standings_history'))
    standings_df.drop(standings_df.columns[0], axis=1, inplace=True)

    # Retirar todas as semanas que não estejam acabadas
    standings_df.drop(standings_df[standings_df['Season'] != season].index, inplace=True)
    return standings_df

def delete_standings_from_season(season):
    standings_df = pd.read_csv(os.getenv('csv_path')+os.getenv('standings_history'))
    standings_df.drop(standings_df.columns[0], axis=1, inplace=True)

    # Retirar as standings da Season
    standings_df.drop(standings_df[standings_df['Season'] == season].index, inplace=True)
    standings_df.to_csv(os.getenv('csv_path')+os.getenv('standings_history'))

def get_last_updated_week():
    control_panel_df = pd.read_csv(os.getenv('csv_path')+os.getenv('control_panel'))
    control_panel_df.drop(control_panel_df.columns[0], axis=1, inplace=True)

    return control_panel_df

# Controle de atualização dos standings e resultados da rodada. Deverá ser usado no controle de quando as DataFrames serão atualizadas
def att_control_panel(week):
    control_panel_df = pd.read_csv(os.getenv('csv_path')+os.getenv('control_panel'))
    control_panel_df.drop(control_panel_df.columns[0], axis=1, inplace=True)

    control_panel_df['last_standing_update_week'][0] = week
    control_panel_df['last_matchup_update_week'][0] = week

    control_panel_df.to_csv(os.getenv("csv_path")+os.getenv('control_panel'))