import pandas as pd
import numpy as np 
import geopandas as gpd

# class Correction():
#     def __init__(self):
#         print("Initializing class 'Correction'")  


def flag_faulty_percentages(df, setValueToNan=True, dropColumns=True, dropFlag=False):
    '''
        Aim: 
            Inspect if there are faulty percentages (percentages below 0 and above 100)

        Input: 
            Geodataframa

        Output: 
            Geodataframe with added column which contains when percentages are faulty
    '''
    df["faulty_percentages"] = 0
    units = df.filter(like='.unit').columns
    values = df.filter(like='.value').columns

    listNames =[]
    for col in units:
        if df[col].iloc[0]== '%':
            name = col.split(".")[0] + '.value'
            listNames.append(name)

    for variable in listNames:
        variableName = 'faulty_percentages_' + variable
        df[variableName] = 0
        df.loc[df[variable] < 0, 'faulty_percentages'] = 1
        df.loc[df[variable] > 100, 'faulty_percentages'] = 1
        df.loc[df[variable] < 0, variableName] = 1
        df.loc[df[variable] > 100, variableName] = 1
        faultyPercentagesV = (df[variableName].values == 1).sum()
        print(variableName, faultyPercentagesV)

        if setValueToNan == True:
            df.loc[df[variable] < 0, variable] = np.nan
            df.loc[df[variable] > 100, variable] = np.nan
        #df[variable +'_corrected' ] = df[variable].interpolate(method ='linear', limit_direction ='both')
        #print(variable, df[variable].isna().sum())
        
        if dropColumns == True:
            df.drop([variableName], axis=1, inplace=True)
        
    faultyPercentages = (df['faulty_percentages'].values == 1).sum()
    print('Flagged faulty percentages: ', faultyPercentages)
    if dropFlag == True:
        df.drop(['faulty_percentages'], axis=1, inplace=True)
    
    return df


def flag_implausible_negative_values(df, setToNan=False, dropFlag=False):
    '''
        Aim: Inspect if there are unexpected negative values

        Input: Geodataframa

        Output: Geodataframe with added column which contains 1 when values are negative
    '''   
    
    listNonNegative=['Speed.value', 
                     'CO2.value',
                     'Rpm.value',
                     'Consumption (GPS-based).value',
                     'Consumption.value',
                     'CO2 Emission (GPS-based).value']

    
    df["implausible_neg_value"] = 0
    for variable in listNonNegative:
        df.loc[df[variable] < 0, 'implausible_neg_value'] = 1
        if setToNan == True:
            df.loc[df[variable] < 0, variable] = np.nan
        
    implausibleNegativeValues = (df['implausible_neg_value'].values == 1).sum()
    print('Flagged implausible negative values: ', implausibleNegativeValues)
    if dropFlag == True:
        df.drop(['implausible_neg_value'], axis=1, inplace=True)
    return df


def drop_dublicates(complete_track_df, keep='last'):
    beforeDel=complete_track_df.shape[0]
    complete_track_df.drop_duplicates(subset=['geometry', 'Engine Load.value', 'Calculated MAF.value',
           'Speed.value', 'CO2.value', 'Intake Pressure.value', 'Rpm.value',
           'Intake Temperature.value', 'Consumption (GPS-based).value',
           'GPS Altitude.value', 'Throttle Position.value', 'GPS Bearing.value',
           'Consumption.value', 'GPS Accuracy.value',
           'CO2 Emission (GPS-based).value', 'GPS Speed.value', 
           'track.length', 'track.begin', 'track.end', 'sensor.type',
           'sensor.engineDisplacement', 'sensor.model', 'sensor.id',
           'sensor.fuelType', 'sensor.constructionYear', 'sensor.manufacturer'],keep='last', inplace=True)
    afterDel=complete_track_df.shape[0]
    deleted=beforeDel-afterDel
    print('Deleted rows: ', deleted)
    return complete_track_df


