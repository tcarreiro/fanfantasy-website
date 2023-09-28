from flask import Blueprint, render_template, request
import pandas as pd
import request_folder.nfl_requests as espnrequest
import os
import website.league as league

pd.options.mode.chained_assignment = None  # default='warn'

views = Blueprint('views', __name__)


##############################
##### ROUTES
##############################

##############################
##### LEAGUE
##############################

@views.route('/')
def home():
    [matchup_data, teams_data, current_year, current_week, weekday, time] = league.home()
    return render_template("home.html", matchup_data=matchup_data, teams_data=teams_data, current_year=current_year, current_week=current_week, weekday=weekday, time=time)
    

@views.route('/classificacao', methods=['GET', 'POST'])
def classificacao():
    [matchup_data, teams_data, tab, current_year, current_week, weekday, league_year, time] = league.classificacao()
    return render_template("classificacao.html", matchup_data=matchup_data, teams_data=teams_data,
                           tab=tab, current_year=current_year, current_week=current_week, weekday=weekday, league_year=league_year, time=time)

@views.route('/fanfastats', methods=['GET', 'POST'])
def fanfastats():
    [matchup_data, teams_data, current_year, current_week, weekday, time] = league.fanfastats()
    return render_template("fanfastats.html", matchup_data=matchup_data, teams_data=teams_data,
                           current_year=current_year, current_week=current_week, weekday=weekday, time=time)

@views.route('/rankings', methods=['GET', 'POST'])
def rankings():
    [matchup_data, teams_data, tab, current_year, current_week, weekday, league_year,league_week, time] = league.rankings() 
    return render_template("rankings.html", matchup_data=matchup_data, teams_data=teams_data, tab=tab,
                           current_year=current_year, current_week=current_week, weekday=weekday, league_year=league_year, league_week=league_week, time=time)

##############################
##### DRAFTS
##############################

@views.route('/draft', methods=['GET', 'POST'])
def draft():
    backup_df = pd.read_csv(os.getenv("DRAFT_LIST"))
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

    return render_template("draft.html", player_df=player_df, amount=amount, display_positions=display_positions)

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
            new_players_list.to_csv(os.getenv("PLAYERS_LIST"))
            msg_id = 1
        elif (request.form.get('form_selector') == 'create-draft-list'):
            espnrequest.create_draft_list(int(request.form.get('fp-board-range')))
            draft_list = espnrequest.get_draft_list() # atualizar dados da lista. TODO É necessário????
            msg_id = 2
        elif (request.form.get('form_selector') == 'players_list_edit'):
            action = request.form.get('action').split(" ",1)[0]
            id = request.form.get('action').split(" ",1)[1]
            profile_pic = request.form.get('profile-picture-url '+id)
            if len(request.form.get('players-name '+id).split(" ")) > 1:
                first_name = request.form.get('players-name '+id).split(" ")[0]
                last_name = request.form.get('players-name '+id).split(" ")[1]
            else:
                first_name = " "
                last_name = request.form.get('players-name '+id).split(" ")[0]
            team = request.form.get('players-team '+id).replace(" ", "_").lower()
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
    return render_template("draft_config.html", msg=msg, msg_id=msg_id, teams_list=teams_list, draft_list=draft_list)