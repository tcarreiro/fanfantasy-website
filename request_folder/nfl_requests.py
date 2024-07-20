import pandas as pd  # type: ignore
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import os

#####################################################################################################
### ESSA CLASSE GERENCIA O WEBSCRAPPING DO ESPN.COM, NÃO O API. PARA O API, VER ESPNFANFANTASY.PY ###
#####################################################################################################

# Código para desenvolvimento. Configurações de display do Pandas
pd.options.mode.chained_assignment = None  # default='warn'
pd.set_option('display.max_rows', 800)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# Listas e dicionários auxiliares
teams_list = [
    'Atlanta Falcons',
    'Arizona Cardinals',
    'Baltimore Ravens',
    'Buffalo Bills',
    'Carolina Panthers',
    'Chicago Bears',
    'Cincinnati Bengals',
    'Cleveland Browns',
    'Dallas Cowboys',
    'Denver Broncos',
    'Detroit Lions',
    'Green Bay Packers',
    'Houston Texans',
    'Indianapolis Colts',
    'Jacksonville Jaguars',
    'Kansas City Chiefs',
    'Las Vegas Raiders',
    'Los Angeles Chargers',
    'Los Angeles Rams',
    'Miami Dolphins',
    'Minnesota Vikings',
    'New England Patriots',
    'New Orleans Saints',
    'New York Giants',
    'New York Jets',
    'Philadelphia Eagles',
    'Pittsburgh Steelers',
    'San Francisco 49ers',
    'Seattle Seahawks',
    'Tampa Bay Buccaneers',
    'Tennessee Titans',
    'Washington Commanders'
    ]

team_short = {
    'Atlanta Falcons': 'atl',
    'Arizona Cardinals': 'ari',
    'Baltimore Ravens': 'bal',
    'Buffalo Bills': 'buf',
    'Carolina Panthers': 'car',
    'Chicago Bears': 'chi',
    'Cincinnati Bengals': 'cin',
    'Cleveland Browns': 'cle',
    'Dallas Cowboys': 'dal',
    'Denver Broncos': 'den',
    'Detroit Lions': 'det',
    'Green Bay Packers': 'gb',
    'Houston Texans': 'hou',
    'Indianapolis Colts': 'ind',
    'Jacksonville Jaguars': 'jax',
    'Kansas City Chiefs': 'kc',
    'Las Vegas Raiders': 'lv',
    'Los Angeles Chargers': 'lac',
    'Los Angeles Rams': 'lar',
    'Miami Dolphins': 'mia',
    'Minnesota Vikings': 'min',
    'New England Patriots': 'ne',
    'New Orleans Saints': 'no',
    'New York Giants': 'nyg',
    'New York Jets': 'nyj',
    'Philadelphia Eagles': 'phi',
    'Pittsburgh Steelers': 'pit',
    'San Francisco 49ers': 'sf',
    'Seattle Seahawks': 'sea',
    'Tampa Bay Buccaneers': 'tb',
    'Tennessee Titans': 'ten',
    'Washington Commanders': 'wsh'
    }

def get_teams_list():
    return teams_list

# helper function that makes a HTTP request over a list of players of a given team
def make_team_list_request(team: str):
    team_endpoint = team.lower().replace(" ","-")
    team_short_endpoint = team_short[team]
    url = 'https://www.espn.com.br/nfl/time/elenco/_/nome/%s/%s/' % (team_short_endpoint, team_endpoint)
    r = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    c = urlopen(r).read()
    soup = BeautifulSoup(c, "html.parser")
    return soup

# helper function that takes a BeautifulSoup object and converts it into a pandas dataframe containing player data
def team_player_list(soup: BeautifulSoup, team:str) -> pd.DataFrame:
    valid_positions = ['QB', 'FB', 'RB', 'WR', 'TE', 'DST']
    data = {
        'profile_pic': [],
        'team': [],
        'position': [],
        'first_name': [],
        'last_name': [],
        'rookie': [],
        'bye': []
    }  # type: dict
    

    # All src imgs of offense
    players_pictures_list = soup.find('tbody').find_all('img')
    for i in range(0, len(players_pictures_list)):
        data['team'].append(team.lower().replace(" ","_"))
        data['profile_pic'].append(players_pictures_list[i].get('alt'))
        data['first_name'].append(players_pictures_list[i].get('title').split(" ",1)[0])
        data['last_name'].append(players_pictures_list[i].get('title').split(" ",1)[1])

    # All positions of offense (3 results for each player, position is the second result)
    players_position_list = soup.find('tbody').find_all('div', style='min-width:40px')
    for i in range(1, len(players_position_list), 3):
        if (players_position_list[i] is not None):
            data['position'].append(players_position_list[i].text)

    data['rookie'] = False
    data['bye'] = 1

    # Drop players that are not of allowed positions
    players_pd=pd.DataFrame(data=data)
    new_pd = pd.DataFrame()
    for pos in valid_positions:
        new_pd = pd.concat([new_pd, players_pd[players_pd['position']==pos]], ignore_index=True)

    new_pd['position'][new_pd['position']=='FB'] = 'RB'
    return new_pd

