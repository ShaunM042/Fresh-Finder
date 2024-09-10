<<<<<<< HEAD
from flask import Flask, jsonify, render_template, request
from nba_api.stats.static import players, teams
<<<<<<< HEAD
from nba_api.stats.endpoints import playergamelog, commonplayerinfo, playercareerstats, teamgamelog, commonteamroster, teamdetails, leaguedashteamstats
=======
from nba_api.stats.endpoints import playergamelog, commonplayerinfo, playercareerstats, teamgamelog, commonteamroster, teamdetails
>>>>>>> 6e63ab058810a2cb12c8b9df2bc92d40a7769f8e
=======
from flask import Flask, Flask, jsonify, render_template, request, redirect, url_for
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, commonplayerinfo, playercareerstats, teamgamelog, commonteamroster, teamdetails, leaguedashteamstats
>>>>>>> Final updates for Fresh Finder project
import datetime
import os

app = Flask(__name__, template_folder='templates')

TEAM_LOGOS = {
    'ATL': 'https://a.espncdn.com/i/teamlogos/nba/500/atl.png',
    'BOS': 'https://a.espncdn.com/i/teamlogos/nba/500/bos.png',
    'BKN': 'https://a.espncdn.com/i/teamlogos/nba/500/bkn.png',
    'CHA': 'https://a.espncdn.com/i/teamlogos/nba/500/cha.png',
    'CHI': 'https://a.espncdn.com/i/teamlogos/nba/500/chi.png',
    'CLE': 'https://a.espncdn.com/i/teamlogos/nba/500/cle.png',
    'DAL': 'https://a.espncdn.com/i/teamlogos/nba/500/dal.png',
    'DEN': 'https://a.espncdn.com/i/teamlogos/nba/500/den.png',
    'DET': 'https://a.espncdn.com/i/teamlogos/nba/500/det.png',
    'GSW': 'https://a.espncdn.com/i/teamlogos/nba/500/gsw.png',
    'HOU': 'https://a.espncdn.com/i/teamlogos/nba/500/hou.png',
    'IND': 'https://a.espncdn.com/i/teamlogos/nba/500/ind.png',
    'LAC': 'https://a.espncdn.com/i/teamlogos/nba/500/lac.png',
    'LAL': 'https://a.espncdn.com/i/teamlogos/nba/500/lal.png',
    'MEM': 'https://a.espncdn.com/i/teamlogos/nba/500/mem.png',
    'MIA': 'https://a.espncdn.com/i/teamlogos/nba/500/mia.png',
    'MIL': 'https://a.espncdn.com/i/teamlogos/nba/500/mil.png',
    'MIN': 'https://a.espncdn.com/i/teamlogos/nba/500/min.png',
    'NOP': 'https://a.espncdn.com/i/teamlogos/nba/500/no.png',
    'NYK': 'https://a.espncdn.com/i/teamlogos/nba/500/nyk.png',
    'OKC': 'https://a.espncdn.com/i/teamlogos/nba/500/okc.png',
    'ORL': 'https://a.espncdn.com/i/teamlogos/nba/500/orl.png',
    'PHI': 'https://a.espncdn.com/i/teamlogos/nba/500/phi.png',
    'PHX': 'https://a.espncdn.com/i/teamlogos/nba/500/phx.png',
    'POR': 'https://a.espncdn.com/i/teamlogos/nba/500/por.png',
    'SAC': 'https://a.espncdn.com/i/teamlogos/nba/500/sac.png',
    'SAS': 'https://a.espncdn.com/i/teamlogos/nba/500/sas.png',
    'TOR': 'https://a.espncdn.com/i/teamlogos/nba/500/tor.png',
    'UTA': 'https://a.espncdn.com/i/teamlogos/nba/500/utah.png',
    'WAS': 'https://a.espncdn.com/i/teamlogos/nba/500/was.png',
}

<<<<<<< HEAD
@app.route('/')
def index():
    return render_template('index.html')

<<<<<<< HEAD
@app.route('/autocomplete')
def autocomplete():
    term = request.args.get('term')
    results = players.find_players_by_full_name(term)
    player_names = [player['full_name'] for player in results]
    return jsonify(player_names)

=======
>>>>>>> 6e63ab058810a2cb12c8b9df2bc92d40a7769f8e
=======
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/autocomplete')
def autocomplete():
    term = request.args.get('term')
    player_results = players.find_players_by_full_name(term)
    team_results = teams.find_teams_by_full_name(term)
    results = [player['full_name'] for player in player_results] + [team['full_name'] for team in team_results]
    return jsonify(results)

