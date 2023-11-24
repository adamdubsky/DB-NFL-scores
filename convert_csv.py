#PANDAS AND SQLALCHEMY
import pandas as pd
from sqlalchemy import create_engine


#DATABASE FILE
db_path = 'database.db'

#SQL ENGINE
engine = create_engine(f'sqlite:///{db_path}')

#DATAFRAME SKELETONS
df1 = pd.read_csv('data_csv/nfl_stadiums.csv')
df2 = pd.read_csv('data_csv/nfl_teams.csv')
df3 = pd.read_csv('data_csv/spreadspoke_scores.csv')

# Convert DataFrames to SQL tables
df1.to_sql('Stadiums', engine, index=False, if_exists='replace')
df2.to_sql('Teams', engine, index=False, if_exists='replace')
df3.to_sql('Results', engine, index=False, if_exists='replace')