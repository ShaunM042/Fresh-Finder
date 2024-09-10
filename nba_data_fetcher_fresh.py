from nba_api.stats.static import players, teams
<<<<<<< HEAD
from nba_api.stats.endpoints import playergamelog, teamgamelog
import json
import time
=======
from nba_api.stats.endpoints import playergamelog, teamgamelog, teamdetails, commonteamroster
from flask import jsonify
>>>>>>> Final updates for Fresh Finder project

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

def fetch_nba_data(day, month, year):
<<<<<<< HEAD
    # Using the nba_api to fetch player box scores
=======
>>>>>>> Final updates for Fresh Finder project
    target_date = f'{year}-{month:02d}-{day:02d}'
    players_stats = []
    
    all_players = players.get_players()
    for player in all_players:
        player_id = player['id']
        try:
            game_log = playergamelog.PlayerGameLog(player_id=player_id, date_from_nullable=target_date, date_to_nullable=target_date)
            games = game_log.get_data_frames()[0]
            if not games.empty:
                players_stats.append(games.iloc[0].to_dict())
        except:
            continue
    
    cleaned_data = []
    for player in players_stats:
        made_field_goals = player.get('FGM', 0)
        attempted_field_goals = player.get('FGA', 0)
        made_three_point_field_goals = player.get('FG3M', 0)
        attempted_three_point_field_goals = player.get('FG3A', 0)
        made_free_throws = player.get('FTM', 0)
        attempted_free_throws = player.get('FTA', 0)
        points_scored = player.get('PTS', 0)
        total_rebounds = player.get('REB', 0)
        assists = player.get('AST', 0)
        turnovers = player.get('TOV', 0)
        minutes_played = player.get('MIN', 1)
        
        field_goal_percentage = (made_field_goals / attempted_field_goals) * 100 if attempted_field_goals else 0
        true_shooting_attempts = attempted_field_goals + 0.44 * attempted_free_throws
        true_shooting_percentage = (points_scored / (2 * true_shooting_attempts)) * 100 if true_shooting_attempts else 0
        
        matchup = player.get('MATCHUP', 'N/A')
        opposing_team = matchup.split(' ')[-1] if matchup != 'N/A' else 'N/A'
        team = player.get('TEAM_ABBREVIATION', 'N/A')
        team_logo = TEAM_LOGOS.get(team, '')
        opposing_team_logo = TEAM_LOGOS.get(opposing_team, '')

        per = (points_scored + total_rebounds + assists - turnovers) / minutes_played * 15

        cleaned_player = {
            'name': player.get('PLAYER_NAME', 'N/A'),
            'team': team,
            'team_logo': team_logo,
            'opposing_team': opposing_team,
            'opposing_team_logo': opposing_team_logo,
            'points_scored': int(points_scored),
            'assists': int(assists),
            'rebounds': int(total_rebounds),
            'field_goal_percentage': field_goal_percentage,
            'true_shooting_percentage': true_shooting_percentage,
            'player_efficiency_rating': per
        }
        cleaned_data.append(cleaned_player)
    
    return cleaned_data
<<<<<<< HEAD
=======

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

    team_info_dict = {
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
            'score': f"{row['PTS']} - {row.get('PTS_OPP', 'N/A')}",
            'points': row['PTS'],
            'rebounds': row['REB'],
            'assists': row['AST'],
            'fg_percent': round(row['FG_PCT'] * 100, 2),
            'threep_percent': round(row['FG3_PCT'] * 100, 2),
            'ft_percent': round(row['FT_PCT'] * 100, 2)
        }
        recent_games.append(game_info)

    return team_info_dict, roster, recent_games
>>>>>>> Final updates for Fresh Finder project