@app.route('/get_search_type')
def get_search_type():
    term = request.args.get('term')
    if not term:
        return jsonify(error="Search term is required"), 400

    player_results = players.find_players_by_full_name(term)
    if player_results:
        return jsonify(type="player")

    team_results = teams.find_teams_by_full_name(term)
    if team_results:
        return jsonify(type="team")

    return jsonify(error="No match found"), 404

>>>>>>> Final updates for Fresh Finder project
@app.route('/player_stats')
def get_player_stats():
    player_name = request.args.get('player_name')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not player_name:
        return jsonify(error="Player name is required"), 400

    player_info = players.find_players_by_full_name(player_name)
    if not player_info:
        return jsonify(message="Player not found"), 404

    player_id = player_info[0]['id']

    try:
        if start_date and end_date:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date_obj = datetime.datetime.today()
            start_date_obj = end_date_obj - datetime.timedelta(days=7)

<<<<<<< HEAD
        game_log = playergamelog.PlayerGameLog(player_id=player_id, date_from_nullable=start_date_obj.strftime('%m/%d/%Y'), date_to_nullable=end_date_obj.strftime('%m/%d/%Y'))
=======
        game_log = playergamelog.PlayerGameLog(
            player_id=player_id,
            date_from_nullable=start_date_obj.strftime('%m/%d/%Y'),
            date_to_nullable=end_date_obj.strftime('%m/%d/%Y')
        )
>>>>>>> Final updates for Fresh Finder project
        data_frame = game_log.get_data_frames()[0]

        if data_frame.empty:
            return jsonify(message="No matches played on this date"), 404

        data_frame['TEAM_ABBREVIATION'] = data_frame['MATCHUP'].apply(lambda x: x.split(' ')[0])
        data_frame['MATCHUP'] = data_frame['MATCHUP'].apply(lambda x: x.split(' ')[-1])

        games = []
        for index, row in data_frame.iterrows():
<<<<<<< HEAD
            ts_percent = (row['PTS'] / (2 * (row['FGA'] + 0.44 * row['FTA']))) * 100 if (row['FGA'] + 0.44 * row['FTA']) != 0 else 0
            game_stats = {
                'game_id': row['Game_ID'],
=======
            turnovers = row['TO'] if 'TO' in data_frame.columns else 'N/A'

            ts_percent = (row['PTS'] / (2 * (row['FGA'] + 0.44 * row['FTA']))) * 100 if (row['FGA'] + 0.44 * row['FTA']) != 0 else 0
            game_stats = {
                'game_id': row['Game_ID'],
                'game_date': row['GAME_DATE'],
>>>>>>> Final updates for Fresh Finder project
                'name': player_name,
                'team_for': row['TEAM_ABBREVIATION'],
                'team_logo': TEAM_LOGOS.get(row['TEAM_ABBREVIATION'], ''),
                'team_against': row['MATCHUP'],
                'opposing_team_logo': TEAM_LOGOS.get(row['MATCHUP'], ''),
                'minutes': row.get('MIN', 'N/A'),
                'points': row['PTS'],
                'rebounds': row['REB'],
                'assists': row['AST'],
<<<<<<< HEAD
                'fg_percent': round(row['FG_PCT'] * 100, 2),
                'ts_percent': round(ts_percent, 2),
                'plus_minus': row.get('PLUS_MINUS', 'N/A')
            }
            games.append(game_stats)

        return jsonify(games)
=======
                'steals': row['STL'],
                'blocks': row['BLK'],
                'fg_percent': round(row['FG_PCT'] * 100, 2),
                'ts_percent': round(ts_percent, 2),
                'plus_minus': row.get('PLUS_MINUS', 'N/A'),
                'turnovers': turnovers
            }
            games.append(game_stats)

        return render_template('player_stats.html', stats=games, player_name=player_name, start_date=start_date, end_date=end_date)
>>>>>>> Final updates for Fresh Finder project

    except Exception as e:
        return jsonify(error=str(e)), 500

<<<<<<< HEAD
=======

@app.route('/')
def landing():
    return render_template('landing.html')

