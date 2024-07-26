from flask import Flask, jsonify, render_template, request
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, commonplayerinfo, playercareerstats, teamgamelog, commonteamroster, teamdetails
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

@app.route('/')
def index():
    return render_template('index.html')

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

        game_log = playergamelog.PlayerGameLog(player_id=player_id, date_from_nullable=start_date_obj.strftime('%m/%d/%Y'), date_to_nullable=end_date_obj.strftime('%m/%d/%Y'))
        data_frame = game_log.get_data_frames()[0]

        if data_frame.empty:
            return jsonify(message="No matches played on this date"), 404

        data_frame['TEAM_ABBREVIATION'] = data_frame['MATCHUP'].apply(lambda x: x.split(' ')[0])
        data_frame['MATCHUP'] = data_frame['MATCHUP'].apply(lambda x: x.split(' ')[-1])

        games = []
        for index, row in data_frame.iterrows():
            ts_percent = (row['PTS'] / (2 * (row['FGA'] + 0.44 * row['FTA']))) * 100 if (row['FGA'] + 0.44 * row['FTA']) != 0 else 0
            game_stats = {
                'game_id': row['Game_ID'],
                'name': player_name,
                'team_for': row['TEAM_ABBREVIATION'],
                'team_logo': TEAM_LOGOS.get(row['TEAM_ABBREVIATION'], ''),
                'team_against': row['MATCHUP'],
                'opposing_team_logo': TEAM_LOGOS.get(row['MATCHUP'], ''),
                'minutes': row.get('MIN', 'N/A'),
                'points': row['PTS'],
                'rebounds': row['REB'],
                'assists': row['AST'],
                'fg_percent': round(row['FG_PCT'] * 100, 2),
                'ts_percent': round(ts_percent, 2),
                'plus_minus': row.get('PLUS_MINUS', 'N/A')
            }
            games.append(game_stats)

        return jsonify(games)

    except Exception as e:
        return jsonify(error=str(e)), 500

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
    
@app.route('/team_profile/<team_abbreviation>')
def get_team_profile(team_abbreviation):
    try:
        team_info, roster, recent_games = fetch_team_data(team_abbreviation)
        return render_template('team_profile.html', team_info=team_info, roster=roster, recent_games=recent_games)
    except Exception as e:
        return jsonify(error=str(e)), 500

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

    team_info = {
        'name': team_data['TEAM_NAME'].values[0] if 'TEAM_NAME' in team_data.columns else team_info.get('full_name', 'N/A'),
        'city': team_data['TEAM_CITY'].values[0] if 'TEAM_CITY' in team_data.columns else 'N/A',
        'state': team_data['TEAM_STATE'].values[0] if 'TEAM_STATE' in team_data.columns else 'N/A',
        'abbreviation': team_data['TEAM_ABBREVIATION'].values[0] if 'TEAM_ABBREVIATION' in team_data.columns else 'N/A',
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

    return team_info, roster, recent_games

@app.route('/team_search', methods=['GET', 'POST'])
def team_search():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        if not search_term:
            return jsonify(error="Search term is required"), 400

        matched_teams = [team for team in teams.get_teams() if search_term.lower() in team['full_name'].lower()]

        return render_template('team_search_results.html', teams=matched_teams)

    return render_template('team_search.html')

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
        # Fetch game details using game_id (This is a placeholder as NBA API might not support direct game ID lookup)
        # Assuming playergamelog can provide game details. Replace this with the correct API call if available.
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
    app.run(debug=True)
