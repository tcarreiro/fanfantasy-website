from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import request_folder.nfl_requests as espnrequest
import os
import website.league as league
import fetchESPN as fetch

pd.options.mode.chained_assignment = None  # default='warn'

views = Blueprint('views', __name__)


##############################
##### HELPERS
##############################


##############################
##### LEAGUE
##############################

@views.route('/', methods=['POST', 'GET'])
def home():
    tab = '/'
    nth = 0
    [current_week, weekday, current_year, time] = league.format_date()

    return render_template('home.html', tab=tab, nth=nth, current_week=current_week, current_year=current_year, weekday=weekday, hour=time.hour)

@views.route('/update_match_strip', methods=['POST'])
def requestMatchupESPN():
    # Recuperando dados TODO precisa fazer verificação? Há risco de perda de dados nos 'hiddens'?
    current_week = int(request.form.get('current_week'))
    weekday = int(request.form.get('weekday'))
    current_year = int(request.form.get('current_year'))
    hour = int(request.form.get('hour'))
    fetch.league = fetch.connect_league(os.getenv('league_id'), current_year)
    matchup_data = fetch.league.get_matchup_data_from_API(week=current_week)
    return jsonify({'data': render_template('match_strip.html', current_week=current_week, weekday=weekday, current_year=current_year, hour=hour, matchup_data=matchup_data)})
    
@views.route('/classificacao', methods=['POST'])
def classificacao():
    tab = '/classificacao'
    nth = 1
    [current_week, weekday, current_year, time] = league.format_date()
    teams_data = league.get_standings_from_csv(current_year)

    # Config para os tipos de classificação (divisões ou geral)
    if request.form.get('table_format'):
        table_format = request.form.get('table_format')
    else:
        table_format = 'group'

    # Config para a temporada consultada
    if request.form.get('year'):
        year = int(request.form.get('year'))
    else:
        year = current_year

    # Aquisição de dados caso seja solicitado um novo ano
    if (year != current_year):
        teams_data = league.get_standings_from_csv(year)
        [week, day, league_year, time] = league.format_date(year=year)
    else:
        league_year=current_year

    # Ordenar standings de acordo com a aba selecionada
    if table_format == 'group':
        teams_data = teams_data.sort_values(by=['Division', 'Seed'], ascending=[True, True])
        teams_data.reset_index(drop=True, inplace=True)
    if table_format == 'overall':
        teams_data = teams_data.sort_values(by=['Seed'], ascending=[True])
        teams_data.reset_index(drop=True, inplace=True)

    # Configuração arredondamentos
    teams_data['%'] = teams_data['%'].round(3)
    teams_data['PF'] = teams_data['PF'].round(1)
    teams_data['PA'] = teams_data['PA'].round(1)

    return jsonify({'data': render_template('classificacao.html', tab=tab, nth=nth, teams_data=teams_data,
                           table_format=table_format, current_year=current_year, current_week=current_week, weekday=weekday, league_year=league_year, hour=time.hour)})

@views.route('/rankings', methods=['GET', 'POST'])
def rankings():
    tab = '/rankings'
    nth = 2
    [current_week, weekday, current_year, time] = league.format_date()
    teams_data = league.get_standings_from_csv(current_year)

    # Config para a temporada consultada
    if request.form.get('year'):
        year = int(request.form.get('year'))
    else:
        year = current_year

    # Recuperação de dados
    cur_param = request.form.get('cur_param')
    cur_ascending = request.form.get('cur_ascending')
    param = request.form.get('param')

    if(cur_param==param):
        if (cur_ascending == 'True'):
            cur_ascending = False
        else:
            cur_ascending = True
    else:
            cur_ascending = True

    # Aquisição de dados caso seja solicitado um novo ano
    if (year != current_year):
        teams_data = league.get_standings_from_csv(year)
        [week, day, league_year, time] = league.format_date(year=year)
    else:
        league_year=current_year

    teams_data['deltaWins'] = teams_data['Wins'] - teams_data['ExpectedWins']
    
    # Configuração arredondamentos
    teams_data['%'] = teams_data['%'].round(3)
    teams_data['PF'] = teams_data['PF'].round(1)
    teams_data['PA'] = teams_data['PA'].round(1)
    teams_data['ExpectedWins'] = teams_data['ExpectedWins'].round(3)
    teams_data['MedPF'] = teams_data['MedPF'].round(1)
    teams_data['MedPA'] = teams_data['MedPA'].round(1)
    teams_data['deltaWins'] = teams_data['deltaWins'].round(3)

    # Ordenar standings de acordo com a aba selecionada
    teams_data = teams_data.sort_values(by=[param, 'Seed'], ascending=[bool(cur_ascending), ~bool(cur_ascending)])
    teams_data.reset_index(drop=True, inplace=True)

    return jsonify({'data': render_template('rankings.html', tab=tab, nth=nth, ascending=cur_ascending, param=param, teams_data=teams_data,
                           current_year=current_year, current_week=current_week, weekday=weekday, league_year=league_year, hour=time.hour)})