# That is the method called to generate DataFrame. Use players_pd.to_csv('file.csv') to create csv file
def get_all_players_pd() -> pd.DataFrame:
    players_list = pd.DataFrame()
    for team in teams_list:
        players_list = pd.concat([players_list, team_player_list(make_team_list_request(team), team)], ignore_index=True)

    return players_list

# Retorna tabela com as defesas REVISADO OK
def get_defenses(draft_board_list) -> pd.DataFrame:
    defense_list = draft_board_list.copy()
    
    defense_list.drop(defense_list[defense_list['position'] != 'DS'].index, inplace = True)
    defense_list.reset_index(drop=True, inplace=True)

    for i in range(0,len(defense_list)):
        team_name = defense_list['first_name'][i] + " " + defense_list['last_name'][i]
        defense_list['team'][i] = team_name.replace(" ","_").lower()
        defense_list['profile_pic'][i] = ' '
        defense_list['first_name'][i] = team_name.rsplit(" ",1)[0]
        defense_list['last_name'][i] = team_name.rsplit(" ",1)[1]
        defense_list['position'][i] = 'DST'

    return defense_list

# Lê e configura a tabela de rookies importada do Fantasy Pros
def get_rookies_list() -> pd.DataFrame:
    # Rookies
    rookies_list = pd.read_csv(os.getenv("csv_path")+os.getenv('ROOKIE_LIST'))
    rookies_list['last_name'] = rookies_list['PLAYER NAME']
    rookies_list['profile_pic'] = ""
    rookies_list['rookie'] = True
    rookies_list['bye'] = 1
    rookies_list = rookies_list[['profile_pic', 'TEAM', 'POS', 'PLAYER NAME', 'last_name', 'rookie', 'bye']]
    for i in range(0,len(rookies_list)):
        rookies_list['PLAYER NAME'][i] = rookies_list['PLAYER NAME'][i].split(" ",1)[0]
        rookies_list['last_name'][i] = rookies_list['last_name'][i].split(" ",1)[1]
    rookies_list['TEAM'] = rookies_list['TEAM'].str.lower()
    rookies_list['POS'] = (rookies_list['POS'].str[0]+rookies_list['POS'].str[1])
    column_names = {
        'profile_pic': 'profile_pic',
        'TEAM': 'team',
        'POS': 'position',
        'PLAYER NAME': 'first_name',
        'last_name': 'last_name',
        'rookie': 'rookie',
        'bye': 'bye'
    }
    rookies_list = rookies_list.reindex(columns=column_names).rename(
            columns=column_names)
    
    return rookies_list

# Board do fantasy pros REVISADO OK
def get_fp_draft_board_list() -> pd.DataFrame:
    draft_board_list = pd.read_csv(os.getenv("csv_path")+os.getenv('FP_BOARD_LIST'))
    draft_board_list['last_name'] = draft_board_list['PLAYER NAME']
    draft_board_list['profile_pic'] = ""
    draft_board_list['rookie'] = False
    draft_board_list = draft_board_list[['profile_pic', 'TEAM', 'POS', 'PLAYER NAME', 'last_name', 'rookie', 'BYE WEEK']]
    for i in range(0,len(draft_board_list)):
        draft_board_list['PLAYER NAME'][i] = draft_board_list['PLAYER NAME'][i].split(" ",1)[0]
        draft_board_list['last_name'][i] = draft_board_list['last_name'][i].split(" ",1)[1]
    draft_board_list['TEAM'] = draft_board_list['TEAM'].str.lower()
    draft_board_list['POS'] = (draft_board_list['POS'].str[0]+draft_board_list['POS'].str[1])

    column_names = {
        'profile_pic': 'profile_pic',
        'TEAM': 'team',
        'POS': 'position',
        'PLAYER NAME': 'first_name',
        'last_name': 'last_name',
        'rookie': 'rookie',
        'BYE WEEK': 'bye'
    }
    draft_board_list = draft_board_list.reindex(columns=column_names).rename(
            columns=column_names)

    draft_board_list = draft_board_list[ (draft_board_list['first_name'] + " " + draft_board_list['last_name'] != 'Taysom Hill')] # Dropar Taysom Hill, que está como TE

    # Retirando os kickers
    for i in range(0,10):
        draft_board_list.drop(draft_board_list[draft_board_list['position'] == 'K'+str(i)].index, inplace = True)

    # Reseta os indexes
    draft_board_list.reset_index(drop=True, inplace=True)
    return draft_board_list

