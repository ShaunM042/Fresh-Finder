# Standard Library
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
import traceback

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

    # Prepare default context for rendering fallback UI
    current_date = datetime.now().strftime('%Y-%m-%d')
    def should_return_json():
        try:
            return request.args.get('debug') == '1' or 'application/json' in (request.headers.get('Accept') or '')
        except Exception:
            return False

    def render_fallback(message=None):
        if message:
            # Log the reason for the fallback for diagnosis
            app.logger.info(f"player_stats fallback: %s", message)
        if should_return_json():
            return jsonify({
                'ok': False,
                'route': '/player_stats',
                'error': message or 'No stats found',
                'player_name': player_name,
                'start_date': start_date,
                'end_date': end_date,
            }), 200
        return render_template('player_stats.html', stats=[], player_name=player_name or '', start_date=start_date, end_date=end_date, current_date=current_date)

    if not player_name:
        app.logger.warning("player_stats: missing player_name param")
        return render_fallback("Missing player name")

    try:
        player_info = players.find_players_by_full_name(player_name)
        if not player_info:
            app.logger.info("player_stats: player not found - %s", player_name)
            return render_fallback("Player not found")

        player_id = player_info[0].get('id')
        if not player_id:
            app.logger.error("player_stats: missing player id for %s", player_name)
            return render_fallback("Missing player id")

        # Parse dates or use last 7 days
        try:
            if start_date and end_date:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date_obj = datetime.now()
                start_date_obj = end_date_obj - timedelta(days=7)
        except ValueError:
            app.logger.exception("player_stats: invalid date format")
            return render_fallback("Invalid date format")

        # Call NBA API with robust guards
        try:
            game_log = playergamelog.PlayerGameLog(
                player_id=player_id,
                date_from_nullable=start_date_obj.strftime('%m/%d/%Y'),
                date_to_nullable=end_date_obj.strftime('%m/%d/%Y')
            )
            frames = getattr(game_log, 'get_data_frames', lambda: [])()
            data_frame = frames[0] if frames else pd.DataFrame()
            # Attempt to log raw JSON response for debugging
            try:
                raw_json = getattr(game_log, 'get_json', lambda: '')()
                if raw_json:
                    snippet = raw_json[:1000]
                    app.logger.debug("player_stats raw NBA API json (truncated): %s", snippet)
            except Exception:
                app.logger.debug("player_stats: unable to get raw json from nba_api endpoint")
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as te:
            app.logger.exception("player_stats: NBA API timeout")
            return render_fallback("NBA API timeout")
        except Exception:
            # Print full traceback to stdout/stderr in Render logs
            traceback.print_exc()
            app.logger.exception("player_stats: NBA API call failed")
            return render_fallback("NBA API error")

        if data_frame is None or data_frame.empty:
            app.logger.info("player_stats: no stats found for %s in range %s - %s", player_name, start_date_obj, end_date_obj)
            return render_fallback("No stats found in date range")

        # Derive safe columns
        if 'MATCHUP' in data_frame.columns:
            data_frame['TEAM_ABBREVIATION'] = data_frame['MATCHUP'].apply(lambda x: str(x).split(' ')[0] if isinstance(x, str) else '')
            data_frame['MATCHUP'] = data_frame['MATCHUP'].apply(lambda x: str(x).split(' ')[-1] if isinstance(x, str) else '')

        games = []
        for _, row in data_frame.iterrows():
            fga = row.get('FGA', 0)
            fta = row.get('FTA', 0)
            pts = row.get('PTS', 0)
            ts_percent = (pts / (2 * (fga + 0.44 * fta)) * 100) if (fga + 0.44 * fta) != 0 else 0

            game_stats = {
                'game_id': row.get('Game_ID') or row.get('GAME_ID'),
                'game_date': row.get('GAME_DATE', ''),
                'name': player_name,
                'team_for': row.get('TEAM_ABBREVIATION', ''),
                'team_logo': TEAM_LOGOS.get(row.get('TEAM_ABBREVIATION', ''), ''),
                'team_against': row.get('MATCHUP', ''),
                'opposing_team_logo': TEAM_LOGOS.get(row.get('MATCHUP', ''), ''),
                'minutes': row.get('MIN', 'N/A'),
                'points': pts,
                'rebounds': row.get('REB', 0),
                'assists': row.get('AST', 0),
                'steals': row.get('STL', 0),
                'blocks': row.get('BLK', 0),
                'fg_percent': round((row.get('FG_PCT', 0) or 0) * 100, 2),
                'ts_percent': round(ts_percent, 2),
                'plus_minus': row.get('PLUS_MINUS', 'N/A'),
                'turnovers': row.get('TO', 'N/A'),
            }
            games.append(game_stats)

        return render_template(
            'player_stats.html',
            stats=games,
            player_name=player_name,
            start_date=start_date,
            end_date=end_date,
            current_date=current_date,
        )

    except Exception as e:
        # Full traceback to logs and JSON in debug mode
        traceback.print_exc()
        app.logger.exception("player_stats: unexpected error")
        if should_return_json():
            return jsonify({
                'ok': False,
                'route': '/player_stats',
                'error': str(e),
                'traceback': traceback.format_exc(),
            }), 500
        return render_fallback("Unexpected error")

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

        # Get advanced statistics
        advanced_stats = get_advanced_player_stats(player_id, used_season)

        return render_template('player_profile.html', 
                             profile=profile, 
                             recent_games=recent_games,
                             advanced_stats=advanced_stats)

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

    # Get comprehensive advanced statistics
    advanced_stats_dict = get_advanced_team_stats(team_id, used_season)

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

    return team_info_dict, roster, recent_games, advanced_stats_dict

