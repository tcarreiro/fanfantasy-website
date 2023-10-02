import requests
import pandas as pd
import os
import json

class FantasyLeague:
    '''
    ESPN Fantasy Football League class for pulling data from the ESPN API
    '''
    BASE_URL = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}"
    POSITION_MAPPING = {
        0: 'QB',
        4: 'WR',
        2: 'RB',
        23: 'FLEX',
        6: 'TE',
        16: 'D/ST',
        17: 'K',
        20: 'Bench',
        21: 'IR',
        '': 'NA'
    }

    def __init__(self, league_id, year, espn_s2, swid):
        self.league_id = league_id
        self.year = year
        self.espn_s2 = espn_s2
        self.swid = swid
        self.base_url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{self.year}/segments/0/leagues/{self.league_id}"
        self.cookies = {
            "swid": self.swid,
            "espn_s2": self.espn_s2
        }
        self.matchup_df = None
        self.team_df = None

    # Adiciona uma df no fim de um .csv
    def add_data_to_csv(self, df, data_type:str):
        if data_type == 'Matchup':
            data = 'matchup_history'
        elif data_type == 'Standings':
            data = 'standings_history'

        # Fazer backup dos dados e deletar a primeira coluna (duplicação dos IDs)
        cur_df = pd.read_csv(os.getenv('csv_path')+os.getenv(data))
        cur_df.drop(cur_df.columns[0], axis=1, inplace=True)

        # Concatenar resultado com o backup do arquivo e redefinir os IDs
        cur_df = pd.concat([cur_df, df])
        cur_df.reset_index(drop=True, inplace=True)
        
        # Salvar dados no arquivo
        cur_df.to_csv(os.getenv('csv_path')+os.getenv(data))
        
    # Retorna a DataFrame das matchups de uma Semana específica do ano que está conectado {{self.year}}
    def get_matchup_data_by_week(self, week):
        # Pull team and matchup data from the URL
        matchup_response = requests.get(self.base_url,
                                        params={"leagueId": self.league_id,
                                                "seasonId": self.year,
                                                "matchupPeriodId": 1,
                                                "view": "mMatchup"},
                                        cookies=self.cookies)

        team_response = requests.get(self.base_url,
                                        params={"leagueId": self.league_id,
                                                "seasonId": self.year,
                                                "matchupPeriodId": 1,
                                                "view": "mTeam"},
                                        cookies=self.cookies)

        # Transform the response into a json
        matchup_json = matchup_response.json()
        team_json = team_response.json()

        # Transform both of the json outputs into DataFrames
        matchup_df = pd.json_normalize(matchup_json['schedule'])
        team_df = pd.json_normalize(team_json['teams'])

        # Retirar todas as semanas que não seja a atual
        matchup_df.drop(matchup_df[matchup_df['matchupPeriodId'] != week].index, inplace=True)

        # Define the column names needed
        matchup_column_names = {
            'matchupPeriodId': 'Week',
            'away.teamId': 'Team1',
            'away.rosterForCurrentScoringPeriod.appliedStatTotal': 'CurrentStatsTotal1',
            #'away.rosterForCurrentScoringPeriod.entries': 'CurrentEntries1', # Para o futuro
            'away.totalPoints': 'Score1',
            'home.teamId': 'Team2',
            'home.rosterForCurrentScoringPeriod.appliedStatTotal': 'CurrentStatsTotal2',
            #'home.rosterForCurrentScoringPeriod.entries': 'CurrentEntries2', # Para o futuro
            'home.totalPoints': 'Score2',
            'winner': 'Winner',
        }

        team_column_names = {
            'id': 'id',
            'logo': 'Logo',
            'name': 'Name',
            'abbrev': 'Abbrev',
            'record.overall.losses': 'Losses',
            'record.overall.ties': 'Ties',
            'record.overall.wins': 'Wins'
        }

        # Alterar nomes das colunas
        matchup_df = matchup_df.reindex(columns=matchup_column_names).rename(
            columns=matchup_column_names)
        team_df = team_df.reindex(columns=team_column_names).rename(
            columns=team_column_names)

        # Adiciona a coluna com o tipo da matchup (temporada regular ou playoff)
        matchup_df['Type'] = ['Regular' if week <=
                                14 else 'Playoff' for week in matchup_df['Week']]
        
        # Adiciona a coluna com a temporada (mais fácil para encontrar uma matchup específica depois)
        matchup_df['Season'] = self.year

        # Colunas para rankings
        # Vitórias esperadas
        team_df['ExpectedWins'] = 0

        # Pontos feitos nas vitórias
        team_df['PFonWins'] = 0

        # Pontos sofridos nas derrotas
        team_df['PAonLosses'] = 0

        # Pontos feitos nas derrotas
        team_df['PFonLosses'] = 0

        # Pontos sofridos nas vitórias
        team_df['PAonWins'] = 0 

        # Retira todas as colunas do DataFrame, exceto as listadas
        team_df = team_df.filter(['id', 'Logo', 'Name', 'Abbrev', 'Wins', 'Losses', 'Ties', 'ExpectedWins', 'PFonWins', 'PAonLosses', 'PFonLosses', 'PAonWins'])

        # (1) Renomear as colunas para mesclar os DataFrames e não ter conflitos com nomes iguais
        matchup_df = matchup_df.rename(columns={"Team1": "id"})
        
        # (1) Renomear as colunas para mesclar os DataFrames e não ter conflitos com nomes iguais
        matchup_df = matchup_df.merge(team_df, on=['id'], how='left')
        matchup_df = matchup_df.rename(columns={'Abbrev': 'Abbrev1'})
        matchup_df = matchup_df.rename(columns={'Wins': 'Wins1'})
        matchup_df = matchup_df.rename(columns={'Losses': 'Losses1'})
        matchup_df = matchup_df.rename(columns={'Ties': 'Ties1'})
        matchup_df = matchup_df.rename(columns={'Name': 'Name1'})
        matchup_df = matchup_df.rename(columns={'Logo': 'Logo1'})
        matchup_df = matchup_df.rename(columns={'ExpectedWins': 'ExpectedWins1'})
        matchup_df = matchup_df.rename(columns={'PFonWins': 'PFonWins1'})
        matchup_df = matchup_df.rename(columns={'PAonLosses': 'PAonLosses1'})
        matchup_df = matchup_df.rename(columns={'PFonLosses': 'PFonLosses1'})
        matchup_df = matchup_df.rename(columns={'PAonWins': 'PAonWins1'})

        # (1) Reordena as colunas após a primeira mescla
        matchup_df = matchup_df[['Season', 'Week', 'Winner', 'Logo1', 'Name1', 'Abbrev1', 'Wins1', 'Losses1', 'Ties1', 'Score1', 'CurrentStatsTotal1', 'ExpectedWins1', 'PFonWins1', 'PAonLosses1', 'PFonLosses1', 'PAonWins1',
                                 'Team2', 'Score2', 'CurrentStatsTotal2', 'Type']]

        # (2) Renomear as colunas para mesclar os DataFrames e não ter conflitos com nomes iguais
        matchup_df = matchup_df.rename(columns={"Team2": "id"})

        # (2) Renomear as colunas para mesclar os DataFrames e não ter conflitos com nomes iguais
        matchup_df = matchup_df.merge(team_df, on=['id'], how='left')
        matchup_df = matchup_df.rename(columns={'Abbrev': 'Abbrev2'})
        matchup_df = matchup_df.rename(columns={'Wins': 'Wins2'})
        matchup_df = matchup_df.rename(columns={'Losses': 'Losses2'})
        matchup_df = matchup_df.rename(columns={'Ties': 'Ties2'})
        matchup_df = matchup_df.rename(columns={'Name': 'Name2'})
        matchup_df = matchup_df.rename(columns={'Logo': 'Logo2'})
        matchup_df = matchup_df.rename(columns={'ExpectedWins': 'ExpectedWins2'})
        matchup_df = matchup_df.rename(columns={'PFonWins': 'PFonWins2'})
        matchup_df = matchup_df.rename(columns={'PAonLosses': 'PAonLosses2'})
        matchup_df = matchup_df.rename(columns={'PFonLosses': 'PFonLosses2'})
        matchup_df = matchup_df.rename(columns={'PAonWins': 'PAonWins2'})

        # (2) Reordena as colunas após a segunda mescla
        matchup_df = matchup_df[['Season', 'Week', 'Winner', 'Logo1', 'Name1', 'Abbrev1', 'Wins1', 'Losses1', 'Ties1', 'Score1', 'CurrentStatsTotal1', 'ExpectedWins1', 'PFonWins1', 'PAonLosses1', 'PFonLosses1', 'PAonWins1',
                                 'Logo2', 'Name2', 'Abbrev2', 'Wins2', 'Losses2', 'Ties2', 'Score2', 'CurrentStatsTotal2', 'ExpectedWins2', 'PFonWins2', 'PAonLosses2', 'PFonLosses2', 'PAonWins2', 'Type']]
        
        return matchup_df

    # Adiciona ao CSV todas as partidas já finalizadas da season conectada {{self.year}}
    def season_matchup_history_to_csv(self):
        # Fazer backup dos dados e deletar a primeira coluna (duplicação dos IDs)
        #cur_matchup_df = pd.read_csv(os.getenv('csv_path')+os.getenv('matchup_history'))
        #cur_matchup_df.drop(cur_matchup_df.columns[0], axis=1, inplace=True)

        matchup_response = requests.get(self.base_url,
                                    params={"leagueId": self.league_id,
                                            "seasonId": self.year,
                                            "matchupPeriodId": 1,
                                            "view": "mMatchup"},
                                    cookies=self.cookies)
        
        team_response = requests.get(self.base_url,
                                        params={"leagueId": self.league_id,
                                                "seasonId": self.year,
                                                "matchupPeriodId": 1,
                                                "view": "mTeam"},
                                        cookies=self.cookies)
        
        # Transforma a resposta em json
        matchup_json = matchup_response.json()
        team_json = team_response.json()

        # Transforma os json em DataFrame
        matchup_df = pd.json_normalize(matchup_json['schedule'])
        team_df = pd.json_normalize(team_json['teams'])

        # Retirar todas as semanas que não estejam acabadas
        #matchup_df.drop(matchup_df[matchup_df['winner'] == "UNDECIDED"].index, inplace=True)

        # Define the column names needed
        matchup_column_names = {
            'matchupPeriodId': 'Week',
            'away.teamId': 'Team1',
            'away.rosterForCurrentScoringPeriod.appliedStatTotal': 'CurrentStatsTotal1',
            #'away.rosterForCurrentScoringPeriod.entries': 'CurrentEntries1', # Para o futuro
            'away.totalPoints': 'Score1',
            'home.teamId': 'Team2',
            'home.rosterForCurrentScoringPeriod.appliedStatTotal': 'CurrentStatsTotal2',
            #'home.rosterForCurrentScoringPeriod.entries': 'CurrentEntries2', # Para o futuro
            'home.totalPoints': 'Score2',
            'winner': 'Winner',
        }

        team_column_names = {
            'id': 'id',
            'logo': 'Logo',
            'name': 'Name',
            'abbrev': 'Abbrev',
            'record.overall.losses': 'Losses',
            'record.overall.ties': 'Ties',
            'record.overall.wins': 'Wins',
        }

        # Alterar nomes das colunas
        matchup_df = matchup_df.reindex(columns=matchup_column_names).rename(
            columns=matchup_column_names)
        team_df = team_df.reindex(columns=team_column_names).rename(
            columns=team_column_names)

        # Adiciona a coluna com o tipo da matchup (temporada regular ou playoff)
        matchup_df['Type'] = ['Regular' if week <=
                                14 else 'Playoff' for week in matchup_df['Week']]
        
        # Adiciona a coluna com a temporada (mais fácil para encontrar uma matchup específica depois)
        matchup_df['Season'] = self.year

        # Colunas para rankings
        # Vitórias esperadas
        team_df['ExpectedWins'] = 0

        # Pontos feitos nas vitórias
        team_df['PFonWins'] = 0

        # Pontos sofridos nas derrotas
        team_df['PAonLosses'] = 0

        # Pontos feitos nas derrotas
        team_df['PFonLosses'] = 0

        # Pontos sofridos nas vitórias
        team_df['PAonWins'] = 0 

        # Retira todas as colunas do DataFrame, exceto as listadas
        team_df = team_df.filter(['id', 'Logo', 'Name', 'Abbrev', 'Wins', 'Losses', 'Ties', 'ExpectedWins', 'PFonWins', 'PAonLosses', 'PFonLosses', 'PAonWins'])

        # (1) Renomear as colunas para mesclar os DataFrames e não ter conflitos com nomes iguais
        matchup_df = matchup_df.rename(columns={"Team1": "id"})
        
        # (1) Renomear as colunas para mesclar os DataFrames e não ter conflitos com nomes iguais
        matchup_df = matchup_df.merge(team_df, on=['id'], how='left')
        matchup_df = matchup_df.rename(columns={'Abbrev': 'Abbrev1'})
        matchup_df = matchup_df.rename(columns={'Wins': 'Wins1'})
        matchup_df = matchup_df.rename(columns={'Losses': 'Losses1'})
        matchup_df = matchup_df.rename(columns={'Ties': 'Ties1'})
        matchup_df = matchup_df.rename(columns={'Name': 'Name1'})
        matchup_df = matchup_df.rename(columns={'Logo': 'Logo1'})
        matchup_df = matchup_df.rename(columns={'ExpectedWins': 'ExpectedWins1'})
        matchup_df = matchup_df.rename(columns={'PFonWins': 'PFonWins1'})
        matchup_df = matchup_df.rename(columns={'PAonLosses': 'PAonLosses1'})
        matchup_df = matchup_df.rename(columns={'PFonLosses': 'PFonLosses1'})
        matchup_df = matchup_df.rename(columns={'PAonWins': 'PAonWins1'})

        # (1) Reordena as colunas após a primeira mescla
        matchup_df = matchup_df[['Season', 'Week', 'Winner', 'Logo1', 'Name1', 'Abbrev1', 'Wins1', 'Losses1', 'Ties1', 'Score1', 'CurrentStatsTotal1', 'ExpectedWins1', 'PFonWins1', 'PAonLosses1', 'PFonLosses1', 'PAonWins1',
                                 'Team2', 'Score2', 'CurrentStatsTotal2', 'Type']]

        # (2) Renomear as colunas para mesclar os DataFrames e não ter conflitos com nomes iguais
        matchup_df = matchup_df.rename(columns={"Team2": "id"})

        # (2) Renomear as colunas para mesclar os DataFrames e não ter conflitos com nomes iguais
        matchup_df = matchup_df.merge(team_df, on=['id'], how='left')
        matchup_df = matchup_df.rename(columns={'Abbrev': 'Abbrev2'})
        matchup_df = matchup_df.rename(columns={'Wins': 'Wins2'})
        matchup_df = matchup_df.rename(columns={'Losses': 'Losses2'})
        matchup_df = matchup_df.rename(columns={'Ties': 'Ties2'})
        matchup_df = matchup_df.rename(columns={'Name': 'Name2'})
        matchup_df = matchup_df.rename(columns={'Logo': 'Logo2'})
        matchup_df = matchup_df.rename(columns={'ExpectedWins': 'ExpectedWins2'})
        matchup_df = matchup_df.rename(columns={'PFonWins': 'PFonWins2'})
        matchup_df = matchup_df.rename(columns={'PAonLosses': 'PAonLosses2'})
        matchup_df = matchup_df.rename(columns={'PFonLosses': 'PFonLosses2'})
        matchup_df = matchup_df.rename(columns={'PAonWins': 'PAonWins2'})

        # (2) Reordena as colunas após a segunda mescla
        matchup_df = matchup_df[['Season', 'Week', 'Winner', 'Logo1', 'Name1', 'Abbrev1', 'Wins1', 'Losses1', 'Ties1', 'Score1', 'CurrentStatsTotal1', 'ExpectedWins1', 'PFonWins1', 'PAonLosses1', 'PFonLosses1', 'PAonWins1',
                                 'Logo2', 'Name2', 'Abbrev2', 'Wins2', 'Losses2', 'Ties2', 'Score2', 'CurrentStatsTotal2', 'ExpectedWins2', 'PFonWins2', 'PAonLosses2', 'PFonLosses2', 'PAonWins2', 'Type']]
        
        # Concatena com dados no arquivo e reescreve
        self.add_data_to_csv(df=matchup_df,data_type='Matchup')

        # Concatenar resultado com o backup do arquivo e redefinir os IDs
        #cur_matchup_df = pd.concat([cur_matchup_df, matchup_df])
        #cur_matchup_df.reset_index(drop=True, inplace=True)
        
        # Salvar dados no arquivo
        #cur_matchup_df.to_csv(os.getenv('csv_path')+"teste_"+os.getenv('matchup_history'))

    # Adiciona ao CSV a standing atual da season conectada {{self.year}}
    def season_standings_history_to_csv(self):
        # Fazer backup dos dados e deletar a primeira coluna (duplicação dos IDs)
        #cur_standings_df = pd.read_csv(os.getenv('csv_path')+os.getenv('standings_history'))
        #cur_standings_df.drop(cur_standings_df.columns[0], axis=1, inplace=True)

        # Pull team and matchup data from the URL
        team_response = requests.get(self.base_url,
                                        params={"leagueId": self.league_id,
                                                "seasonId": self.year,
                                                "matchupPeriodId": 1,
                                                "view": "mTeam"},
                                        cookies=self.cookies)
        
        # Transforma a resposta em json
        team_json = team_response.json()

        # Transforma os json em DataFrame
        team_df = pd.json_normalize(team_json['teams'])

        team_column_names = {
            'id': 'id',
            'logo': 'Logo',
            'name': 'Name',
            'divisionId': 'Division',
            'playoffSeed': 'Seed',
            'abbrev': 'Abbrev',
            'record.overall.losses': 'Losses',
            'record.overall.ties': 'Ties',
            'record.overall.wins': 'Wins',
            'record.overall.percentage': '%',
            'record.overall.pointsAgainst': 'PA',
            'record.overall.pointsFor': 'PF',
        }

        # Alterar nomes das colunas
        team_df = team_df.reindex(columns=team_column_names).rename(
            columns=team_column_names)

        # Adiciona a coluna com a temporada (mais fácil para encontrar uma matchup específica depois)
        team_df['Season'] = self.year
        
        # Colunas para rankings
        # Vitórias esperadas
        team_df['ExpectedWins'] = 0

        # Pontos feitos nas vitórias
        team_df['PFonWins'] = 0

        # Pontos sofridos nas derrotas
        team_df['PAonLosses'] = 0

        # Pontos feitos nas derrotas
        team_df['PFonLosses'] = 0

        # Pontos sofridos nas vitórias
        team_df['PAonWins'] = 0 

        team_df = team_df[['Season', 'id', 'Division', 'Logo', 'Name', 'Abbrev', 'Seed', 'Wins', 'Losses', 'Ties', '%', 'PF', 'PA', 'ExpectedWins', 'PFonWins', 'PAonLosses', 'PFonLosses','PAonWins']]

        # Concatena com dados no arquivo e reescreve
        self.add_data_to_csv(df=team_df,data_type='Standings')

        # Concatenar resultado com o backup do arquivo e redefinir os IDs
        #cur_standings_df = pd.concat([cur_standings_df, team_df])
        #cur_standings_df.reset_index(drop=True, inplace=True)
        
        # Salvar dados no arquivo
        #cur_standings_df.to_csv(os.getenv('csv_path')+os.getenv('standings_history'))