# Lista de Free Agents. Opção: deixar o parâmetro opcional e, caso não seja informado, ler o arquivo do board get_fp_draft_board_list() REVISADO OK
def get_fa_list_from_board_list(draft_board_list) -> pd.DataFrame:
    fa_list = draft_board_list.copy()
    fa_list.drop(fa_list[fa_list['team'] != 'fa'].index, inplace = True)
    fa_list.reset_index(drop=True, inplace=True)

    return fa_list

def get_draft_list() -> pd.DataFrame:
    draft_list = pd.read_csv(os.getenv("csv_path")+os.getenv('DRAFT_LIST'))
    draft_list.drop(draft_list.columns[0], axis=1, inplace=True)
    return draft_list

# Cria a lista do draft pronta para ser usada (jogadores podem ser adicionados manualmente depois desse passo) REVISADO OK
def create_draft_list(draft_board_reach):
    players_list = pd.read_csv(os.getenv("csv_path")+os.getenv('PLAYERS_LIST'))
    players_list.drop(players_list.columns[0], axis=1, inplace=True)
    draft_board_list = get_fp_draft_board_list()
    defense_list = get_defenses(draft_board_list)
    rookies_list = get_rookies_list()
    fa_list = get_fa_list_from_board_list(draft_board_list)

    # Dropar todas as defesas do FP board e resetar indices
    draft_board_list.drop(draft_board_list[draft_board_list['position'] == 'DS'].index, inplace = True)
    draft_board_list.reset_index(drop=True, inplace=True)

    # Filtrar board para o número de jogadores escolhidos
    draft_board_list = draft_board_list.iloc[:draft_board_reach]
        
    listed_players = {
        'profile_pic': [],
        'team': [],
        'position': [],
        'first_name': [],
        'last_name': [],
        'rookie': [],
        'bye': []
    }  # type: dict

    all_players_names = pd.DataFrame()
    all_players_names = pd.concat([all_players_names, fa_list],ignore_index=True)
    all_players_names = pd.concat([all_players_names, players_list],ignore_index=True)

    # Varredura pelos rosters (webscrapper players_list) + FA para fazer comparação dos que estão presentes no FP board depois de filtrado para a quantidade de jogadores escolhidos
    for i in range(0, len(all_players_names)):
        # A comparação é feita exclusivamente com o primeiro nome e o primeiro sobrenome (ignorando caso tenham outros sobrenomes)
        if is_player_on_a_team_two_names(all_players_names['first_name'][i]+" "+all_players_names['last_name'][i].split(" ",1)[0], draft_board_list):
            listed_players['profile_pic'].append(all_players_names['profile_pic'][i])
            listed_players['team'].append(all_players_names['team'][i])
            listed_players['position'].append(all_players_names['position'][i])
            listed_players['first_name'].append(all_players_names['first_name'][i])
            listed_players['last_name'].append(all_players_names['last_name'][i])
            
            # Varredura se o nome também está na lista de calouros para atualizar a flag
            is_rookie = False
            for k in range(0, len(rookies_list)):
                if (all_players_names['first_name'][i] + " " + all_players_names['last_name'][i].split(" ",1)[0] ==
                    rookies_list['first_name'][k] + " " + rookies_list['last_name'][k].split(" ",1)[0]):
                    is_rookie = True
                    break
            listed_players['rookie'].append(is_rookie)
            
            # Procurar semana de bye do jogador de acordo com seu time
            bye_week = get_bye_by_team(all_players_names['team'][i], defense_list)
            # Verifica se é FA
            if (bye_week == "-"): 
                listed_players['bye'].append(all_players_names['bye'][i])
            else:
                listed_players['bye'].append(bye_week)

    draft_list=pd.DataFrame(data=listed_players)
    # Adiciona 5 etiquetas em branco para cada posição (menos defesa)
    draft_list = pd.concat([draft_list, add_empty_space(5)],ignore_index=True)
    # Concatena as etiquetas vazias com todos os jogadores listados pelo procedimento anterior
    draft_list = pd.concat([draft_list, defense_list],ignore_index=True)
    draft_list.to_csv(os.getenv("csv_path")+os.getenv('DRAFT_LIST'))

