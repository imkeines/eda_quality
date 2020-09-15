import pandas as pd
import seaborn as sns
import numpy as np 
import matplotlib.pyplot as plt
import plotly.express as px
import geopandas as gpd
from scipy import stats

# class Inspection():
#     def __init__(self):
#         print("Initializing class 'Inspection'")  


def skewness_num_variables(df): # show_skewness_num_variables
    numericFeaturesIndex = df.dtypes[df.dtypes=='float64'].index
    skewedFeatures=df[numericFeaturesIndex].skew().sort_values(ascending=False)
    skewness=pd.DataFrame({'Skew':skewedFeatures})
    return skewness


def missing_values_per_variable(df, percent=100, dropCol=False): # sum_missing_values
    listCol =[]
    rowCount = df.shape[0]
    for column in df:
        sumColumn = df[column].isna().sum()
        percentNA = sumColumn/rowCount*100
        if percentNA <= percent:
            listCol.append({'column':column ,'missing_values': sumColumn, 'missing_values(%)': percentNA})
        else: 
            if dropCol == True:
                print('Column dropped: ', column, ', missing values(%): ', percentNA )
                df.drop([column], axis=1, inplace=True)
    listCol = pd.DataFrame(listCol).sort_values(by='missing_values', ascending=False).reset_index(drop=True)
    return listCol


def missing_values_per_track(df):
    columnList=df.select_dtypes(['float64']).columns.tolist()
    df_count=df.groupby('track.id').apply(lambda x: x.isna().sum()) 
    df_prop=df.groupby('track.id').apply(lambda x: x.isna().sum()/len(x)*100)
    return df_count, df_prop


def get_classified_correlations(df, method):
    allCoeffs=[]
    correlationsMatrixAll = df.corr(method=method)
    for column in correlationsMatrixAll:
        for i in correlationsMatrixAll[column].index:
            df = correlationsMatrixAll.at[i, column]
            if df < 1.0:
                allCoeffs.append({'column':column, 'index':i, 'coefficient':df })

    correlationsMatrix = correlationsMatrixAll.where(np.tril(np.ones(correlationsMatrixAll.shape)).astype(np.bool))

    very_strong=[]
    strong=[]
    moderate=[]
    weak=[]   
    for column in correlationsMatrix:
        for i in correlationsMatrix[column].index:
            df = correlationsMatrix.at[i, column]
            if df >= 0.8 and df < 1.0 or df <= -0.8 and df > -1.0:
                very_strong.append({'column':column, 'index':i, 'coefficient':df })#   
            if df >= 0.6 and df < 0.8 or df <= -0.6 and df > -0.8:
                strong.append({'column':column, 'index':i, 'coefficient':df })
            if df >= 0.4 and df < 0.6 or df <= -0.4 and df > -0.6:
                moderate.append({'column':column, 'index':i, 'coefficient':df })
            if df < 0.4 and df > -0.4:
                weak.append({'column':column, 'index':i, 'coefficient':df })

    very_strong = pd.DataFrame(very_strong).sort_values(by='coefficient', ascending=False).reset_index(drop=True)
    strong = pd.DataFrame(strong).sort_values(by='coefficient', ascending=False).reset_index(drop=True)
    moderate = pd.DataFrame(moderate).sort_values(by='coefficient', ascending=False).reset_index(drop=True)
    weak=pd.DataFrame(weak).sort_values(by='coefficient', ascending=False).reset_index(drop=True)
    allCoeffs= pd.DataFrame(allCoeffs).sort_values(by='coefficient', ascending=False).reset_index(drop=True)

    return allCoeffs, very_strong, strong, moderate, weak 


def get_correlation(df, method, variable1, variable2):
    allCoeffs=[]
    correlationsMatrixAll = df.corr(method=method)
    for column in correlationsMatrixAll:
        for i in correlationsMatrixAll[column].index:
            df = correlationsMatrixAll.at[i, column]
            if df < 1.0:
                allCoeffs.append({'v1':column, 'v2':i, 'coefficient':df })

    correlationsMatrix = correlationsMatrixAll.where(np.tril(np.ones(correlationsMatrixAll.shape)).astype(np.bool))
    allCoeffs= pd.DataFrame(allCoeffs).sort_values(by='coefficient', ascending=False).reset_index(drop=True)
    showCorr= allCoeffs.loc[(allCoeffs['v1'] == variable1) & (allCoeffs['v2'] == variable2)]
    return showCorr
    
    
def correlation_heatmap_triangle(df, method, figsize=(20, 16)):
    df = df.select_dtypes(['float64'])
    coefficient = df.corr(method=method)
    coefficient = coefficient.where(np.tril(np.ones(coefficient.shape)).astype(np.bool))
    plt.figure(figsize=figsize)
    sns.heatmap(coefficient, annot = True, vmin=-1, vmax=1.0, cmap="RdBu_r")


def get_single_track(df, track_id):
    grouped = df.groupby('track.id')
    df = grouped.get_group(track_id).copy()
    return df


