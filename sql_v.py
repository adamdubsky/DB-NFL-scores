import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

# STREAMLIT TITLES
st.title("NFL Data Visualization")
st.sidebar.title("Select Features to Display")

# Initialize a connection to the SQLite database
conn = sqlite3.connect("database.db")

# SELECT TEAM
team_query = "SELECT DISTINCT team_id FROM TEAMS"
df_teams = pd.read_sql(team_query, conn)
team = st.sidebar.selectbox('Select a team', df_teams['team_id'])
selected_team_name = pd.read_sql(f"SELECT team_name FROM TEAMS WHERE team_id = '{team}'", conn)['team_name'].iloc[0]

# SELECT HOST
host = st.sidebar.selectbox('Select where team is playing', ['Home', 'Away', 'Both'])

# SELECT STADIUM TYPE WITH 'ANY' OPTION
stadium_type_query = "SELECT DISTINCT stadium_type FROM STADIUMS WHERE stadium_type IS NOT NULL"
stadium_type_options = ['Any'] + pd.read_sql(stadium_type_query, conn)['stadium_type'].tolist()
stadium_type = st.sidebar.selectbox('Select a stadium type', stadium_type_options)

# SELECT STADIUM SURFACE WITH 'ANY' OPTION
stadium_surface_query = "SELECT DISTINCT stadium_surface FROM STADIUMS WHERE stadium_surface IS NOT NULL"
stadium_surface_options = ['Any'] + pd.read_sql(stadium_surface_query, conn)['stadium_surface'].tolist()
stadium_surface = st.sidebar.selectbox('Select a stadium surface', stadium_surface_options)


# STADIUM CAPACITIES SLIDER
# Query to fetch and convert stadium capacities to integer after removing commas
stadium_capacities_query = """
SELECT DISTINCT 
    CAST(REPLACE(stadium_capacity, ',', '') AS INTEGER) AS stadium_capacity
FROM STADIUMS 
WHERE stadium_capacity IS NOT NULL 
ORDER BY CAST(REPLACE(stadium_capacity, ',', '') AS INTEGER)
"""
stadium_capacities = pd.read_sql(stadium_capacities_query, conn)['stadium_capacity']
stadium_capacity = st.sidebar.slider('Select a stadium capacity range', 
                                     min_value=int(stadium_capacities.min()), 
                                     max_value=int(stadium_capacities.max()), 
                                     value=(int(stadium_capacities.quantile(0.25)), 
                                            int(stadium_capacities.quantile(0.75))),
                                     step=1)  # Set step as an integer


# WEATHER TEMPERATURE SLIDER
weather_temps_query = "SELECT DISTINCT weather_temperature FROM RESULTS WHERE weather_temperature IS NOT NULL ORDER BY weather_temperature"
weather_temps = pd.read_sql(weather_temps_query, conn)['weather_temperature']
temperature = st.sidebar.slider('Select a temperature range in degrees Fahrenheit', min_value=int(weather_temps.min()), 
                                     max_value=int(weather_temps.max()), 
                                     value=(int(weather_temps.quantile(0.25)), 
                                            int(weather_temps.quantile(0.75))), step=1)

# WEATHER WIND SLIDER
wind_speeds_query = "SELECT DISTINCT weather_wind_mph FROM RESULTS WHERE weather_wind_mph IS NOT NULL ORDER BY weather_wind_mph"
wind_speeds = pd.read_sql(wind_speeds_query, conn)['weather_wind_mph']
wind_speed = st.sidebar.slider('Select a wind speed range in mph', min_value=int(wind_speeds.min()), 
                                     max_value=int(wind_speeds.max()), 
                                     value=(int(wind_speeds.quantile(0.25)), 
                                            int(wind_speeds.quantile(0.75))), step=1)

# WEATHER HUMIDITY SLIDER
weather_humidity_query = "SELECT DISTINCT weather_humidity FROM RESULTS WHERE weather_humidity IS NOT NULL ORDER BY weather_humidity"
weather_humidity = pd.read_sql(weather_humidity_query, conn)['weather_humidity']
humidity = st.sidebar.slider('Select a humidity range', min_value=int(weather_humidity.min()), 
                                     max_value=int(weather_humidity.max()), 
                                     value=(int(weather_humidity.quantile(0.25)), 
                                            int(weather_humidity.quantile(0.75))), step=1)

# YEAR SLIDER
years_query = "SELECT DISTINCT schedule_season FROM RESULTS WHERE schedule_season IS NOT NULL ORDER BY schedule_season"
years = pd.read_sql(years_query, conn)['schedule_season']
year = st.sidebar.slider('Select a range of seasons', min_value=int(years.min()), 
                                     max_value=int(years.max()), 
                                     value=(int(years.min()), 
                                            int(years.max())), step=1)

# CONSTRUCT DYNAMIC QUERY FOR RESULTS
results_query = f"""
SELECT r.*, s.stadium_capacity, s.stadium_type, s.stadium_surface
FROM RESULTS r
JOIN STADIUMS s ON r.stadium = s.stadium_name
WHERE ((r.team_home = '{selected_team_name}' AND '{host}' IN ('Home', 'Both')) OR
       (r.team_away = '{selected_team_name}' AND '{host}' IN ('Away', 'Both')))
AND ('{stadium_type}' = 'Any' OR s.stadium_type = '{stadium_type}')
AND ('{stadium_surface}' = 'Any' OR s.stadium_surface = '{stadium_surface}')
AND s.stadium_capacity BETWEEN {stadium_capacity[0]} AND {stadium_capacity[1]}
AND r.weather_temperature BETWEEN {temperature[0]} AND {temperature[1]}
AND r.weather_wind_mph BETWEEN {wind_speed[0]} AND {wind_speed[1]}
AND r.weather_humidity BETWEEN {humidity[0]} AND {humidity[1]}
AND r.schedule_season BETWEEN {year[0]} AND {year[1]}
"""

team_data = pd.read_sql(results_query, conn)
team_data['Performance'] = team_data.apply(lambda row: row['score_home'] - row['score_away'] if row['team_home'] == selected_team_name else row['score_away'] - row['score_home'], axis=1)

# SORT BY DATE
team_data['schedule_date'] = pd.to_datetime(team_data['schedule_date'], format='%m/%d/%Y').dt.date
team_data = team_data.sort_values(by='schedule_date')

# DISPLAY DATA
display_data = pd.DataFrame()
display_data['Date'] = team_data['schedule_date']
display_data['Performance'] = team_data['Performance']

fig = px.bar(display_data, x='Date', y='Performance')
st.plotly_chart(fig, use_container_width=True)

conn.close()