>>>>>>> Final updates for Fresh Finder project
@app.route('/player_profile/<player_name>')
def get_player_profile(player_name):
    player_info = players.find_players_by_full_name(player_name)
    if not player_info:
        return jsonify(message="Player not found"), 404

    player_id = player_info[0]['id']

    try:
        player_career = playercareerstats.PlayerCareerStats(player_id=player_id)
        career_data = player_career.get_data_frames()[0]
        common_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        common_data = common_info.get_data_frames()[0]

        position = common_data['POSITION'].values[0] if 'POSITION' in common_data.columns and not common_data.empty else 'N/A'

        profile = {
            'name': player_name,
            'position': position,
            'height': common_data['HEIGHT'].values[0] if 'HEIGHT' in common_data.columns else 'N/A',
            'weight': common_data['WEIGHT'].values[0] if 'WEIGHT' in common_data.columns else 'N/A',
            'team': common_data['TEAM_NAME'].values[0] if 'TEAM_NAME' in common_data.columns else 'N/A',
            'team_logo': TEAM_LOGOS.get(common_data['TEAM_ABBREVIATION'].values[0], '') if 'TEAM_ABBREVIATION' in common_data.columns else ''
        }

        recent_games_log = playergamelog.PlayerGameLog(player_id=player_id, season='2023-24')
        recent_games_data = recent_games_log.get_data_frames()[0]
        
        if 'TEAM_ABBREVIATION' not in recent_games_data.columns:
            recent_games_data['TEAM_ABBREVIATION'] = recent_games_data['MATCHUP'].apply(lambda x: x.split(' ')[0])

        recent_games_data = recent_games_data.head(10)

        recent_games = []
        for index, row in recent_games_data.iterrows():
            ts_percent = (row['PTS'] / (2 * (row['FGA'] + 0.44 * row['FTA']))) * 100 if (row['FGA'] + 0.44 * row['FTA']) != 0 else 0
            game_stats = {
                'date': row['GAME_DATE'],
                'team_for': row['TEAM_ABBREVIATION'],
                'team_for_logo': TEAM_LOGOS.get(row['TEAM_ABBREVIATION'], ''),
                'team_against': row['MATCHUP'].split(' ')[-1],
                'team_against_logo': TEAM_LOGOS.get(row['MATCHUP'].split(' ')[-1], ''),
                'minutes': row['MIN'],
                'points': row['PTS'],
                'rebounds': row['REB'],
                'assists': row['AST'],
                'fg_percent': round(row['FG_PCT'] * 100, 2),
                'ts_percent': round(ts_percent, 2),
                'plus_minus': row.get('PLUS_MINUS', 'N/A')
            }
            recent_games.append(game_stats)

        return render_template('player_profile.html', profile=profile, recent_games=recent_games)

    except Exception as e:
        return jsonify(error=str(e)), 500
<<<<<<< HEAD
    
@app.route('/team_profile/<team_abbreviation>')
def get_team_profile(team_abbreviation):
    try:
<<<<<<< HEAD
        team_info, roster, recent_games, advanced_stats = fetch_team_data(team_abbreviation)
        return render_template('team_profile.html', team_info=team_info, roster=roster, recent_games=recent_games, advanced_stats=advanced_stats)
=======
        team_info, roster, recent_games = fetch_team_data(team_abbreviation)
        return render_template('team_profile.html', team_info=team_info, roster=roster, recent_games=recent_games)
>>>>>>> 6e63ab058810a2cb12c8b9df2bc92d40a7769f8e
    except Exception as e:
        return jsonify(error=str(e)), 500

=======

@app.route('/team_profile/<team_search_term>')
def get_team_profile(team_search_term):
    team_info = teams.find_team_by_abbreviation(team_search_term.upper())
    
    if not team_info:
        all_teams = teams.get_teams()
        team_info = next((team for team in all_teams if team['full_name'].lower() == team_search_term.lower()), None)

    if not team_info:
        return jsonify(error="Team not found"), 404

    try:
        team_info_dict, roster, recent_games, advanced_stats = fetch_team_data(team_info['abbreviation'])
        return render_template('team_profile.html', team_info=team_info_dict, roster=roster, recent_games=recent_games, advanced_stats=advanced_stats)
    except Exception as e:
        return jsonify(error=str(e)), 500



>>>>>>> Final updates for Fresh Finder project
def fetch_team_data(team_abbreviation):
    team_info = teams.find_team_by_abbreviation(team_abbreviation)
    if not team_info:
        return jsonify(error="Team not found"), 404

    team_id = team_info['id']

    team_details = teamdetails.TeamDetails(team_id=team_id)
    team_data = team_details.get_data_frames()[0]
    roster_data = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
    game_log = teamgamelog.TeamGameLog(team_id=team_id, season='2023-24')
    game_log_data = game_log.get_data_frames()[0].head(10)

<<<<<<< HEAD
<<<<<<< HEAD
    advanced_stats = leaguedashteamstats.LeagueDashTeamStats(team_id=team_id).get_data_frames()[0]