@views.route('/fanfastats', methods=['GET', 'POST'])
def fanfastats():
    tab = '/fanfastats'
    nth = 3
    [current_week, weekday, current_year, time] = league.format_date()

    matchup_data = league.get_matchup_from_csv(current_year)
    teams_data = league.get_standings_from_csv(current_year)
    
    return jsonify({'data': render_template('fanfastats.html', tab=tab, nth=nth, matchup_data=matchup_data, teams_data=teams_data,
                           current_year=current_year, current_week=current_week, weekday=weekday, hour=time.hour)})

##############################
##### DRAFTS
##############################

@views.route('/draft', methods=['GET', 'POST'])
def draft():
    backup_df = pd.read_csv(os.getenv('DRAFT_LIST'))
    player_df = pd.DataFrame()
    display_positions = []
    amount = 0

    if request.method == 'POST':
        valid_positions = ['QB', 'RB', 'WR', 'TE', 'DST']
        for position in valid_positions:
            if (request.form.get(position)):
                display_positions.append(position)

        if len(display_positions) != 0:
            for pos in display_positions:
                player_df = pd.concat([player_df, backup_df[backup_df['position']==pos]], ignore_index=True)
                amount=len(player_df)
        else:
            player_df = pd.concat([player_df, backup_df], ignore_index=True)

    else:
        player_df = pd.concat([player_df, backup_df], ignore_index=True)
           
    player_df.sort_values(['position', 'last_name'], ascending=[False, True], ignore_index=True, inplace=True)

    return render_template('draft.html', player_df=player_df, amount=amount, display_positions=display_positions)

@views.route('/draft_config', methods=['GET', 'POST'])
def draft_config():
    teams_list = espnrequest.get_teams_list()
    draft_board_list = espnrequest.get_fp_draft_board_list()
    draft_list = espnrequest.get_draft_list()
    msg = ['', 'Banco de dados atualizado!', 'Lista de draft configurada para uso!', 'Jogador atualizado!', 'Jogador deletado!', 'Jogador adicionado!']
    msg_id = 0
    if request.method == 'POST':
        if (request.form.get('form_selector') == 'import-data-from-espn'):
            new_players_list = espnrequest.get_all_players_pd()
            new_players_list.to_csv(os.getenv('PLAYERS_LIST'))
            msg_id = 1
        elif (request.form.get('form_selector') == 'create-draft-list'):
            espnrequest.create_draft_list(int(request.form.get('fp-board-range')))
            draft_list = espnrequest.get_draft_list() # atualizar dados da lista. TODO É necessário????
            msg_id = 2
        elif (request.form.get('form_selector') == 'players_list_edit'):
            action = request.form.get('action').split(' ',1)[0]
            id = request.form.get('action').split(' ',1)[1]
            profile_pic = request.form.get('profile-picture-url '+id)
            if len(request.form.get('players-name '+id).split(' ')) > 1:
                first_name = request.form.get('players-name '+id).split(' ')[0]
                last_name = request.form.get('players-name '+id).split(' ')[1]
            else:
                first_name = " "
                last_name = request.form.get('players-name '+id).split(' ')[0]
            team = request.form.get('players-team '+id).replace(' ', '_').lower()
            position = request.form.get('players-position '+id)
            if request.form.get('is-rookie '+id) == None: is_rookie = False
            else: is_rookie = True
            if (action == 'update'):
                espnrequest.update_player(int(id), profile_pic, first_name, last_name, team, position, is_rookie, draft_board_list)
                msg_id = 3
            elif (action == 'delete'):
                espnrequest.delete_player(int(id))
                msg_id = 4
            elif (action == 'add'):
                espnrequest.add_player(profile_pic, first_name, last_name, team, position, is_rookie, draft_board_list)
                msg_id = 5
            else:
                pass

            # Atualizar lista
            draft_list = espnrequest.get_draft_list()
    else:
        msg_id = 0
    return render_template('draft_config.html', msg=msg, msg_id=msg_id, teams_list=teams_list, draft_list=draft_list)