def show_dublicated_tracks(df):   
    dublicates = df[df[['geometry', 'Engine Load.value', 'Calculated MAF.value',
    'Speed.value', 'CO2.value', 'Intake Pressure.value', 'Rpm.value',
    'Intake Temperature.value', 'Consumption (GPS-based).value',
    'GPS Altitude.value', 'Throttle Position.value', 'GPS Bearing.value',
    'Consumption.value', 'GPS Accuracy.value',
    'CO2 Emission (GPS-based).value', 'GPS Speed.value', 
    'track.length', 'track.begin', 'track.end', 'sensor.type',
    'sensor.engineDisplacement', 'sensor.model', 'sensor.id',
    'sensor.fuelType', 'sensor.constructionYear', 'sensor.manufacturer']].
     duplicated(keep=False)==True]['track.id'].unique().tolist()

    newdf= df.copy().loc[df['track.id'].isin(dublicates)]
    ls= newdf['track.id'].unique().tolist()
    print('Dublicated tracks:', ls)
    return newdf



def count_tracks(df):
    print(len(df['track.id'].unique().tolist()))

def show_units(df):
    '''
        Aim: 
            get an overview of the variables and corresponding units
        
        Keyword Arguments: 
            df {Geodataframe} -- point input
        
        Output: Matrix-like overview on variables an the relevant unit
    '''
    units = df.filter(like='.unit').columns
    for unit in units:
        if unit in df:
            print(df[unit].name, df[unit].iloc[0])
    return units
    
def get_units(df):
    '''
        Aim: 
            get an overview of the variables and corresponding units

        Keyword Arguments: 
            df {Geodataframe} -- point input

        Output: Matrix-like overview on variables an the relevant unit
    '''
    units = df.filter(like='.unit').columns
    unitList=[]
    for unit in units:
        if unit in df:
            unitList.append(unit)
            #print(df[unit].name, df[unit].iloc[0])
    return(unitList)


def get_categories(df):
    for column in df:
        print(column, df[column].unique())


def get_sensor_columns(df):
    sensor = df.filter(like='sensor.', axis=1).columns.copy()
    sensor = sensor.tolist()
    df = df[sensor]
    return df, sensor


def get_columns(df, name=''):
    columns =  df.filter(like=name, axis=1).columns.copy()
    columns = columns.tolist()
    df = df[columns]
    return columns, df


def plot_tracks(points_df, column):
    """ 
    Aim: 
        Visualize phenomena of tracks as timeserie in Linechart, in which each line represents one single track

    Keyword Arguments: 
        df {Geodataframe} -- point input

    Returns:
        Chart is shown 

    """
    # Add datetime to data frame
    points_df['datetime'] = pd.to_datetime(points_df['time'])
    points_df['index']=points_df.index
    fig = px.line(points_df, x="index", y=column, color="track.id",
                  line_group="track.id", hover_name="datetime")
    fig.update_traces(mode='lines+markers')
    fig.show()



def plot_point_values(points, value = None):
    """ This function is based on a function from the envirocar fork of the github user 'annaformaniuk'.

    Aim: 
        show points on a map

    Keyword Arguments:
        points {GeoDataFrame} -- points input
        value {string} -- column value to use for colouring

    Returns:
        No Return
    """

    points['lat'] = points['geometry'].apply(lambda coord: coord.y)
    points['lng'] = points['geometry'].apply(lambda coord: coord.x)

    if value is not None:
    # Visualizing points of the selected variable
        fig = px.scatter_mapbox(points, lat="lat", lon="lng", hover_data=["CO2.value"],
                                color=value,
                                color_continuous_scale=px.colors.sequential.Reds,
                                title=value + " visualisation", zoom=8,
                                hover_name="id")
    else:
        fig = px.scatter_mapbox(points, lat="lat", lon="lng", hover_data=["CO2.value"],
                                title= " Spatial distribution or requested tracks", zoom=8,
                                hover_name="id")


    fig.update_layout(mapbox_style="open-street-map",
                          margin={"r": 5, "t": 50, "l": 10, "b": 5})
    fig.show()
        

def plot_scatter(df, column1, column2, alpha=0.2):
    relation = df[['track.id',column1, column2]]
    relation.plot(kind='scatter', x = column1, y = column2, alpha=alpha )
    
    
    
def plot_normality_with_qqplot(point_df, column):
    '''
        Aim: 
            create q-q plot to inspect normality of distribution of selected variable

    Keyword Arguments: 
        df {Geodataframe} -- points input
        column {str} -- variable name

        Output: Q-Q plot
    '''
    plot = stats.probplot(point_df[column],  dist="norm", plot=plt, fit = False)
    plt.title(column)
    plt.show()
    
    

def plot_hist(df, column=''):
    if column !='':
        x = df[column]
    else:
        x = df
    sns.distplot(x)
    
    
def plot_linear_regression(variableName1, variableName2, title=''):
    sns.regplot(x=variableName1, y=variableName2).set_title(title)
    
    
def plot_distribution_s(points_df, column, column_gps = None):
    """ 
    Aim:
        Plot of two distributions in a single figure for visually comparing the shapes of the two distributions
    
    Keyword Arguments: 
        points {GeoDataFrame} -- the GeoDataFrame containing the measurements
        Column {str} -- the column name of measurement of interest,e.g. 'Speed.value'
        Column {str} -- the column name of measurement of same phenomena but measured based on GPS, e.g. 'GPS speed.value'
        
    Return:
        No Return, instead a plot is displayed
    """
    if column_gps is not None:
        sns.kdeplot(points_df[column], shade=True)
        sns.kdeplot(points_df[column_gps], shade=True)
    else:
        sns.kdeplot(points_df[column], shade=True)
    

