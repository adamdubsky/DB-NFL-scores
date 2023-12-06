import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import warnings
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
warnings.filterwarnings("ignore")

# STREAMLIT TITLES
st.title("NFL Data Visualization")
st.sidebar.title("Select Features to Display")

# CONNECT TO DATABASE
conn = sqlite3.connect("database.db")

# LOAD TEAMS DATA
df_teams = pd.read_sql("SELECT * FROM TEAMS", conn)
team = st.sidebar.selectbox('Select a Team', sorted(df_teams['team_id'].unique()))
selected_team_name = list(df_teams[df_teams['team_id'] == team]['team_name'])
st.subheader(selected_team_name[0])

# BEFORE LOADING STADIUMS DATA, FIXING ISSUE WITH DATA
cursor = conn.cursor()
update_query = """
UPDATE STADIUMS
SET stadium_capacity = 0
WHERE stadium_capacity IS NULL;
"""
# A LOT OF THE 'stadium_capacity' COLUMN WAS SET AS NULL, SO JUST CONSIDERED THIS AS 0
cursor.execute(update_query)
conn.commit()

# LOAD STADIUMS DATA AND HANDLE 'stadium_capacity'
df_stadiums = pd.read_sql("SELECT * FROM STADIUMS", conn)
df_stadiums['stadium_capacity'] = pd.to_numeric(df_stadiums['stadium_capacity'].str.replace(',', ''), errors='coerce').fillna(0).astype(int)
stadium_capacities = sorted(df_stadiums['stadium_capacity'].unique())
min_capacity = int(stadium_capacities[0])
max_capacity = int(stadium_capacities[-1]) if len(stadium_capacities) > 0 else 0

# SELECT HOST
host = st.sidebar.selectbox('Select where Team is Playing', ['Home', 'Away', 'Both'])

# SELECT STADIUM TYPE WITH 'ANY' OPTION
stadium_type_options = ['Any'] + list(df_stadiums['stadium_type'].dropna().unique())
stadium_type = st.sidebar.selectbox('Select a Stadium Type', stadium_type_options)

# SELECT STADIUM SURFACE WITH 'ANY' OPTION
stadium_surface_options = ['Any', 'Grass', 'FieldTurf']
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

if len(selected_team_name) > 1:
    if host == 'Home':
        where_conditions.append(f"team_home IN {tuple(selected_team_name)}")
    elif host == 'Away':
        where_conditions.append(f"team_away IN {tuple(selected_team_name)}")
    elif host == 'Both':
        team_condition = f"(team_home IN {tuple(selected_team_name)} OR team_away IN {tuple(selected_team_name)})"
        where_conditions.append(team_condition)
else:
    if host == 'Home':
        where_conditions.append(f"team_home = '{selected_team_name[0]}'")
    elif host == 'Away':
        where_conditions.append(f"team_away = '{selected_team_name[0]}'")
    elif host == 'Both':
        team_condition = f"(team_home = '{selected_team_name[0]}' OR team_away = '{selected_team_name[0]}')"
        where_conditions.append(team_condition)

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

try:
    season_stats['win_percentage'] = round((season_stats['win'] / season_stats[['win', 'loss']].sum(axis=1)) * 100, 1)
except KeyError:
    season_stats['win_percentage'] = 0

columns_to_select = ['win_percentage', 'win', 'loss', 'tie'] if 'tie' in season_stats.columns else ['win_percentage', 'win', 'loss']
df_season = season_stats[columns_to_select].reset_index()
df_season.columns = ['Season', 'Win Percentage', 'Win', 'Loss', 'Tie'] if 'tie' in season_stats.columns else ['Season', 'Win Percentage', 'Win', 'Loss']

# SEASON PERFORMANCE LINE CHART
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_season['Season'], y=df_season['Win Percentage'], mode='lines+markers', name='Win Percentage'))
fig.update_layout(title_text='Season by Season Win %')
st.plotly_chart(fig, use_container_width=True)

# SEASON PERFORMANCE BAR CHART
fig = px.bar(df_season, x='Season', y=['Win', 'Loss', 'Tie'] if 'tie' in season_stats.columns else ['Win', 'Loss'], 
             title='Season by Season Win/Loss/Tie')
st.plotly_chart(fig, use_container_width=True)

# DISPLAY DATAFRAME
st.divider()
st.write("Dataframe with Season by Season stats for user manipulation")
st.dataframe(season_stats)
st.divider()

# SELECT OPPONENT FOR REGRESSION ANALYSIS
st.subheader("Estimate the outcome of a game given user inputs")

opponent_options = []
for opponent in list(df_teams['team_id']):
    if opponent != team:
        opponent_options.append(opponent)
opponent = st.selectbox('Select an Opponent', sorted(set(opponent_options)))
selected_opponent = list(df_teams[df_teams['team_id'] == opponent]['team_name'])

#RERUN QUERY WITH ADDITION OF SELECTED OPPONENT
if len(selected_opponent) > 1:
    opponent_condition = f"(team_home IN {tuple(selected_opponent)} OR team_away IN {tuple(selected_opponent)})"
else:
    opponent_condition = f"(team_home = '{selected_opponent[0]}' OR team_away = '{selected_opponent[0]}')"
where_conditions.append(opponent_condition)

where_clause = " AND ".join(where_conditions)

sql_query = f"""
SELECT R.*, S.stadium_type, S.stadium_surface, S.stadium_capacity 
FROM RESULTS R
LEFT JOIN STADIUMS S ON R.stadium = S.stadium_name
WHERE {where_clause};
"""

##############REGRESSION ANALYSIS##############

#TREAT DATA
team_data = pd.read_sql(sql_query, conn)
team_data['Performance'] = team_data.apply(lambda row: row['score_home'] - row['score_away'] 
                                           if row['team_home'] == selected_team_name 
                                           else row['score_away'] - row['score_home'], axis=1)
team_data['stadium_capacity'] = pd.to_numeric(team_data['stadium_capacity'].str.replace(',', ''), errors='coerce').fillna(0).astype(int)

#SELEC USER INPUT FEATURES
regression_columns = ['weather_temperature', 'weather_wind_mph', 'stadium_capacity', 'stadium_type', 'stadium_surface', 'Performance']
df_regression = team_data[regression_columns].copy()

#TARGET PERFORMANCE
X = df_regression.drop('Performance', axis=1)
y = df_regression['Performance']
try:
    #SPLIT TRAIN/TEST DATA
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=0)

    #SPLIT NUMERICAL AND CATEGORIC FEATURES
    numeric_features = ['weather_temperature', 'weather_wind_mph', 'stadium_capacity']
    categorical_features = ['stadium_type', 'stadium_surface']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features),
            ('cat', OneHotEncoder(), categorical_features)
        ])

    #APPLY REGRESSION MODEL
    model = LinearRegression()

    pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                ('model', model)])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    historic_prediction = round(sum(y_pred)/len(y_pred),2)

    if historic_prediction > 0:
        st.write(f"With the user inputed data, it is estimated that the {selected_team_name[0]}, in the given conditions would beat the {selected_opponent[0]} by {historic_prediction} points.")
    else:
        st.write(f"With the user inputed data, it is estimated that the {selected_team_name[0]}, in the given conditions would lose to the {selected_opponent[0]} by {np.abs(historic_prediction)} points.")
except ValueError:
    st.write("With the inputed values, we don't have enough data to perform a prediction. We apologize for the limitations of our model.")

conn.close()