def calculate_per(stats_row):
    """
    Calculate Player Efficiency Rating (PER)
    Simplified version of PER calculation
    """
    try:
        # Extract necessary stats
        min_played = stats_row.get('MIN', 0)
        if min_played == 0:
            return 0
        
        pts = stats_row.get('PTS', 0)
        fgm = stats_row.get('FGM', 0)
        fga = stats_row.get('FGA', 0)
        ftm = stats_row.get('FTM', 0)
        fta = stats_row.get('FTA', 0)
        fg3m = stats_row.get('FG3M', 0)
        reb = stats_row.get('REB', 0)
        ast = stats_row.get('AST', 0)
        stl = stats_row.get('STL', 0)
        blk = stats_row.get('BLK', 0)
        tov = stats_row.get('TO', 0)
        pf = stats_row.get('PF', 0)
        
        # Simplified PER calculation (not the full Hollinger formula)
        per = ((pts + reb + ast + stl + blk) - ((fga - fgm) + (fta - ftm) + tov + pf)) / min_played * 48
        return max(0, per)  # Ensure PER is not negative
        
    except Exception:
        return 0

def calculate_true_shooting_percentage(pts, fga, fta):
    """Calculate True Shooting Percentage"""
    try:
        if (fga + 0.44 * fta) == 0:
            return 0
        return (pts / (2 * (fga + 0.44 * fta))) * 100
    except Exception:
        return 0

def calculate_effective_field_goal_percentage(fgm, fg3m, fga):
    """Calculate Effective Field Goal Percentage"""
    try:
        if fga == 0:
            return 0
        return ((fgm + 0.5 * fg3m) / fga) * 100
    except Exception:
        return 0

def calculate_usage_rate(fga, fta, tov, min_played, team_min, team_fga, team_fta, team_tov):
    """Calculate Usage Rate (approximate)"""
    try:
        if team_min == 0:
            return 0
        
        player_possessions = fga + 0.44 * fta + tov
        team_possessions = team_fga + 0.44 * team_fta + team_tov
        
        if team_possessions == 0:
            return 0
            
        usage_rate = (player_possessions * (team_min / 5)) / (min_played * team_possessions) * 100
        return min(100, max(0, usage_rate))  # Cap between 0-100%
    except Exception:
        return 0

def get_advanced_player_stats(player_id, season=None):
    """Get advanced statistics for a player"""
    try:
        if season is None:
            season = get_current_nba_season()
        
        # Get detailed player stats
        career_data = cached_api_call(playercareerstats.PlayerCareerStats, player_id=player_id)
        
        # Find season data
        season_data = career_data[career_data['SEASON_ID'] == season]
        if season_data.empty and not career_data.empty:
            season_data = career_data.tail(1)  # Get most recent season
            
        if season_data.empty:
            return {}
            
        row = season_data.iloc[0]
        
        # Calculate advanced metrics
        per = calculate_per(row)
        ts_pct = calculate_true_shooting_percentage(row.get('PTS', 0), row.get('FGA', 0), row.get('FTA', 0))
        efg_pct = calculate_effective_field_goal_percentage(row.get('FGM', 0), row.get('FG3M', 0), row.get('FGA', 0))
        
        return {
            'per': round(per, 2),
            'ts_percent': round(ts_pct, 2),
            'efg_percent': round(efg_pct, 2),
            'games_played': row.get('GP', 0),
            'minutes_per_game': round(row.get('MIN', 0) / max(1, row.get('GP', 1)), 1),
            'usage_rate': 0  # Would need team data for accurate calculation
        }
        
    except Exception as e:
        print(f"Error calculating advanced player stats: {e}")
        return {}

def get_advanced_team_stats(team_id, season=None):
    """Get comprehensive advanced statistics for a team"""
    try:
        if season is None:
            season = get_current_nba_season()
        
        # Get team stats from league dashboard
        league_stats = cached_api_call(leaguedashteamstats.LeagueDashTeamStats, season=season)
        team_stats = league_stats[league_stats['TEAM_ID'] == team_id]
        
        if team_stats.empty:
            return {}
            
        row = team_stats.iloc[0]
        
        # Extract advanced metrics
        advanced_stats = {
            'off_rating': round(row.get('OFF_RATING', 0), 1),
            'def_rating': round(row.get('DEF_RATING', 0), 1),
            'net_rating': round(row.get('NET_RATING', 0), 1),
            'reb_percent': round(row.get('REB_PCT', 0), 1),
            'ast_percent': round(row.get('AST_PCT', 0), 1),
            'ts_percent': round(row.get('TS_PCT', 0) * 100, 1),
            'effective_fg_pct': round(((row.get('FGM', 0) + 0.5 * row.get('FG3M', 0)) / max(1, row.get('FGA', 0))) * 100, 1),
            'turnover_pct': round(row.get('TOV_PCT', 0), 1),
            'steal_pct': round(row.get('STL_PCT', 0), 1),
            'block_pct': round(row.get('BLK_PCT', 0), 1),
            'wins': row.get('W', 0),
            'losses': row.get('L', 0),
            'win_percentage': round(row.get('W_PCT', 0) * 100, 1),
            'plus_minus': round(row.get('PLUS_MINUS', 0), 1)
        }
        
        return advanced_stats
        
    except Exception as e:
        print(f"Error getting advanced team stats: {e}")
        return {}

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