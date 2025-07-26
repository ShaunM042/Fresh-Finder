# Standard Library
import os
import json
import hashlib
import time
from datetime import datetime, timedelta

# Third-Party Libraries
import requests
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    playergamelog, commonplayerinfo, playercareerstats,
    teamgamelog, commonteamroster, teamdetails, leaguedashteamstats
)
from nba_api.stats.library.http import NBAStatsHTTP

# Application-Specific Modules
from team_logos import TEAM_LOGOS

# Cache Configuration
CACHE_DIR = 'cache'
CACHE_DURATION = 3600  # 1 hour in seconds

def ensure_cache_directory():
    """Ensure cache directory exists"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def generate_cache_key(*args, **kwargs):
    """Generate a unique cache key based on function arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def get_cache_file_path(cache_key):
    """Get the full path for a cache file"""
    return os.path.join(CACHE_DIR, f"{cache_key}.json")

def is_cache_valid(cache_file_path):
    """Check if cache file exists and is still valid"""
    if not os.path.exists(cache_file_path):
        return False
    
    # Check if cache is expired
    file_age = time.time() - os.path.getmtime(cache_file_path)
    return file_age < CACHE_DURATION

def save_to_cache(cache_key, data):
    """Save data to cache file"""
    try:
        ensure_cache_directory()
        cache_file_path = get_cache_file_path(cache_key)
        
        cache_data = {
            'timestamp': time.time(),
            'data': data
        }
        
        with open(cache_file_path, 'w') as f:
            json.dump(cache_data, f, default=str)
        
        print(f"Data cached with key: {cache_key}")
    except Exception as e:
        print(f"Failed to save cache: {e}")

def load_from_cache(cache_key):
    """Load data from cache file"""
    try:
        cache_file_path = get_cache_file_path(cache_key)
        
        if not is_cache_valid(cache_file_path):
            return None
        
        with open(cache_file_path, 'r') as f:
            cache_data = json.load(f)
        
        print(f"Data loaded from cache: {cache_key}")
        return cache_data['data']
    except Exception as e:
        print(f"Failed to load cache: {e}")
        return None

def cached_api_call(func, *args, **kwargs):
    """Wrapper function to cache API calls"""
    # Generate cache key
    cache_key = generate_cache_key(func.__name__, *args, **kwargs)
    
    # Try to load from cache first
    cached_data = load_from_cache(cache_key)
    if cached_data is not None:
        # Convert back to DataFrame if it was a DataFrame
        if isinstance(cached_data, dict) and 'dataframe_data' in cached_data:
            return pd.DataFrame(cached_data['dataframe_data'])
        return cached_data
    
    # Make API call if not in cache
    try:
        result = func(*args, **kwargs)
        
        # Prepare data for caching
        if hasattr(result, 'get_data_frames'):
            # NBA API endpoint result
            data_frames = result.get_data_frames()
            if data_frames and len(data_frames) > 0:
                df = data_frames[0]
                cache_data = {'dataframe_data': df.to_dict('records')}
                save_to_cache(cache_key, cache_data)
                return df
        elif isinstance(result, pd.DataFrame):
            # Direct DataFrame result
            cache_data = {'dataframe_data': result.to_dict('records')}
            save_to_cache(cache_key, cache_data)
            return result
        else:
            # Other data types
            save_to_cache(cache_key, result)
            return result
            
    except Exception as e:
        print(f"API call failed: {e}")
        raise e

def clear_expired_cache():
    """Clear expired cache files"""
    try:
        if not os.path.exists(CACHE_DIR):
            return
        
        current_time = time.time()
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(CACHE_DIR, filename)
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > CACHE_DURATION:
                    os.remove(file_path)
                    print(f"Removed expired cache file: {filename}")
    except Exception as e:
        print(f"Failed to clear expired cache: {e}")

def get_current_nba_season():
    """Get the current NBA season based on the date"""
    current_date = datetime.now()
    current_year = current_date.year
    
    # NBA season starts in October, so if we're before October, use previous year
    if current_date.month < 10:
        start_year = current_year - 1
    else:
        start_year = current_year
    
    return f"{start_year}-{str(start_year + 1)[2:]}"

