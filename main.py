import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3

# STREAMLIT TITLES
st.title("NFL Data visualization")
st.sidebar.title("Select features to display")

# INITIALLY BRING FULL DATABASE INTO PROGRAM THROUGH PANDAS
conn = sqlite3.connect("database.db")

sql_query = "SELECT * FROM STADIUMS"
df_stadiums = pd.read_sql(sql_query, conn)

# Handle non-numeric values and None in stadium_capacity
df_stadiums['stadium_capacity'] = pd.to_numeric(df_stadiums['stadium_capacity'].str.replace(',', ''), errors='coerce').fillna(0).astype(int)

sql_query = "SELECT * FROM TEAMS"
df_teams = pd.read_sql(sql_query, conn)

sql_query = "SELECT * FROM RESULTS"
df_results = pd.read_sql(sql_query, conn)

#SELECT TEAM
team = st.sidebar.selectbox('Select a team', sorted(list(df_teams['team_id'].drop_duplicates())))
selected_team_name = list(df_teams[df_teams['team_id'] == team]['team_name'])
st.subheader(selected_team_name[0])

# SELECT HOST
host = st.sidebar.selectbox('Select where team is playing', ['Home', 'Away', 'Both'])

# SELECT STADIUM TYPE WITH 'ANY' OPTION
stadium_type_options = ['Any'] + list(df_stadiums['stadium_type'].dropna().unique())
stadium_type = st.sidebar.selectbox('Select a stadium type', stadium_type_options)

# SELECT STADIUM SURFACE WITH 'ANY' OPTION
stadium_surface_options = ['Any'] + list(df_stadiums['stadium_surface'].dropna().unique())
stadium_surface = st.sidebar.selectbox('Select a stadium surface', stadium_surface_options)

# STADIUM CAPACITIES SLIDER
stadium_capacities = sorted(df_stadiums['stadium_capacity'].unique())
stadium_capacity = st.sidebar.slider('Select a stadium capacity range', min_value=int(stadium_capacities[0]), 
                                     max_value=int(stadium_capacities[-1]), 
                                     value=(int(stadium_capacities[int(len(stadium_capacities)*0.10)]), 
                                            int(stadium_capacities[int(len(stadium_capacities)*0.90)])))

# WEATHER TEMPERATURE SLIDER
weather_temps = sorted(df_results['weather_temperature'].dropna().unique())
temperature = st.sidebar.slider('Select a temperature range in degrees fahrenheit', min_value=int(weather_temps[0]), 
                                     max_value=int(weather_temps[-1]), 
                                     value=(int(weather_temps[int(len(weather_temps)*0.10)]), 
                                            int(weather_temps[int(len(weather_temps)*0.90)])), step=1)

# WEATHER WIND SLIDER
wind_speeds = sorted(df_results['weather_wind_mph'].dropna().unique())
wind_speed = st.sidebar.slider('Select a wind speed range in mph', min_value=int(wind_speeds[0]), 
                                     max_value=int(wind_speeds[-1]), 
                                     value=(int(wind_speeds[int(len(wind_speeds)*0.10)]), 
                                            int(wind_speeds[int(len(wind_speeds)*0.90)])), step=1)

# YEAR SLIDER
years = sorted([1966,2018])
year = st.sidebar.slider('Select a range of seasons', min_value=int(years[0]), 
                                     max_value=int(years[-1]), 
                                     value=(int(years[0]), 
                                            int(years[-1])), step=1)

#SELECT HOME/AWAY
if host == 'Home':
    team_data = df_results[df_results['team_home'].isin(selected_team_name)]
elif host == 'Away':
    team_data = df_results[df_results['team_away'].isin(selected_team_name)]
elif host == 'Both':
    team_home = df_results[df_results['team_home'].isin(selected_team_name)]
    team_away = df_results[df_results['team_away'].isin(selected_team_name)]
    team_data = pd.concat([team_home, team_away], ignore_index=True)
    
# APPLY FILTERS
team_data = team_data.join(df_stadiums.set_index('stadium_name'), on='stadium')
team_data = team_data[
    ((stadium_type == 'Any') | (team_data['stadium_type'] == stadium_type)) &
    ((stadium_surface == 'Any') | (team_data['stadium_surface'] == stadium_surface)) &
    (team_data['stadium_capacity'].between(*stadium_capacity)) &
    (team_data['weather_temperature'].between(*temperature)) &
    (team_data['weather_wind_mph'].between(*wind_speed)) &
    (team_data['schedule_season'].between(*year))
]

#GAME BY GAME PERFORMANCE DISPLAY
team_data['Performance'] = team_data.apply(lambda row: row['score_home'] - row['score_away'] 
                                           if row['team_home'] in selected_team_name 
                                           else row['score_away'] - row['score_home'], axis=1)
team_data['game_result'] = team_data['Performance'].apply(lambda x: 'win' 
                                                          if x > 0 
                                                          else ('tie' if x == 0 else 'loss'))

team_data['schedule_date'] = pd.to_datetime(team_data['schedule_date'], format='%m/%d/%Y')
team_data['schedule_date'] = team_data['schedule_date'].dt.date 
team_data = team_data.sort_values(by='schedule_date')

fig = px.bar(team_data, x='schedule_date', y='Performance')

st.markdown("Game by game performance with given conditions")
st.plotly_chart(fig, use_container_width=True)

#SEASON BY SEASON PERFORMANCE DISPLAY

#CALCULATE SEASON PERFORMANCE
season_stats = team_data.groupby('schedule_season')['game_result'].value_counts().unstack(fill_value=0)
try:
    season_stats['win_percentage'] = round((season_stats['win'] / season_stats[['win', 'loss']].sum(axis=1)) * 100, 1)
except KeyError:
    season_stats['win_percentage'] = 0

columns_to_select = ['win_percentage', 'win', 'loss']
if 'tie' in season_stats.columns:
    columns_to_select.append('tie')

df_season = season_stats[columns_to_select].reset_index()
df_season.columns = ['Season', 'Win Percentage', 'Win', 'Loss', 'Tie'] if 'tie' in season_stats.columns else ['Season', 'Win Percentage', 'Win', 'Loss']


#FIRST DISPLAY
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_season['Season'], y=df_season['Win Percentage'],
                    mode='lines+markers',
                    name='lines+markers'))
st.markdown("Season by season win % with given conditions")
st.plotly_chart(fig, use_container_width=True)

#SECOND DISPLAY
st.markdown("Observe data inputted on chart")
st.dataframe(season_stats)

#THIRD DISPLAY
fig = px.bar(df_season, x="Season", y=["Win", "Loss"])
st.markdown("Season by season WIN/LOSS visualization")
st.plotly_chart(fig, use_container_width=True)

conn.close()  # SHOULD BE LAST LINE OF THE PROGRAM, SO WE CAN MAKE DYNAMIC QUERYING