def flag_outlier_in_sample(df, dropOutlierColumn=False, setOutlierToNan=False, dropFlag=False):
    '''
        Aim: Find outlier with regard to the sample's distribution 

        Input: Geodataframa

        Output: Geodataframe with added column which values are '1' 
                        when a certain value of a variable in the list is considered to 
                        be an outlier regarding the samples's distribution
    '''
    ls = df.select_dtypes(['float64']).columns.to_list()
    
    df['outlier_in_sample'] = 0
    for variable in ls:
        variableName='outlier_in_sample_'+ variable
        df[variableName] = 0
        Q1 = df[variable].quantile(0.10)
        Q3 = df[variable].quantile(0.90)
        IQR = Q3 - Q1
        low_lim = Q1 - 1.5 * IQR 
        up_lim = Q3 + 1.5 * IQR  
        df.loc[df[variable] < low_lim, variableName] = 1
        df.loc[df[variable] > up_lim, variableName] = 1
        df.loc[df[variable] < low_lim, 'outlier_in_sample'] = 1
        df.loc[df[variable] > up_lim, 'outlier_in_sample'] = 1
        print(variableName, (df[variableName].values == 1).sum())

        if setOutlierToNan == True:
            df.loc[df[variableName] == 1 , variable] = np.nan

        if dropOutlierColumn == True:
            df.drop([variableName], axis=1, inplace=True)

    outlier = (df['outlier_in_sample'].values == 1).sum()
    print('Flagged outlier in sample: ', outlier)
    
    if dropFlag==True:
        df.drop(['outlier_in_sample'], axis=1, inplace=True)
        
    return df


def remove_outliers(points, column):
    """ Remove outliers by using the statistical approach
    as described in
    https://www.itl.nist.gov/div898/handbook/prc/section1/prc16.htm

    Keyword Arguments:
        points {GeoDataFrame} -- A GeoDataFrame containing the track points
        column {String} -- Columnn name to remove outliers from

    Returns:
        new_points -- Points with outliers removed
    """

    if (column == "Acceleration.value"):
        # trying to keep outliers while removing unrealistic values
        new_points = points.loc[(points[column] > -20) & (
            points[column] < 20)]
    else:
        # broader range with 0.01 and 0.99
        first_quartile = points[column].quantile(0.10)
        third_quartile = points[column].quantile(0.90)
        iqr = third_quartile-first_quartile   # Interquartile range
        fence_low = first_quartile - 1.5 * iqr
        fence_high = third_quartile + 1.5 * iqr

        new_points = points.loc[(points[column] > fence_low) & (
            points[column] < fence_high)]
    print('Removed outliers: ', points.shape[0]-new_points.shape[0])
    return new_points


def flag_outlier_in_track(df, dropLimits=True, dropOutlierColumn=True, setOutlierToNan=False, dropFlag=False):
    
    def low_limit(x):
            q1 = x.quantile(0.10)
            q3 = x.quantile(0.90)
            iqr = q3 - q1
            lower_limit = q1 - 1.5 * iqr
            return lower_limit

    def upper_limit(x):
            q1 = x.quantile(0.10)
            q3 = x.quantile(0.90)
            iqr = q3 - q1
            upper_limit = q3 + 1.5 * iqr
            return upper_limit
        
    ls = df.select_dtypes(['float64']).columns.to_list()
    df['outlier_in_track_all'] = 0
    for variable in ls:
            lowName = 'track_lowerLimit_' + variable
            upName = 'track_upperLimit_' + variable
            df_1 = df.groupby(['track.id'])
            df[lowName] = df_1[variable].transform(low_limit)
            df[upName] = df_1[variable].transform(upper_limit)
            df.loc[df[upName] < df[variable], "outlier_in_track_all"] = 1 
            df.loc[df[lowName] > df[variable], "outlier_in_track_all"] = 1 
            variableName='outlier_in_track_'+ variable
            df[variableName] = 0
            df.loc[df[upName] < df[variable], variableName] = 1 
            df.loc[df[lowName] > df[variable], variableName] = 1
            print(variableName, (df[variableName].values == 1).sum())

            if setOutlierToNan == True:
                df.loc[df[variableName] == 1 , variable] = np.nan

            if dropLimits == True:
                df.drop([upName, lowName], axis=1, inplace=True)

            if dropOutlierColumn == True:
                df.drop([variableName], axis=1, inplace=True)

    outlier = (df['outlier_in_track_all'].values == 1).sum()
    print('Rows which contain outliers in tracks  (there may be multiple outlier in a single row) : ',outlier)
    
    if dropFlag == True:
        df.drop(['outlier_in_track_all'], axis=1, inplace=True)
    return df
