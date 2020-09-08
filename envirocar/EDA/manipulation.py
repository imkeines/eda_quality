import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np
import math


class Manipulation():
    def __init__(self):
        print("Initializing class 'Manipulate'")  
        
 
    def drop_unit_columns(df):
        units = df.filter(like='.unit').columns
        units.tolist()
        df.drop(units, axis=1)#, inplace=True)
        return df
    
    
    def add_column_datetime(df):
        df['datetime'] = pd.to_datetime(df['time'])
        return df
    
    def add_coordinate_columns(df):
        df['lat'] = df['geometry'].apply(lambda coord: coord.y)
        df['lng'] = df['geometry'].apply(lambda coord: coord.x)
        return df
    
    def normalize(column):
        upper = column.max()
        lower = column.min()
        y = (column - lower)/(upper-lower)
        return y
    
