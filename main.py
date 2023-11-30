import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

#STREAMLIT TITLES
st.title("NFL Data visualization")
st.sidebar.title("Select features to display")

#INITIALLY BRING FULL DATABASE INTO PROGRAM THROUGH PANDAS
conn = sqlite3.connect("database.db")

sql_query = "SELECT * FROM STADIUMS"
df_stadiums = pd.read_sql(sql_query, conn)

sql_query = "SELECT * FROM TEAMS"
df_teams = pd.read_sql(sql_query, conn)

sql_query = "SELECT * FROM RESULTS"
df_results = pd.read_sql(sql_query, conn)

#SELECT TEAM
team = st.sidebar.selectbox('Select a team', df_teams['team_id'].drop_duplicates())
selected_team_name = df_teams[df_teams['team_id'] == team]['team_name'].iloc[0]

#SELECT HOST
host = st.sidebar.selectbox('Select where team is playng', ['Home', 'Away', 'Both'])

#SELECT STADIUM TYPE
stadium_type = st.sidebar.selectbox('Select a stadium type', df_stadiums['stadium_type'].dropna().unique())

#SELECT STADIUM SURFACE
stadium_surface = st.sidebar.selectbox('Select a stadium surface', df_stadiums['stadium_surface'].dropna().unique())

#STADIUM CAPACITIES SLIDER
stadium_capacities = sorted(list(df_stadiums['stadium_capacity'].dropna()))
stadium_capacities = [int(s.replace(',', '')) for s in stadium_capacities]
stadium_capacity = st.sidebar.slider('Select a stadium capacity range', stadium_capacities[0], 
                                     stadium_capacities[len(stadium_capacities)-1], 
                                     (stadium_capacities[int(len(stadium_capacities)*0.25)], 
                                      stadium_capacities[int(len(stadium_capacities)*0.75)]))

#WEATHER TEMPERATURE SLIDER
weather_temps = sorted(list(df_results['weather_temperature'].dropna()))
temperature = st.sidebar.slider('Select a temperature range in degrees fahrenheit', weather_temps[0], 
                                     weather_temps[len(weather_temps)-1], 
                                     (weather_temps[int(len(weather_temps)*0.25)], 
                                      weather_temps[int(len(weather_temps)*0.75)]), step=1.0)

#WEATHER WIND SLIDER
wind_speeds = sorted(list(df_results['weather_wind_mph'].dropna()))
wind_speed = st.sidebar.slider('Select a wind speed range in mph', wind_speeds[0], 
                                     wind_speeds[len(wind_speeds)-1], 
                                     (wind_speeds[int(len(wind_speeds)*0.25)], 
                                      wind_speeds[int(len(wind_speeds)*0.75)]), step=1.0)

#WEATHER HUMIDITY
weather_humidity = sorted(list(df_results['weather_humidity'].dropna()))
humidity = st.sidebar.slider('Select a humidity range', weather_humidity[0], 
                                     weather_humidity[len(weather_humidity)-1], 
                                     (weather_humidity[int(len(weather_humidity)*0.25)], 
                                      weather_humidity[int(len(weather_humidity)*0.75)]), step=1.0)

#YEAR SLIDER
years = sorted(list(df_results['schedule_season'].dropna()))
year = st.sidebar.slider('Select a range of seasons', years[0], 
                                     years[len(years)-1], 
                                     (years[0], 
                                      years[len(years)-1]), step=1)

# THIS NEEDS TO BE DINAMICALLY DONE
# user can select a team id. A team id gets data from all possible variants of this team
# ex: WAS gets data from Washington Redskins, Washington Commanders etc.
# Team (and other data) should be passed according to user selection dinamically insetad of just arbitraly inputing the Falcons
# This should probably be easier to do in SQL than pandas, and this could be the whole SQL part of our project

#SELECT DATA TO BE DISPLAYED BY PLOTLY CHART
if host == 'Home':
    team_data = df_results[df_results['team_home'] == selected_team_name]
    team_data['Performance'] = team_data['score_home'] - team_data['score_away']
elif host == 'Away':
    team_data = df_results[df_results['team_away'] == selected_team_name]
    team_data['Performance'] = team_data['score_away'] - team_data['score_home']
elif host == 'Both':
    team_home = df_results[df_results['team_home'] == selected_team_name]
    team_home['Performance'] = team_home['score_home'] - team_home['score_away']
    team_away = df_results[df_results['team_away'] == selected_team_name]
    team_away['Performance'] = team_away['score_away'] - team_away['score_home']
    team_data = pd.concat([team_home, team_away], ignore_index=True)

#SORT BY DATE
team_data['schedule_date'] = pd.to_datetime(team_data['schedule_date'], format='%m/%d/%Y')
team_data['schedule_date'] = team_data['schedule_date'].dt.date 
team_data = team_data.sort_values(by='schedule_date')

#DISPLAY DATA
display_data = pd.DataFrame()
display_data['Date'] = team_data['schedule_date']
display_data['Performance'] = team_data['Performance']

fig = px.bar(display_data, x='Date', y='Performance')
st.plotly_chart(fig, use_container_width=True)

conn.close() #SHOULD BE LAST LINE OF THE PROGRAM, SO WE CAN MAKE DYNAMIC QUERYING