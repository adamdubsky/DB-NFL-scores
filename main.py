import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3

# STREAMLIT TITLES
st.title("NFL Data Visualization")
st.sidebar.title("Select Features to Display")

# CONNECT TO DATABASE
conn = sqlite3.connect("database.db")

# LOAD TEAMS DATA
df_teams = pd.read_sql("SELECT * FROM TEAMS", conn)
team = st.sidebar.selectbox('Select a Team', sorted(df_teams['team_id'].unique()))
selected_team_name = df_teams[df_teams['team_id'] == team]['team_name'].iloc[0]
st.subheader(selected_team_name)

# LOAD STADIUMS DATA AND HANDLE 'stadium_capacity'
df_stadiums = pd.read_sql("SELECT * FROM STADIUMS", conn)
df_stadiums['stadium_capacity'] = pd.to_numeric(df_stadiums['stadium_capacity'].fillna(0), errors='coerce').fillna(0).astype(int)
stadium_capacities = sorted(df_stadiums['stadium_capacity'].unique())
min_capacity = int(stadium_capacities[0])
max_capacity = int(stadium_capacities[-1]) if len(stadium_capacities) > 0 else 0

# SELECT HOST
host = st.sidebar.selectbox('Select where Team is Playing', ['Home', 'Away', 'Both'])

# SELECT STADIUM TYPE WITH 'ANY' OPTION
stadium_type_options = ['Any'] + list(df_stadiums['stadium_type'].dropna().unique())
stadium_type = st.sidebar.selectbox('Select a Stadium Type', stadium_type_options)

# SELECT STADIUM SURFACE WITH 'ANY' OPTION
stadium_surface_options = ['Any'] + list(df_stadiums['stadium_surface'].dropna().unique())
stadium_surface = st.sidebar.selectbox('Select a Stadium Surface', stadium_surface_options)

# STADIUM CAPACITIES SLIDER
stadium_capacity = st.sidebar.slider('Select a Stadium Capacity Range', min_value=min_capacity, 
                                     max_value=max_capacity, value=(min_capacity, max_capacity))

# WEATHER TEMPERATURE SLIDER
df_results = pd.read_sql("SELECT * FROM RESULTS", conn)
weather_temps = sorted(df_results['weather_temperature'].dropna().unique())
temperature = st.sidebar.slider('Select a Temperature Range in Fahrenheit', min_value=int(weather_temps[0]), 
                                max_value=int(weather_temps[-1]), value=(int(weather_temps[0]), int(weather_temps[-1])), step=1)

# WEATHER WIND SLIDER
wind_speeds = sorted(df_results['weather_wind_mph'].dropna().unique())
wind_speed = st.sidebar.slider('Select a Wind Speed Range in MPH', min_value=int(wind_speeds[0]), 
                               max_value=int(wind_speeds[-1]), value=(int(wind_speeds[0]), int(wind_speeds[-1])), step=1)

# YEAR SLIDER
years = sorted([1966, 2018])
year = st.sidebar.slider('Select a Range of Seasons', min_value=int(years[0]), 
                         max_value=int(years[-1]), value=(int(years[0]), int(years[-1])), step=1)

# PREPARE SQL QUERY BASED ON USER SELECTION
where_conditions = []
if host == 'Home':
    where_conditions.append(f"team_home = '{selected_team_name}'")
elif host == 'Away':
    where_conditions.append(f"team_away = '{selected_team_name}'")
elif host == 'Both':
    where_conditions.append(f"(team_home = '{selected_team_name}' OR team_away = '{selected_team_name}')")

if stadium_type != 'Any':
    where_conditions.append(f"stadium_type = '{stadium_type}'")
if stadium_surface != 'Any':
    where_conditions.append(f"stadium_surface = '{stadium_surface}'")

where_conditions.append(f"stadium_capacity BETWEEN {stadium_capacity[0]} AND {stadium_capacity[1]}")
where_conditions.append(f"weather_temperature BETWEEN {temperature[0]} AND {temperature[1]}")
where_conditions.append(f"weather_wind_mph BETWEEN {wind_speed[0]} AND {wind_speed[1]}")
where_conditions.append(f"schedule_season BETWEEN {year[0]} AND {year[1]}")

where_clause = " AND ".join(where_conditions)

# JOIN RESULTS WITH STADIUMS AND APPLY FILTERS
sql_query = f"""
SELECT R.*, S.stadium_type, S.stadium_surface, S.stadium_capacity 
FROM RESULTS R
LEFT JOIN STADIUMS S ON R.stadium = S.stadium_name
WHERE {where_clause};
"""
team_data = pd.read_sql(sql_query, conn)

# GAME BY GAME PERFORMANCE DISPLAY
team_data['Performance'] = team_data.apply(lambda row: row['score_home'] - row['score_away'] 
                                           if row['team_home'] == selected_team_name 
                                           else row['score_away'] - row['score_home'], axis=1)
team_data['game_result'] = team_data['Performance'].apply(lambda x: 'win' 
                                                          if x > 0 
                                                          else ('tie' if x == 0 else 'loss'))

team_data['schedule_date'] = pd.to_datetime(team_data['schedule_date'], format='%m/%d/%Y')
team_data['schedule_date'] = team_data['schedule_date'].dt.date 
team_data = team_data.sort_values(by='schedule_date')

fig = px.bar(team_data, x='schedule_date', y='Performance', title='Game by Game Performance')
st.plotly_chart(fig, use_container_width=True)

# SEASON BY SEASON PERFORMANCE DISPLAY
season_stats = team_data.groupby('schedule_season')['game_result'].value_counts().unstack(fill_value=0)
season_stats['win_percentage'] = round((season_stats['win'] / season_stats[['win', 'loss']].sum(axis=1)) * 100, 2)

columns_to_select = ['win_percentage', 'win', 'loss', 'tie'] if 'tie' in season_stats.columns else ['win_percentage', 'win', 'loss']
df_season = season_stats[columns_to_select].reset_index()
df_season.columns = ['Season', 'Win Percentage', 'Win', 'Loss', 'Tie'] if 'tie' in season_stats.columns else ['Season', 'Win Percentage', 'Win', 'Loss']

# SEASON PERFORMANCE LINE CHART
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_season['Season'], y=df_season['Win Percentage'], mode='lines+markers', name='Win Percentage'))
st.plotly_chart(fig, use_container_width=True)

# SEASON PERFORMANCE BAR CHART
fig = px.bar(df_season, x='Season', y=['Win', 'Loss', 'Tie'] if 'tie' in season_stats.columns else ['Win', 'Loss'], 
             title='Season by Season Win/Loss/Tie')
st.plotly_chart(fig, use_container_width=True)

# DISPLAY DATAFRAME
st.dataframe(season_stats)

conn.close()
