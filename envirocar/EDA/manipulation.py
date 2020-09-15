import pandas as pd
import geopandas as gpd
from scipy import stats
import numpy as np
import math

# class Manipulation():
#     def __init__(self):
#         print("Initializing class 'Manipulation'")  
 
def drop_unit_columns(df):
    units = df.filter(like='.unit').columns
    units.tolist()
    df.drop(units, axis=1, inplace=True)
    print('Dropped unit columns: ', units)
    return df


def add_column_datetime(df):
    df['datetime'] = pd.to_datetime(df['time'])
    return df

def add_coordinate_columns(df):
    df['lat'] = df['geometry'].apply(lambda coord: coord.y)
    df['lng'] = df['geometry'].apply(lambda coord: coord.x)
    return df

def normalize(df):
    columnList=df.select_dtypes(['float64']).columns.tolist()
    for variable in columnList:
        df[variable]=df.groupby('track.id')[variable].transform(lambda x:(x-x.min())/(x.max()-x.min()))
    return df

def standardize(df):
    columnList=df.select_dtypes(['float64']).columns.tolist()
    for variable in columnList:
        df[variable]=df.groupby('track.id')[variable].transform(lambda x:(x - x.mean()) / x.std())
    return df

def get_dummies_sensor(df):
    sensor = df.filter(like='sensor.', axis=1).columns.copy()
    sensorList = sensor.tolist()
    newDF = pd.get_dummies(df, columns=sensorList)
    return newDF
    
def interpolate_nearest(df):
    columnList=df.select_dtypes(['float64']).columns.tolist()
    for variable in columnList:
        variableName=variable
        #TODO!!! .groupby('track.id')--> not provided for groups in Geopandas
        df[variableName]=df[variable]\
        .interpolate(method='nearest', limit_direction="both", axis=0)\
        .ffill()\
        .bfill()
    return df

def get_numerical(df):
    numericalDF=df.select_dtypes(['float64']).copy()
    return numericalDF
    
def squareRoot_transformation(df, column):
    squareRoot=df[column]**(.5)
    print(squareRoot.describe())
    return squareRoot

    
def reciprocal_transformation(df, column):
    reciprocal=1/(df[column]+1)
    print(reciprocal.describe())
    return reciprocal

def log_transformation(df, column):
    log = np.log(df[column]+1)
    print(log.describe())
    return log