def add_empty_space(count):
    valid_positions = ['QB', 'RB', 'WR', 'TE']
    added_players = {
        'profile_pic': [],
        'team': [],
        'position': [],
        'first_name': [],
        'last_name': [],
        'rookie': [],
        'bye': []
    }  # type: dict

    for position in valid_positions:
        for i in range(0, count):
            added_players['profile_pic'].append("")
            added_players['team'].append("")
            added_players['position'].append(position)
            added_players['first_name'].append(" ")
            added_players['last_name'].append("blank_label")
            added_players['rookie'].append(False)
            added_players['bye'].append(" ")

    added_list=pd.DataFrame(data=added_players)

    return added_list

# Retorna a semana de bye do @team procurando na lista de times REVISADO OK
def get_bye_by_team(team, defense_list):
    bye_week = "-"
    for j in range(0,len(defense_list)):
        team_name = defense_list['first_name'][j].lower() + " " + defense_list['last_name'][j].lower()
        team_name = team_name.replace(" ", "_")
        if (team == team_name):
            bye_week = defense_list['bye'][j]
            break
    return bye_week

# Adiciona jogadores manualmente à lista de draft pronta para uso REVISADO OK TODO CHECAR REPETIÇÃO 
def add_player(profile_pic:str, first_name:str, last_name:str, team:str, position, is_rookie, draft_board_list):
    draft_list = pd.read_csv(os.getenv("csv_path")+os.getenv('DRAFT_LIST'))
    draft_list.drop(draft_list.columns[0], axis=1, inplace=True)

    added_players = {
        'profile_pic': [],
        'team': [],
        'position': [],
        'first_name': [],
        'last_name': [],
        'rookie': [],
        'bye': []
    }  # type: dict

    defense_list = get_defenses(draft_board_list)

    added_players['profile_pic'].append(profile_pic)
    added_players['team'].append(team.replace(' ','_').lower())
    added_players['position'].append(position)
    added_players['first_name'].append(first_name)
    added_players['last_name'].append(last_name)
    added_players['rookie'].append(is_rookie)
    added_players['bye'].append(get_bye_by_team(team.replace(' ','_').lower(), defense_list))

    added_list=pd.DataFrame(data=added_players)
    draft_list = pd.concat([draft_list, added_list])
    draft_list.reset_index(drop=True, inplace=True)

    draft_list.to_csv(os.getenv("csv_path")+os.getenv('DRAFT_LIST'))

def update_player(id:int, profile_pic:str, first_name:str, last_name:str, team:str, position, is_rookie, draft_board_list):
    draft_list = pd.read_csv(os.getenv("csv_path")+os.getenv('DRAFT_LIST'))
    draft_list.drop(draft_list.columns[0], axis=1, inplace=True)
    defense_list = get_defenses(draft_board_list)

    draft_list['profile_pic'][id] = profile_pic
    draft_list['team'][id] = team.replace(' ','_').lower()
    draft_list['position'][id] = position
    draft_list['first_name'][id] = first_name
    draft_list['last_name'][id] = last_name
    draft_list['rookie'][id] = is_rookie
    draft_list['bye'][id] = get_bye_by_team(team.replace(' ','_').lower(), defense_list)

    draft_list.to_csv(os.getenv("csv_path")+os.getenv('DRAFT_LIST'))

def delete_player(id:int):
    draft_list = pd.read_csv(os.getenv("csv_path")+os.getenv('DRAFT_LIST'))
    draft_list.drop(draft_list.columns[0], axis=1, inplace=True)
    draft_list.drop([draft_list.index[id]], inplace=True)
    draft_list.to_csv(os.getenv("csv_path")+os.getenv('DRAFT_LIST'))

# TODO não checa para possíveis jogadores com mesmo nome
def is_player_on_a_team_two_names(player: str, players_team_list) -> bool:
    resp = False
    for i in range(0,len(players_team_list)):
        if (players_team_list['first_name'][i] + " " + players_team_list['last_name'][i].split(' ',1)[0]) == player:
            resp = True
    return(resp)