def get_available_seasons():
    """Get list of available NBA seasons (last 5 years)"""
    current_date = datetime.now()
    current_year = current_date.year
    
    # NBA season starts in October, so if we're before October, use previous year
    if current_date.month < 10:
        start_year = current_year - 1
    else:
        start_year = current_year
    
    seasons = []
    for i in range(5):  # Last 5 seasons
        year = start_year - i
        seasons.append(f"{year}-{str(year + 1)[2:]}")
    
    return seasons

def get_player_data_with_fallback(player_id, data_func, **kwargs):
    """Try to get player data, falling back to previous seasons if current season has no data"""
    seasons = get_available_seasons()
    
    for season in seasons:
        try:
            kwargs['season'] = season
            # Add timeout parameter if it's a game log request
            if hasattr(data_func, '__name__') and 'gamelog' in str(data_func).lower():
                kwargs['timeout'] = 60
            
            # Use cached API call
            df = cached_api_call(data_func, player_id=player_id, **kwargs)
            if hasattr(df, 'empty') and not df.empty:
                return df, season
            elif df is not None:
                return df, season
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            # Skip timeout errors and try next season
            continue
        except Exception:
            continue
    
    # If no data found in any season, return empty dataframe
    return pd.DataFrame(), seasons[0]

def get_team_data_with_fallback(team_id, data_func, **kwargs):
    """Try to get team data, falling back to previous seasons if current season has no data"""
    seasons = get_available_seasons()
    
    for season in seasons:
        try:
            kwargs['season'] = season
            # Add timeout parameter if it's a game log request
            if hasattr(data_func, '__name__') and 'gamelog' in str(data_func).lower():
                kwargs['timeout'] = 60
                
            # Use cached API call
            df = cached_api_call(data_func, team_id=team_id, **kwargs)
            if hasattr(df, 'empty') and not df.empty:
                return df, season
            elif df is not None:
                return df, season
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            # Skip timeout errors and try next season
            continue
        except Exception:
            continue
    
    # If no data found in any season, return empty dataframe
    return pd.DataFrame(), seasons[0]

def get_league_data_with_fallback(data_func, **kwargs):
    """Try to get league data, falling back to previous seasons if current season has no data"""
    seasons = get_available_seasons()
    
    for season in seasons:
        try:
            kwargs['season'] = season
            # Add timeout parameter if it's a game log request
            if hasattr(data_func, '__name__') and 'gamelog' in str(data_func).lower():
                kwargs['timeout'] = 60
                
            # Use cached API call
            df = cached_api_call(data_func, **kwargs)
            if hasattr(df, 'empty') and not df.empty:
                return df, season
            elif df is not None:
                return df, season
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            # Skip timeout errors and try next season
            continue
        except Exception:
            continue
    
    # If no data found in any season, return empty dataframe
    return pd.DataFrame(), seasons[0]

def configure_nba_api():
    NBAStatsHTTP._session = requests.Session()
    NBAStatsHTTP._session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'
    })
    # Increase timeout to 60 seconds
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.adapters.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
    )
    NBAStatsHTTP._session.mount('https://', adapter)
    NBAStatsHTTP._session.mount('http://', adapter)

load_dotenv()
configure_nba_api()

app = Flask(__name__, template_folder='templates')

# Clear expired cache on app startup
@app.before_request
def startup():
    """Initialize app and clear expired cache"""
    if not hasattr(startup, 'called'):
        clear_expired_cache()
        print("Fresh Finder started with caching enabled")
        startup.called = True

