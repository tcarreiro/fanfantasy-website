import requests
import pandas as pd
import os
import json

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