=======
>>>>>>> 6e63ab058810a2cb12c8b9df2bc92d40a7769f8e
    team_info = {
        'name': team_data['TEAM_NAME'].values[0] if 'TEAM_NAME' in team_data.columns else team_info.get('full_name', 'N/A'),
        'city': team_data['TEAM_CITY'].values[0] if 'TEAM_CITY' in team_data.columns else 'N/A',
        'state': team_data['TEAM_STATE'].values[0] if 'TEAM_STATE' in team_data.columns else 'N/A',
        'abbreviation': team_data['TEAM_ABBREVIATION'].values[0] if 'TEAM_ABBREVIATION' in team_data.columns else 'N/A',
=======
    league_stats = leaguedashteamstats.LeagueDashTeamStats(season='2023-24')
    advanced_stats = league_stats.get_data_frames()[0]
    team_advanced_stats = advanced_stats[advanced_stats['TEAM_ID'] == team_id]

    team_info_dict = {
        'name': team_data['TEAM_NAME'].values[0] if 'TEAM_NAME' in team_data.columns else team_info.get('full_name', 'N/A'),
        'city': team_data['TEAM_CITY'].values[0] if 'TEAM_CITY' in team_data.columns else team_info.get('city', 'N/A'),
        'state': team_data['TEAM_STATE'].values[0] if 'TEAM_STATE' in team_data.columns else team_info.get('state', 'N/A'),
        'abbreviation': team_data['TEAM_ABBREVIATION'].values[0] if 'TEAM_ABBREVIATION' in team_data.columns else team_info.get('abbreviation', 'N/A'),
>>>>>>> Final updates for Fresh Finder project
        'logo': TEAM_LOGOS.get(team_abbreviation, '')
    }

    roster = []
    for index, row in roster_data.iterrows():
        player_info = {
            'player_name': row['PLAYER'],
            'position': row['POSITION'],
            'height': row['HEIGHT'],
            'weight': row['WEIGHT'],
            'jersey_number': f"#{row['NUM'].strip('#')}"
        }
        roster.append(player_info)

    recent_games = []
    for index, row in game_log_data.iterrows():
        game_info = {
            'date': row['GAME_DATE'],
            'matchup': row['MATCHUP'],
            'result': row['WL'],
            'score': f"{row['PTS']} - {row['PTS_OPP']}" if 'PTS_OPP' in row else f"{row['PTS']} - N/A",
            'points': row['PTS'],
            'rebounds': row['REB'],
            'assists': row['AST'],
            'fg_percent': round(row['FG_PCT'] * 100, 2),
            'threep_percent': round(row['FG3_PCT'] * 100, 2),
            'ft_percent': round(row['FT_PCT'] * 100, 2)
        }
        recent_games.append(game_info)

<<<<<<< HEAD
<<<<<<< HEAD
    advanced_stats = {
        'off_rating': advanced_stats['OFF_RATING'][0],
        'def_rating': advanced_stats['DEF_RATING'][0],
        'net_rating': advanced_stats['NET_RATING'][0],
        'reb_percent': advanced_stats['REB_PCT'][0],
        'ast_percent': advanced_stats['AST_PCT'][0],
        'ts_percent': advanced_stats['TS_PCT'][0]
    }

    return team_info, roster, recent_games, advanced_stats
=======
    return team_info, roster, recent_games
>>>>>>> 6e63ab058810a2cb12c8b9df2bc92d40a7769f8e
=======
    advanced_stats_dict = {
        'off_rating': team_advanced_stats['OFF_RATING'].values[0] if 'OFF_RATING' in team_advanced_stats.columns else 'N/A',
        'def_rating': team_advanced_stats['DEF_RATING'].values[0] if 'DEF_RATING' in team_advanced_stats.columns else 'N/A',
        'net_rating': team_advanced_stats['NET_RATING'].values[0] if 'NET_RATING' in team_advanced_stats.columns else 'N/A',
        'reb_percent': team_advanced_stats['REB_PCT'].values[0] if 'REB_PCT' in team_advanced_stats.columns else 'N/A',
        'ast_percent': team_advanced_stats['AST_PCT'].values[0] if 'AST_PCT' in team_advanced_stats.columns else 'N/A',
        'ts_percent': team_advanced_stats['TS_PCT'].values[0] if 'TS_PCT' in team_advanced_stats.columns else 'N/A'
    }

    return team_info_dict, roster, recent_games, advanced_stats_dict


@app.route('/team_autocomplete')
def team_autocomplete():
    term = request.args.get('term').lower()
    teams_list = teams.get_teams()
    
    results = [
        {'label': team['full_name'], 'value': team['abbreviation']}
        for team in teams_list if term in team['full_name'].lower() or term in team['abbreviation'].lower()
    ]
    
    return jsonify(results)
>>>>>>> Final updates for Fresh Finder project

@app.route('/team_search', methods=['GET', 'POST'])
def team_search():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        if not search_term:
            return jsonify(error="Search term is required"), 400

<<<<<<< HEAD
        matched_teams = [team for team in teams.get_teams() if search_term.lower() in team['full_name'].lower()]

        return render_template('team_search_results.html', teams=matched_teams)

    return render_template('team_search.html')
=======
        search_term = search_term.lower()

        matched_team = teams.find_team_by_abbreviation(search_term.upper())

        if not matched_team:
            matched_teams = [team for team in teams.get_teams() if search_term in team['full_name'].lower()]
            if matched_teams:
                matched_team = matched_teams[0]  
                
        if matched_team:
            return redirect(url_for('get_team_profile', team_search_term=matched_team['abbreviation']))
        else:
            return jsonify(error="Team not found"), 404

    return redirect(url_for('landing'))


>>>>>>> Final updates for Fresh Finder project

@app.route('/player_stats_average', methods=['GET'])
def get_player_stats_average():
    player_name = request.args.get('player_name')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not player_name:
        return jsonify(error="Player name is required"), 400

    player_info = players.find_players_by_full_name(player_name)
    if not player_info:
        return jsonify(message="Player not found"), 404

    player_id = player_info[0]['id']

    try:
        if start_date and end_date:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        else:
            return jsonify(error="Start date and end date are required"), 400

        game_log = playergamelog.PlayerGameLog(player_id=player_id, date_from_nullable=start_date_obj.strftime('%m/%d/%Y'), date_to_nullable=end_date_obj.strftime('%m/%d/%Y'))
        data_frame = game_log.get_data_frames()[0]

        if data_frame.empty:
            return jsonify(message="No matches played on these dates"), 404

        averages = {
            'player_name': player_name,
            'games_played': len(data_frame),
            'average_minutes': round(data_frame['MIN'].mean(), 2),
            'average_points': round(data_frame['PTS'].mean(), 2),
            'average_rebounds': round(data_frame['REB'].mean(), 2),
            'average_assists': round(data_frame['AST'].mean(), 2),
            'average_fg_percent': round(data_frame['FG_PCT'].mean() * 100, 2),
            'average_ts_percent': round((data_frame['PTS'] / (2 * (data_frame['FGA'] + 0.44 * data_frame['FTA']))).mean() * 100, 2) if not data_frame.empty else 0,
            'average_plus_minus': round(data_frame['PLUS_MINUS'].mean(), 2)
        }

        return jsonify(averages)

    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/game_box_score/<game_id>')
def game_box_score(game_id):
    try:
<<<<<<< HEAD
<<<<<<< HEAD
=======
        # Fetch game details using game_id (This is a placeholder as NBA API might not support direct game ID lookup)
        # Assuming playergamelog can provide game details. Replace this with the correct API call if available.
>>>>>>> 6e63ab058810a2cb12c8b9df2bc92d40a7769f8e
=======
>>>>>>> Final updates for Fresh Finder project
        game_log = playergamelog.PlayerGameLog(player_id=player_id)
        data_frame = game_log.get_data_frames()[0]
        game_details = data_frame[data_frame['Game_ID'] == game_id]

        if game_details.empty:
            return jsonify(message="Game details not found"), 404

        game_stats = {
            'game_date': game_details['GAME_DATE'].values[0],
            'matchup': game_details['MATCHUP'].values[0],
            'wl': game_details['WL'].values[0],
            'minutes': game_details['MIN'].values[0],
            'points': game_details['PTS'].values[0],
            'rebounds': game_details['REB'].values[0],
            'assists': game_details['AST'].values[0],
            'fg_percent': round(game_details['FG_PCT'].values[0] * 100, 2),
            'threep_percent': round(game_details['FG3_PCT'].values[0] * 100, 2),
            'ft_percent': round(game_details['FT_PCT'].values[0] * 100, 2),
            'plus_minus': game_details['PLUS_MINUS'].values[0]
        }

        return render_template('game_box_score.html', game_stats=game_stats)

    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    print("App started, current directory:", os.getcwd())
    print("Templates folder exists:", os.path.isdir('templates'))
    print("player_profile.html exists:", os.path.isfile('templates/player_profile.html'))
<<<<<<< HEAD
<<<<<<< HEAD
    app.run(debug=True, port=5001)
=======
    app.run(debug=True)
>>>>>>> 6e63ab058810a2cb12c8b9df2bc92d40a7769f8e
=======
    app.run(debug=True, port=5002)
>>>>>>> Final updates for Fresh Finder project
