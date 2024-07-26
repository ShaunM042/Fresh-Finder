<<<<<<< HEAD
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

=======
# data_cleaning.py
>>>>>>> 2bfa62ba60d06db956d3d3953d8fea4124e72bd6
def clean_data(data, player_name='', versus_name=''):
    cleaned_data = []
    for item in data:
        if (player_name and player_name not in item.get("name", '').lower()) and (versus_name and versus_name not in item.get("team", '').lower()):
            continue
<<<<<<< HEAD
        team_logo = TEAM_LOGOS.get(item.get("team_for"), '')
        opposing_team_logo = TEAM_LOGOS.get(item.get("team_against"), '')
        cleaned_data.append({
            "name": item.get("name"),
            "team": item.get("team_for", 'N/A'),
            "team_logo": team_logo,
            "opposing_team": item.get("team_against", 'N/A'),
            "opposing_team_logo": opposing_team_logo,
            "points_scored": int(item.get("points_scored", 0)),
            "assists": int(item.get("assists", 0)),
            "rebounds": int(item.get("rebounds", 0)),
=======
        cleaned_data.append({
            "name": item.get("name"),
            "team": item.get("team"),
            "team_logo": item.get("team_logo"),
            "opposing_team": item.get("opposing_team"),
            "opposing_team_logo": item.get("opposing_team_logo"),
            "points_scored": item.get("points_scored", 0),
            "assists": item.get("assists", 0),
            "rebounds": item.get("rebounds", 0),
>>>>>>> 2bfa62ba60d06db956d3d3953d8fea4124e72bd6
            "field_goal_percentage": item.get("field_goal_percentage", 0.0),
            "true_shooting_percentage": item.get("true_shooting_percentage", 0.0),
            "player_efficiency_rating": item.get("player_efficiency_rating", 0.0)
        })
    return cleaned_data
