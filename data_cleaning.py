# data_cleaning.py
def clean_data(data, player_name='', versus_name=''):
    cleaned_data = []
    for item in data:
        if (player_name and player_name not in item.get("name", '').lower()) and (versus_name and versus_name not in item.get("team", '').lower()):
            continue
        cleaned_data.append({
            "name": item.get("name"),
            "team": item.get("team"),
            "team_logo": item.get("team_logo"),
            "opposing_team": item.get("opposing_team"),
            "opposing_team_logo": item.get("opposing_team_logo"),
            "points_scored": item.get("points_scored", 0),
            "assists": item.get("assists", 0),
            "rebounds": item.get("rebounds", 0),
            "field_goal_percentage": item.get("field_goal_percentage", 0.0),
            "true_shooting_percentage": item.get("true_shooting_percentage", 0.0),
            "player_efficiency_rating": item.get("player_efficiency_rating", 0.0)
        })
    return cleaned_data
