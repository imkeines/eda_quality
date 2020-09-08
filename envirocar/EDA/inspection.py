import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import plotly.express as px
import geopandas as gpd



class Inspection():
    def __init__(self):
        print("Initializing class 'Inspect'") 
        
    
    def show_skewness_num_variables(df):
        numericFeaturesIndex = df.dtypes[df.dtypes=='float64'].index
        skewedFeatures=df[numericFeaturesIndex].skew().sort_values(ascending=False)
        skewness=pd.DataFrame({'Skew':skewedFeatures})
        print(skewness)
        return skewness
    
    
    def sum_missing_values(df):
        listCol =[] 
        rowCount = df.shape[0]
        for column in df:
            sumColumn = df[column].isna().sum()
            percentNA = sumColumn/rowCount*100    
            if percentNA <= 80:
                listCol.append({'column':column ,'missing_values': sumColumn, 'missing_values(%)': percentNA})
        listCol = pd.DataFrame(listCol).sort_values(by='missing_values', ascending=False).reset_index(drop=True)
        return listCol
        
        
    def missing_values_per_track(df):
        columnList=df.select_dtypes(['float64']).columns.tolist()
        df_count=df.groupby('track.id').apply(lambda x: x.isna().sum()).head() 
        df_prop=df.groupby('track.id').apply(lambda x: x.isna().sum()/len(x)*100).head()
        return df_count, df_prop
    
    
    def get_classified_correlations(df, method):
        allCoeffs=[]
        correlationsMatrixAll = df.corr(method=method)
        for column in correlationsMatrixAll:
            for i in correlationsMatrixAll[column].index:
                df = correlationsMatrixAll.at[i, column]
                if df != 1.0:
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

    
    def get_single_track(df, track_id):
        grouped = df.groupby('track.id')
        df = grouped.get_group(track_id).copy()
        return df
    
    
    def count_tracks(df):
        print(len(df_tracks['track.id'].unique().tolist()))
    
    
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
                print(df[unit].name, df[unit].iloc[0])
        return(unitList)
    
    
    
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
    
    
    def reciprocal_transformation(column)
        reciprocal=1/column
        reciprocal=normalize(reciprocal)
        print(reciprocal.describe())
        return reciprocal
        
    def log_transformation(column)
        log = np.log(column)
        log=normalize(log)
        print(log.describe())
        return log