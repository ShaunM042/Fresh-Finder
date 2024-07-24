# app.py
from flask import Flask, jsonify, render_template, request
import nba_data_fetcher_fresh
import data_cleaning
import time
from datetime import datetime, timedelta

app = Flask(__name__)

# Simple in-memory cache
cache = {}
cache_expiry = 60 * 60  # Cache expiry time in seconds (e.g., 1 hour)

@app.route('/data', methods=['POST'])
def get_data():
    try:
        start_date = request.json.get('start_date')
        end_date = request.json.get('end_date')
        player_name = request.json.get('player_name', '').lower()
        
        if not start_date or not end_date:
            return jsonify({"error": "Start date and/or end date not provided"}), 400

        # Generate date range
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_date_obj - start_date_obj

        all_data = []

        for i in range(delta.days + 1):
            date = start_date_obj + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            # Check if data is in cache and not expired
            if date_str in cache and time.time() - cache[date_str]['timestamp'] < cache_expiry:
                daily_data = cache[date_str]['data']
            else:
                data = nba_data_fetcher_fresh.fetch_nba_data(date.day, date.month, date.year)
                if not data:
                    continue
                daily_data = data_cleaning.clean_data(data, player_name)
                # Store data in cache
                cache[date_str] = {
                    'data': daily_data,
                    'timestamp': time.time()
                }
            
            all_data.extend(daily_data)

        return jsonify(all_data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