# Add cache management route for admin purposes
@app.route('/admin/clear-cache')
def clear_cache():
    """Clear all cache files (admin route)"""
    try:
        if os.path.exists(CACHE_DIR):
            import shutil
            shutil.rmtree(CACHE_DIR)
            ensure_cache_directory()
            return jsonify({"status": "success", "message": "Cache cleared successfully"})
        else:
            return jsonify({"status": "info", "message": "No cache directory found"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Add cache statistics route
@app.route('/admin/cache-stats')
def cache_stats():
    """Get cache statistics (admin route)"""
    try:
        if not os.path.exists(CACHE_DIR):
            return jsonify({"cache_files": 0, "total_size": 0})
        
        cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.json')]
        total_size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in cache_files)
        
        return jsonify({
            "cache_files": len(cache_files),
            "total_size": f"{total_size / 1024:.2f} KB",
            "cache_duration": f"{CACHE_DURATION / 3600:.1f} hours"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def landing():
    return render_template('landing.html')

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
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=7)

        game_log = playergamelog.PlayerGameLog(
            player_id=player_id,
            date_from_nullable=start_date_obj.strftime('%m/%d/%Y'),
            date_to_nullable=end_date_obj.strftime('%m/%d/%Y')
        )
        data_frame = game_log.get_data_frames()[0]

        if data_frame.empty:
            return jsonify(message="No matches played on this date"), 404

        data_frame['TEAM_ABBREVIATION'] = data_frame['MATCHUP'].apply(lambda x: x.split(' ')[0])
        data_frame['MATCHUP'] = data_frame['MATCHUP'].apply(lambda x: x.split(' ')[-1])

        games = []
        for index, row in data_frame.iterrows():
            turnovers = row['TO'] if 'TO' in data_frame.columns else 'N/A'

            ts_percent = (row['PTS'] / (2 * (row['FGA'] + 0.44 * row['FTA']))) * 100 if (row['FGA'] + 0.44 * row['FTA']) != 0 else 0
            game_stats = {
                'game_id': row['Game_ID'],
                'game_date': row['GAME_DATE'],
                'name': player_name,
                'team_for': row['TEAM_ABBREVIATION'],
                'team_logo': TEAM_LOGOS.get(row['TEAM_ABBREVIATION'], ''),
                'team_against': row['MATCHUP'],
                'opposing_team_logo': TEAM_LOGOS.get(row['MATCHUP'], ''),
                'minutes': row.get('MIN', 'N/A'),
                'points': row['PTS'],
                'rebounds': row['REB'],
                'assists': row['AST'],
                'steals': row['STL'],
                'blocks': row['BLK'],
                'fg_percent': round(row['FG_PCT'] * 100, 2),
                'ts_percent': round(ts_percent, 2),
                'plus_minus': row.get('PLUS_MINUS', 'N/A'),
                'turnovers': turnovers
            }
            games.append(game_stats)

        current_date = datetime.now().strftime('%Y-%m-%d')
        return render_template('player_stats.html', stats=games, player_name=player_name, start_date=start_date, end_date=end_date, current_date=current_date)

    except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
        return jsonify(error="NBA API request timed out. Please try again later."), 408
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/player_profile/<player_name>')
def get_player_profile(player_name):
    player_info = players.find_players_by_full_name(player_name)
    if not player_info:
        return jsonify(message="Player not found"), 404

    player_id = player_info[0]['id']

    try:
        # Use cached API calls for better performance
        career_data = cached_api_call(playercareerstats.PlayerCareerStats, player_id=player_id)
        common_data = cached_api_call(commonplayerinfo.CommonPlayerInfo, player_id=player_id)

        position = common_data['POSITION'].values[0] if 'POSITION' in common_data.columns and not common_data.empty else 'N/A'

        profile = {
            'name': player_name,
            'position': position,
            'height': common_data['HEIGHT'].values[0] if 'HEIGHT' in common_data.columns else 'N/A',
            'weight': common_data['WEIGHT'].values[0] if 'WEIGHT' in common_data.columns else 'N/A',
            'team': common_data['TEAM_NAME'].values[0] if 'TEAM_NAME' in common_data.columns else 'N/A',
            'team_logo': TEAM_LOGOS.get(common_data['TEAM_ABBREVIATION'].values[0], '') if 'TEAM_ABBREVIATION' in common_data.columns else ''
        }

        recent_games_data, used_season = get_player_data_with_fallback(player_id, playergamelog.PlayerGameLog)
        
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

def fetch_team_data(team_abbreviation):
    team_info = teams.find_team_by_abbreviation(team_abbreviation)
    if not team_info:
        return jsonify(error="Team not found"), 404

    team_id = team_info['id']

    # Use cached API calls for better performance
    team_details_data = cached_api_call(teamdetails.TeamDetails, team_id=team_id)
    roster_data = cached_api_call(commonteamroster.CommonTeamRoster, team_id=team_id)
    game_log_data, used_season = get_team_data_with_fallback(team_id, teamgamelog.TeamGameLog)
    game_log_data = game_log_data.head(10)

    # Cache league stats call
    league_stats_data = cached_api_call(leaguedashteamstats.LeagueDashTeamStats, season=used_season)
    team_advanced_stats = league_stats_data[league_stats_data['TEAM_ID'] == team_id]

    team_info_dict = {
        'name': team_details_data['TEAM_NAME'].values[0] if 'TEAM_NAME' in team_details_data.columns else team_info.get('full_name', 'N/A'),
        'city': team_details_data['TEAM_CITY'].values[0] if 'TEAM_CITY' in team_details_data.columns else team_info.get('city', 'N/A'),
        'state': team_details_data['TEAM_STATE'].values[0] if 'TEAM_STATE' in team_details_data.columns else team_info.get('state', 'N/A'),
        'abbreviation': team_details_data['TEAM_ABBREVIATION'].values[0] if 'TEAM_ABBREVIATION' in team_details_data.columns else team_info.get('abbreviation', 'N/A'),
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

@app.route('/team_search', methods=['GET', 'POST'])
def team_search():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        if not search_term:
            return jsonify(error="Search term is required"), 400

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
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
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
@app.route('/game_box_score/<game_id>/<player_name>')
def game_box_score(game_id, player_name):
    player_info = players.find_players_by_full_name(player_name)
    if not player_info:
        return jsonify(message="Player not found"), 404

    player_id = player_info[0]['id']

    try:
        data_frame, used_season = get_player_data_with_fallback(player_id, playergamelog.PlayerGameLog)
        game_details = data_frame[data_frame['Game_ID'] == game_id]

        if game_details.empty:
            return jsonify(message="Game details not found"), 404

        team_for = game_details['MATCHUP'].values[0].split(' ')[0]
        team_against = game_details['MATCHUP'].values[0].split(' ')[-1]

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
            'plus_minus': game_details['PLUS_MINUS'].values[0],
            'player_name': player_name,
            'team_for': team_for,
            'team_against': team_against
        }

        return render_template('game_box_score.html', game_stats=game_stats)

    except Exception as e:
        return jsonify(error=str(e)), 500
@app.route('/team_stats')
def team_stats():
    team_name = request.args.get("team_name")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not team_name:
        return render_template("team_stats.html", stats=[])

    nba_teams = teams.get_teams()
    team = next((t for t in nba_teams if t['abbreviation'].lower() == team_name.lower() or t['full_name'].lower() == team_name.lower()), None)

    if not team:
        return render_template("team_stats.html", stats=[])

    team_id = team['id']
    team_abbreviation = team['abbreviation']

    try:
        games_df, used_season = get_team_data_with_fallback(team_id, teamgamelog.TeamGameLog, season_type_all_star='Regular Season')
        games_df['GAME_DATE'] = pd.to_datetime(games_df['GAME_DATE'])

        if start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            games_df = games_df[(games_df['GAME_DATE'] >= start) & (games_df['GAME_DATE'] <= end)]

        if games_df.empty:
            return render_template("team_stats.html", stats=[])

        if 'TEAM_ABBREVIATION' not in games_df.columns:
            games_df['TEAM_ABBREVIATION'] = games_df['MATCHUP'].apply(lambda x: x.split(' ')[0])

        team_games = []
        for _, row in games_df.iterrows():
            team_games.append({
                "game_date": row["GAME_DATE"].strftime("%b %d, %Y"),
                "team": team_abbreviation,
                "team_logo": TEAM_LOGOS.get(team_abbreviation, ""),
                "opponent": row["MATCHUP"].split(" ")[-1],
                "opponent_logo": TEAM_LOGOS.get(row["MATCHUP"].split(" ")[-1], ""),
                "points": row["PTS"],
                "rebounds": row["REB"],
                "assists": row["AST"],
                "fg_percent": round(row["FG_PCT"] * 100, 1),
                "threep_percent": round(row["FG3_PCT"] * 100, 1),
                "ft_percent": round(row["FT_PCT"] * 100, 1),
                "plus_minus": row["PLUS_MINUS"],
            })

        return render_template("team_stats.html", stats=team_games)

    except Exception as e:
        return jsonify(error=str(e)), 500
@app.route('/search_team_stats', methods=['POST'])
def search_team_stats():
    team_abbreviation = request.form['team_name'].upper()
    start_date = pd.to_datetime(request.form['start_date'])
    end_date = pd.to_datetime(request.form['end_date'])

    try:
        df, used_season = get_league_data_with_fallback(teamgamelog.TeamGameLog)
        df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])

        team_df = df[(df['TEAM_ABBREVIATION'] == team_abbreviation) & 
                     (df['GAME_DATE'] >= start_date) & 
                     (df['GAME_DATE'] <= end_date)]

        if team_df.empty:
            return render_template('team_stats.html', stats=[])

        stats = []
        for _, row in team_df.iterrows():
            stats.append({
                'game_date': row['GAME_DATE'].strftime('%B %d, %Y'),
                'team': row['TEAM_ABBREVIATION'],
                'team_logo': TEAM_LOGOS.get(row['TEAM_ABBREVIATION'], ''),
                'opponent': row['MATCHUP'].split(' ')[-1],
                'opponent_logo': TEAM_LOGOS.get(row['MATCHUP'].split(' ')[-1], ''),
                'points': row['PTS'],
                'rebounds': row['REB'],
                'assists': row['AST'],
                'fg_percent': round(row['FG_PCT'] * 100, 1),
                'threep_percent': round(row['FG3_PCT'] * 100, 1),
                'ft_percent': round(row['FT_PCT'] * 100, 1),
                'plus_minus': row.get('PLUS_MINUS', 'N/A')
            })

        return render_template('team_stats.html', stats=stats)

    except Exception as e:
        return jsonify(error=str(e))
