import requests
import pandas as pd
import json
import os
from datetime import datetime
import streamlit as st

def update_data():
    """Update combined.csv with latest NBA performance data"""
    # Try to get API key from Streamlit secrets first, then environment variables
    try:
        API_KEY = st.secrets["NBA_API_KEY"]
    except:
        API_KEY = os.getenv('NBA_API_KEY')
    
    if not API_KEY:
        raise ValueError("NBA_API_KEY not found in secrets or environment variables")
    
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    
    query = "https://api3.natst.at/971b-24e421/playerperfs/NBA/2025"
    rs = requests.get(query, headers=headers)
    
    if not rs.ok:
        print(f"Error fetching data: {rs.status_code}")
        return
    
    df = parse_performance_json(rs.json())
    
    # Load and update existing data
    combined = pd.read_csv('combined.csv')
    total = pd.concat([df, combined])
    total = total.drop_duplicates(subset=['Player', 'GameDay', 'Team'])
    
    # Save updated data
    total.to_csv('combined.csv', index=False)
    
    # Save last update timestamp
    with open('.last_update', 'w') as f:
        f.write(datetime.now().isoformat())

def should_update():
    """Check if data should be updated based on last update timestamp"""
    try:
        with open('.last_update', 'r') as f:
            last_update = datetime.fromisoformat(f.read().strip())
            now = datetime.now()
            # Update if more than 24 hours have passed
            return (now - last_update).total_seconds() > 24 * 3600
    except FileNotFoundError:
        return True

def parse_performance_json(json_data):
    """Convert performance JSON data into a DataFrame matching combined.csv schema"""
    rows = []
    
    for perf_id, perf in json_data['performances'].items():
        # Extract game info
        game = perf['game']
        
        row = {
            'Player': perf['player'],
            'Team': perf['team']['name'],
            'GameDay': game['gameday'],
            'WinOrLoss': perf['game']['winorloss'],
            'PTS': int(perf['pts']),
            'REB': int(perf['reb']),
            'OREB' : int(perf['oreb']),
            'AST': int(perf['ast']),
            'STL': int(perf['stl']),
            'BLK': int(perf['blk']),
            'TO': int(perf['to']),
            'PF': int(perf['pf']),
            'FGA': int(perf['fga']),
            'FGM': int(perf['fgm']),
            '3FA': int(perf['threefa']),
            '3FM': int(perf['threefm']),
            'FTA': int(perf['fta']),
            'FTM': int(perf['ftm']),
            # Add Playoffs column based on game description if available
            'Playoffs': 'Y' if 'Playoffs' in game['description'] else None
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df

