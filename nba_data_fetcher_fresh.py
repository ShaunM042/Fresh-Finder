# nba_data_fetcher_fresh.py
from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType
import json
import time

TEAM_LOGOS = {
    "Atlanta Hawks": "https://content.sportslogos.net/logos/6/220/thumbs/2208192020.gif",
    "Boston Celtics": "https://content.sportslogos.net/logos/6/213/thumbs/slhg02hbef3j1ov4lsnwyol5o.gif",
    "Brooklyn Nets": "https://content.sportslogos.net/logos/6/3786/thumbs/hsuff5m3dgiv20kovde422r1f.gif",
    "Charlotte Hornets": "https://content.sportslogos.net/logos/6/5120/thumbs/512019262015.gif",
    "Chicago Bulls": "https://content.sportslogos.net/logos/6/221/thumbs/hj3gmh82w9hffmeh3fjm5h874.gif",
    "Cleveland Cavaliers": "https://content.sportslogos.net/logos/6/222/thumbs/22253692023.gif",
    "Dallas Mavericks": "https://content.sportslogos.net/logos/6/228/thumbs/22834632018.gif",
    "Denver Nuggets": "https://content.sportslogos.net/logos/6/229/thumbs/22989262019.gif",
    "Detroit Pistons": "https://content.sportslogos.net/logos/6/223/thumbs/22321642018.gif",
    "Golden State Warriors": "https://content.sportslogos.net/logos/6/235/thumbs/23531522020.gif",
    "Houston Rockets": "https://content.sportslogos.net/logos/6/230/thumbs/23068302020.gif",
    "Indiana Pacers": "https://content.sportslogos.net/logos/6/224/thumbs/22448122018.gif",
    "Los Angeles Clippers": "https://content.sportslogos.net/logos/6/236/thumbs/23655422025.gif",
    "Los Angeles Lakers": "https://content.sportslogos.net/logos/6/237/thumbs/23773242024.gif",
    "Memphis Grizzlies": "https://content.sportslogos.net/logos/6/231/thumbs/23143732019.gif",
    "Miami Heat": "https://content.sportslogos.net/logos/6/214/thumbs/burm5gh2wvjti3xhei5h16k8e.gif",
    "Milwaukee Bucks": "https://content.sportslogos.net/logos/6/225/thumbs/22582752016.gif",
    "Minnesota Timberwolves": "https://content.sportslogos.net/logos/6/232/thumbs/23296692018.gif",
    "New Orleans Pelicans": "https://content.sportslogos.net/logos/6/4962/thumbs/496292922024.gif",
    "New York Knicks": "https://content.sportslogos.net/logos/6/216/thumbs/21671702024.gif",
    "Oklahoma City Thunder": "https://content.sportslogos.net/logos/6/2687/thumbs/khmovcnezy06c3nm05ccn0oj2.gif",
    "Orlando Magic": "https://content.sportslogos.net/logos/6/217/thumbs/wd9ic7qafgfb0yxs7tem7n5g4.gif",
    "Philadelphia 76ers": "https://content.sportslogos.net/logos/6/218/thumbs/21870342016.gif",
    "Phoenix Suns": "https://content.sportslogos.net/logos/6/238/thumbs/23843702014.gif",
    "Portland Trail Blazers": "https://content.sportslogos.net/logos/6/239/thumbs/23997252018.gif",
    "Sacramento Kings": "https://content.sportslogos.net/logos/6/240/thumbs/24040432017.gif",
    "San Antonio Spurs": "https://content.sportslogos.net/logos/6/233/thumbs/23325472018.gif",
    "Toronto Raptors": "https://content.sportslogos.net/logos/6/227/thumbs/22770242021.gif",
    "Utah Jazz": "https://content.sportslogos.net/logos/6/234/thumbs/23485132023.gif",
    "Washington Wizards": "https://content.sportslogos.net/logos/6/219/thumbs/21956712016.gif",
}

def fetch_nba_data(day, month, year):
    time.sleep(1)
    player_box_scores = client.player_box_scores(day=day, month=month, year=year, output_type=OutputType.JSON)
    data = json.loads(player_box_scores)

    cleaned_data = []
    for player in data:
        made_field_goals = player.get('made_field_goals', 0)
        attempted_field_goals = player.get('attempted_field_goals', 0)
        made_three_point_field_goals = player.get('made_three_point_field_goals', 0)
        attempted_three_point_field_goals = player.get('attempted_three_point_field_goals', 0)
        made_free_throws = player.get('made_free_throws', 0)
        attempted_free_throws = player.get('attempted_free_throws', 0)
        points_scored = (made_field_goals - made_three_point_field_goals) * 2 + made_three_point_field_goals * 3 + made_free_throws
        total_rebounds = player.get('defensive_rebounds', 0) + player.get('offensive_rebounds', 0)
        assists = player.get('assists', 0)
        turnovers = player.get('turnovers', 0)
        minutes_played = player.get('minutes_played', 1)
        
        field_goal_percentage = (made_field_goals / attempted_field_goals) * 100 if attempted_field_goals else 0
        true_shooting_attempts = attempted_field_goals + 0.44 * attempted_free_throws
        true_shooting_percentage = (points_scored / (2 * true_shooting_attempts)) * 100 if true_shooting_attempts else 0
        
        opposing_team = player.get('opponent', 'N/A')
        team_logo = TEAM_LOGOS.get(player.get('team'), '')
        opposing_team_logo = TEAM_LOGOS.get(opposing_team, '')

        per = (points_scored + total_rebounds + assists - turnovers) / minutes_played * 15

        cleaned_player = {
            'name': player.get('name'),
            'team': player.get('team'),
            'team_logo': team_logo,
            'opposing_team': opposing_team,
            'opposing_team_logo': opposing_team_logo,
            'points_scored': points_scored,
            'assists': assists,
            'rebounds': total_rebounds,
            'field_goal_percentage': field_goal_percentage,
            'true_shooting_percentage': true_shooting_percentage,
            'player_efficiency_rating': per
        }
        cleaned_data.append(cleaned_player)
    
    return cleaned_data