@app.route('/team_stats_stretch', methods=['GET'])
def team_stats_stretch():
    try:
        team_abbreviation = request.args.get('team')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            today = datetime.now()
            end_date = today.strftime('%Y-%m-%d')
            start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')

        if not (team_abbreviation and start_date and end_date):
            return render_template('team_stats.html', stats=[])

        # Get all NBA teams
        all_teams = teams.get_teams()
        selected_team = next((team for team in all_teams if team['abbreviation'].lower() == team_abbreviation.lower()), None)

        if not selected_team:
            return render_template('team_stats.html', stats=[])

        team_id = selected_team['id']

        # Fetch the game logs for the team
        df, used_season = get_team_data_with_fallback(team_id, teamgamelog.TeamGameLog)

        # Convert date and filter
        df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        filtered = df[(df['GAME_DATE'] >= start_dt) & (df['GAME_DATE'] <= end_dt)]

        if filtered.empty:
            return render_template('team_stats.html', stats=[])

        stats = []
        for _, row in filtered.iterrows():
            stats.append({
                'game_date': row['GAME_DATE'].strftime('%B %d, %Y'),
                'team': selected_team['full_name'],
                'opponent': row['MATCHUP'].split(' ')[-1],
                'points': row.get('PTS', 0),
                'rebounds': row.get('REB', 0),
                'assists': row.get('AST', 0),
                'fg_percent': round(row.get('FG_PCT', 0) * 100, 1),
                'threep_percent': round(row.get('FG3_PCT', 0) * 100, 1),
                'ft_percent': round(row.get('FT_PCT', 0) * 100, 1),
                'plus_minus': row.get('PLUS_MINUS', 0),
                'team_logo': f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg",
                'opponent_logo': '',  
            })

        return render_template('team_stats.html', stats=stats)

    except Exception as e:
        return jsonify(error=str(e)), 500
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    print("App started, current directory:", os.getcwd())
    print("Templates folder exists:", os.path.isdir('templates'))
    print("player_profile.html exists:", os.path.isfile('templates/player_profile.html'))
    app.run(debug=True, port=5002)