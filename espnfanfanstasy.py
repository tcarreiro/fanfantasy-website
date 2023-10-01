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

    def make_request(self, url, params, view):
        '''
        Initiate a request to the ESPN API
        '''
        params['view'] = view
        return requests.get\
            (url, params=params, cookies={"SWID": self.swid, "espn_s2": self.espn_s2}, timeout=30).json()

    def load_league(self, week):
        '''
        Load the league JSON from the ESPN API
        '''
        url = self.base_url.format(year=self.year, league_id=self.league_id)
        return self.make_request(url + '?view=mMatchup&view=mMatchupScore',
                                 params={'scoringPeriodId': week, 'matchupPeriodId': week}, view='mMatchup')

    def load_player_data(self, league_json, week):
        '''
        Load the player data from the league JSON
        '''
        player_name = []
        player_score_act = []
        player_score_proj = []
        player_roster_slot = []
        player_fantasy_team = []
        weeks = []


        # Loop through each team
        for team in range(0, len(league_json['teams'])):

            # Loop through each roster slot in each team
            for slot in range(0, len(league_json['teams'][team]['roster']['entries'])):
                # Append the week number to a list for each entry for each team
                weeks.append(week)
                # Append player name, player fantasy team, and player ro
                player_name.append(league_json['teams'][team]['roster']
                                ['entries'][slot]['playerPoolEntry']['player']['fullName'])
                player_fantasy_team.append(league_json['teams'][team]['id'])
                player_roster_slot.append(
                    league_json['teams'][team]['roster']['entries'][slot]['lineupSlotId'])

                # Initialize the variables before using them
                act = 0
                proj = 0

                # Loop through each statistic set for each roster slot for each team
                # to get projected and actual scores
                for stat in league_json['teams'][team]['roster']['entries'][slot]['playerPoolEntry']['player']['stats']:
                    if stat['scoringPeriodId'] != week:
                        continue
                    if stat['statSourceId'] == 0:
                        act = stat['appliedTotal']
                    elif stat['statSourceId'] == 1:
                        proj = stat['appliedTotal']
                    else:
                        print('Error')

                player_score_act.append(act)
                player_score_proj.append(proj)

        # Put the lists into a dictionary
        player_dict = {
            'Week': weeks,
            'PlayerName': player_name,
            'PlayerScoreActual': player_score_act,
            'PlayerScoreProjected': player_score_proj,
            'PlayerRosterSlotId': player_roster_slot,
            'PlayerFantasyTeam': player_fantasy_team
        }

        # Transform the dictionary into a DataFrame
        df = pd.DataFrame.from_dict(player_dict)

        # Initialize empty column for PlayerRosterSlot
        df['PlayerRosterSlot'] = ""

        # Ignore chained assignment warnings
        pd.options.mode.chained_assignment = None

        # Replace the PlayerRosterSlot integers with position indicators
        df['PlayerRosterSlot'] = df['PlayerRosterSlotId'].apply(
            lambda x: self.POSITION_MAPPING.get(x, 'NA'))

        df.drop(columns=['PlayerRosterSlotId'], inplace=True)
        self.df = df

    def load_team_names(self, week):
        '''
        Load the team names from the league JSON
        '''
        # Define the URL with our parameters
        url = self.base_url.format(year=self.year, league_id=self.league_id)

        team_json = self.make_request(url,
                                      params={"leagueId": self.league_id,
                                              "seasonId": self.year,
                                              "matchupPeriodId": week},
                                      view="mTeam")

        # Initialize empty list for team names and team ids
        team_id = []
        team_shield = []
        team_primary_owner = []
        team_location = []
        team_nickname = []
        owner_first_name = []
        owner_last_name = []
        team_cookie = []

        # Loop through each team in the JSON
        for team in range(0, len(team_json['teams'])):
            # Append the team id and team name to the list
            team_id.append(team_json['teams'][team]['id'])
            team_shield.append(team_json['teams'][team]['logo'])
            team_primary_owner.append(team_json['teams'][team]['primaryOwner'])
            team_location.append(team_json['teams'][team]['location'])
            team_nickname.append(team_json['teams'][team]['nickname'])
            owner_first_name.append(team_json['members'][team]['firstName'])
            owner_last_name.append(team_json['members'][team]['lastName'])
            team_cookie.append(team_json['members'][team]['id'])

        # Create team DataFrame
        team_df = pd.DataFrame({
            'PlayerFantasyTeam': team_id,
            'logo': team_shield,
            'TeamPrimaryOwner': team_primary_owner,
            'Location': team_location,
            'Nickname': team_nickname,
        })

        # Create owner DataFrame
        owner_df = pd.DataFrame({
            'OwnerFirstName': owner_first_name,
            'OwnerLastName': owner_last_name,
            'TeamPrimaryOwner': team_cookie
        })

        # Merge the team and owner DataFrames on the TeamPrimaryOwner column
        team_df = pd.merge(team_df, owner_df, on='TeamPrimaryOwner', how='left')

        # Filter team_df to only include PlayerFantasyTeam, logo, Location, Nickname, OwnerFirstName, and OwnerLastName
        team_df = team_df[['PlayerFantasyTeam','logo' , 'Location',
                        'Nickname', 'OwnerFirstName', 'OwnerLastName']]

        # Concatenate the two name columns
        team_df['TeamName'] = team_df['Location'] + ' ' + team_df['Nickname']

        # Create a column for full name
        team_df['FullName'] = team_df['OwnerFirstName'] + \
            ' ' + team_df['OwnerLastName']

        # Drop all columns except id and Name and Logo
        team_df = team_df.filter(['PlayerFantasyTeam','logo' , 'TeamName', 'FullName'])

        self.df = self.df.merge(team_df, on=['PlayerFantasyTeam'], how='left')
        self.df = self.df.rename(columns={'Name': 'PlayerFantasyTeamName'})
        self.df = self.df.rename(columns={'logo': 'FantasyTeamLogo'})

    def get_league_data(self, week=None):
        '''
        Create the league DataFrame
        '''
        if week is None:  # If no specific week is provided, load data for all weeks.
            weeks = list(range(1, 18))  # Assuming 17 weeks in a season.
        else:
            weeks = list(range(1, week-1))

        # Instead of appending to self.df directly, we're going to store each week's DataFrame in a list.
        dataframes = []

        for week in weeks:
            league_json = self.load_league(week)
            self.load_player_data(league_json, week)
            self.load_team_names(week)

            # After loading the data for the week, add a copy of the DataFrame to the list.
            dataframes.append(self.df.copy())

        # Concatenate all weekly dataframes into one.
        self.df = pd.concat(dataframes)

        return self.df
    
    def season_standings_history_to_csv(self):
        # Pull team and matchup data from the URL
        team_response = requests.get(self.base_url,
                                        params={"leagueId": self.league_id,
                                                "seasonId": self.year,
                                                "matchupPeriodId": 1,
                                                "view": "mTeam"},
                                        cookies=self.cookies)

        # Transform the response into a json
        team_json = team_response.json()
        team_df = pd.json_normalize(team_json['teams'])

        team_df.to_csv(os.getenv('csv_path')+'teams_df.csv')

        team_column_names = {
                'id': 'id',
                'logo': 'Logo',
                'name': 'Name',
                'divisionId': 'Division',
                'record.overall.losses': 'Losses',
                'record.overall.ties': 'Ties',
                'record.overall.wins': 'Wins',
                'record.overall.percentage': '%',
                'record.overall.pointsAgainst': 'PA',
                'record.overall.pointsFor': 'PF',
            }

        # Reindex based on column names defined above
        team_df = team_df.reindex(columns=team_column_names).rename(
            columns=team_column_names)
        
        # Adiciona a coluna com a temporada (mais fácil para encontrar uma matchup específica depois)
        team_df['Season'] = self.year
        
        team_df = team_df[['Season', 'id', 'Division', 'Logo', 'Name', 'Wins', 'Losses', 'Ties', '%', 'PF', 'PA']]
        team_df = team_df.sort_values(by=['Division', '%', 'PF'], ascending=[True, False, False])
        team_df.reset_index(drop=True, inplace=True)

        return team_df
    
    def get_overall_standings(self):
        team_df = self.get_division_standings()
        team_df = team_df.sort_values(by=['%', 'PF'], ascending=[False, False])
        # Look for division leaders
        leaders = []
        for group in range(0,4):
            leader = team_df[team_df.Division == group].iloc[0]
            leader_index = team_df[team_df.Division == group].index[0]
            
            leaders.append(leader)
            team_df.drop(leader_index, inplace=True)

        leaders_df = pd.DataFrame(leaders)
        leaders_df = leaders_df.sort_values(by=['%', 'PF'], ascending=[False, False])
        team_df = pd.concat([leaders_df, team_df], ignore_index=True)

        return team_df
        
    def get_one_schedule_data(self, week):
        matchup_response = requests.get(self.base_url,
                                            params={"leagueId": self.league_id,
                                                    "seasonId": self.year,
                                                    "matchupPeriodId": week,
                                                    "view": "mMatchup"},
                                            cookies=self.cookies)
        
        # Transform the response into a json
        matchup_json = matchup_response.json()

        matchup_df = pd.json_normalize(matchup_json['schedule'])

        # Define the column names needed
        matchup_column_names = {
            'matchupPeriodId': 'Week',
            'away.teamId': 'Team1',
            'away.totalPoints': 'Score1',
            'home.teamId': 'Team2',
            'home.totalPoints': 'Score2',
        }

        matchup_df = matchup_df.reindex(columns=matchup_column_names).rename(
                columns=matchup_column_names)
        
        matchup_df = matchup_df[['Week', 'Team1',
                                     'Score1', 'Team2', 'Score2']]
        
        matchup_df.drop(matchup_df[matchup_df['Week'] != week].index, inplace=True)

        return matchup_df

    def get_schedule_data(self, week=None):
        if week is None:
            weeks = list(range(1, 18))  # Weeks 1 through 17
        else:
            weeks = [week]

        all_matchup_data = []

        for week in weeks:
            # Pull team and matchup data from the URL
            matchup_response = requests.get(self.base_url,
                                            params={"leagueId": self.league_id,
                                                    "seasonId": self.year,
                                                    "matchupPeriodId": week,
                                                    "view": "mMatchup"},
                                            cookies=self.cookies)

            team_response = requests.get(self.base_url,
                                         params={"leagueId": self.league_id,
                                                 "seasonId": self.year,
                                                 "matchupPeriodId": week,
                                                 "view": "mTeam"},
                                         cookies=self.cookies)

            # Transform the response into a json
            matchup_json = matchup_response.json()
            team_json = team_response.json()

            # Transform both of the json outputs into DataFrames
            matchup_df = pd.json_normalize(matchup_json['schedule'])
            team_df = pd.json_normalize(team_json['teams'])

            # Define the column names needed
            matchup_column_names = {
                'matchupPeriodId': 'Week',
                'away.teamId': 'Team1',
                'away.totalPoints': 'Score1',
                'home.teamId': 'Team2',
                'home.totalPoints': 'Score2',
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

           # Reindex based on column names defined above
            matchup_df = matchup_df.reindex(columns=matchup_column_names).rename(
                columns=matchup_column_names)
            team_df = team_df.reindex(columns=team_column_names).rename(
                columns=team_column_names)

            # Add a new column for regular/playoff game based on week number
            matchup_df['Type'] = ['Regular' if week <=
                                  14 else 'Playoff' for week in matchup_df['Week']]

            # Concatenate the two name columns
            #team_df['Name'] = team_df['Name1'] + ' ' + team_df['Name2']

            team_df['Wins'] = team_df['Wins'].apply(str)
            team_df['Losses'] = team_df['Losses'].apply(str)
            team_df['Ties'] = team_df['Ties'].apply(str)
            team_df['Record'] = team_df['Wins'] + '-' + team_df['Losses'] + '-' + team_df['Ties']

            # Drop all columns except id and Name and Logo and Abbrev and Record
            team_df = team_df.filter(['id', 'Logo', 'Name', 'Abbrev', 'Record'])

            # (1) Rename Team1 column to id
            matchup_df = matchup_df.rename(columns={"Team1": "id"})
            
            # (1) Merge DataFrames to get team names instead of ids and rename Name column to Name1
            matchup_df = matchup_df.merge(team_df, on=['id'], how='left')
            matchup_df = matchup_df.rename(columns={'Abbrev': 'Abbrev1'})
            matchup_df = matchup_df.rename(columns={'Record': 'Record1'})
            matchup_df = matchup_df.rename(columns={'Name': 'Name1'})
            matchup_df = matchup_df.rename(columns={'Logo': 'Logo1'})

            # (1) Drop the id column and reorder columns
            matchup_df = matchup_df[['Week', 'Logo1', 'Name1', 'Abbrev1', 'Record1',
                                     'Score1', 'Team2', 'Score2', 'Type']]

            # (2) Rename Team2 column to id
            matchup_df = matchup_df.rename(columns={"Team2": "id"})

            # (2) Merge DataFrames to get team names instead of ids and rename Name column to Name2
            matchup_df = matchup_df.merge(team_df, on=['id'], how='left')
            matchup_df = matchup_df.rename(columns={'Abbrev': 'Abbrev2'})
            matchup_df = matchup_df.rename(columns={'Record': 'Record2'})
            matchup_df = matchup_df.rename(columns={'Name': 'Name2'})
            matchup_df = matchup_df.rename(columns={'Logo': 'Logo2'})

            # (2) Drop the id column and reorder columns
            matchup_df = matchup_df[['Week', 'Logo1', 'Name1', 'Abbrev1', 'Record1',
                                     'Score1', 'Logo2', 'Name2', 'Abbrev2', 'Record2', 'Score2', 'Type']]
            
            # Add info if matchup was already played
            matchup_df.drop(matchup_df[matchup_df['Week'] != week].index, inplace=True)
            all_matchup_data.append(matchup_df)

        self.matchup_df = pd.concat(all_matchup_data, ignore_index=True)

        return self.matchup_df
        
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
    
    # Adiciona uma matchup_df no fim do .csv (atenção à formatação!)
    def add_matchup_to_csv(self, week_matchup_df):
        # Fazer backup dos dados e deletar a primeira coluna (duplicação dos IDs)
        cur_matchup_df = pd.read_csv(os.getenv('csv_path')+os.getenv('matchup_history'))
        cur_matchup_df.drop(cur_matchup_df.columns[0], axis=1, inplace=True)

        # Concatenar resultado com o backup do arquivo e redefinir os IDs
        cur_matchup_df = pd.concat([cur_matchup_df, week_matchup_df])
        cur_matchup_df.reset_index(drop=True, inplace=True)
        
        # Salvar dados no arquivo
        cur_matchup_df.to_csv(os.getenv('csv_path')+os.getenv('matchup_history'))

    # Adiciona ao CSV todas as partidas já finalizadas da season conectada {{self.year}}
    def season_matchup_history_to_csv(self):
        # Fazer backup dos dados e deletar a primeira coluna (duplicação dos IDs)
        cur_matchup_df = pd.read_csv(os.getenv('csv_path')+os.getenv('matchup_history'))
        cur_matchup_df.drop(cur_matchup_df.columns[0], axis=1, inplace=True)

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
        matchup_df.drop(matchup_df[matchup_df['winner'] == "UNDECIDED"].index, inplace=True)

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
        
        # Concatenar resultado com o backup do arquivo e redefinir os IDs
        cur_matchup_df = pd.concat([cur_matchup_df, matchup_df])
        cur_matchup_df.reset_index(drop=True, inplace=True)
        
        # Salvar dados no arquivo
        cur_matchup_df.to_csv(os.getenv('csv_path')+os.getenv('matchup_history'))

    def season_standings_history_to_csv(self):
        # Fazer backup dos dados e deletar a primeira coluna (duplicação dos IDs)
        cur_standings_df = pd.read_csv(os.getenv('csv_path')+os.getenv('standings_history'))
        cur_standings_df.drop(cur_standings_df.columns[0], axis=1, inplace=True)

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

        # Concatenar resultado com o backup do arquivo e redefinir os IDs
        cur_standings_df = pd.concat([cur_standings_df, team_df])
        cur_standings_df.reset_index(drop=True, inplace=True)
        
        # Salvar dados no arquivo
        cur_standings_df.to_csv(os.getenv('csv_path')+os.getenv('standings_history'))

