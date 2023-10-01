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
        att_expected_wins_by_season_by_week(season=current_year, week=current_week-1)
        att_expected_wins_by_season(season=current_year)

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

def att_expected_wins_by_season_by_week(season, week):
    matchup_df = pd.read_csv(os.getenv('csv_path')+os.getenv('matchup_history'))
    matchup_df.drop(matchup_df.columns[0], axis=1, inplace=True)
    aux_matchup_df = matchup_df.copy()
    
    # Retirar todas as temporadas que não sejam a atual
    aux_matchup_df.drop(aux_matchup_df[aux_matchup_df['Season'] != season].index, inplace=True)
    aux_matchup_df.drop(aux_matchup_df[aux_matchup_df['Week'] != week].index, inplace=True)
    aux_matchup_df.reset_index(drop=True, inplace=True)

    # Ranquear pontuações da rodada e transformar em vitórias esperadas
    score_df = pd.DataFrame(columns=['Score1'])
    score_df['Score1'] = aux_matchup_df['Score1']
    score_df2 = pd.DataFrame(columns=['Score1'])
    score_df2['Score1'] = aux_matchup_df['Score2']
    score_df = pd.concat([score_df,score_df2], axis=0, ignore_index=True)
    score_df['Score1'] = score_df.rank(ascending=False, method='min')
    for i in range(0, int(len(score_df)/2)):
        aux_matchup_df['ExpectedWins1'][i]=((len(score_df))-score_df['Score1'][i])/(len(score_df)-1)
        aux_matchup_df['ExpectedWins2'][i]=((len(score_df))-score_df['Score1'][i+len(score_df)/2])/(len(score_df)-1)
    
    # Apagar infos na df original
    matchup_df.drop(matchup_df[(matchup_df['Season'] == season) & (matchup_df['Week'] == week)].index, inplace=True)

    # Concatenar resultado com o backup do arquivo e redefinir os IDs
    matchup_df = pd.concat([matchup_df, aux_matchup_df])
    matchup_df = matchup_df.sort_values(by=['Season', 'Week'], ascending=[True, True])
    matchup_df.reset_index(drop=True, inplace=True)
    
    # Salvar dados no arquivo
    matchup_df.to_csv(os.getenv('csv_path')+os.getenv('matchup_history'))
    
def att_expected_wins_by_season(season):
    standings_df = pd.read_csv(os.getenv('csv_path')+os.getenv('standings_history'))
    standings_df.drop(standings_df.columns[0], axis=1, inplace=True)
    matchup_df = pd.read_csv(os.getenv('csv_path')+os.getenv('matchup_history'))
    matchup_df.drop(matchup_df.columns[0], axis=1, inplace=True)
    aux_standings_df = standings_df.copy()
    aux_matchup_df = matchup_df.copy()
    
    # Retirar todas as temporadas que não sejam a atual
    aux_matchup_df.drop(aux_matchup_df[aux_matchup_df['Season'] != season].index, inplace=True)
    aux_matchup_df.reset_index(drop=True, inplace=True)

    # Retirar todas as temporadas que não sejam a atual
    aux_standings_df.drop(aux_standings_df[aux_standings_df['Season'] != season].index, inplace=True)
    aux_standings_df.reset_index(drop=True, inplace=True)

    for team in range(0, len(aux_standings_df)):
        aux_standings_df['ExpectedWins'][team] = 0
        for match in range(0, len(aux_matchup_df)):
            if (aux_matchup_df['Type'][match] == 'Regular'):
                if (aux_standings_df['Name'][team] == aux_matchup_df['Name1'][match]):
                    aux_standings_df['ExpectedWins'][team] = aux_standings_df['ExpectedWins'][team] + aux_matchup_df['ExpectedWins1'][match]
                if (aux_standings_df['Name'][team] == aux_matchup_df['Name2'][match]):
                    aux_standings_df['ExpectedWins'][team] = aux_standings_df['ExpectedWins'][team] + aux_matchup_df['ExpectedWins2'][match]
    
    # Apagar infos na df original
    standings_df.drop(standings_df[standings_df['Season'] == season].index, inplace=True)

    # Concatenar resultado com o backup do arquivo e redefinir os IDs
    standings_df = pd.concat([standings_df, aux_standings_df])
    standings_df = standings_df.sort_values(by=['Season', 'id'], ascending=[True, True])
    standings_df.reset_index(drop=True, inplace=True)
    

    # Salvar dados no arquivo
    standings_df.to_csv(os.getenv('csv_path')+os.getenv('standings_history'))