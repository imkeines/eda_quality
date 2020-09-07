import pandas as pd
import numpy as np 
import geopandas as gpd



class Correction():
    def __init__(self):
        print("Initializing class 'Correction'")  


    def flag_faulty_percentages(df):
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


            df.loc[df[variable] < 0, variable] = np.nan
            df.loc[df[variable] > 100, variable] = np.nan
            #df[variable +'_corrected' ] = df[variable].interpolate(method ='linear', limit_direction ='both')
            #print(variable, df[variable].isna().sum())

        faultyPercentages = (df['faulty_percentages'].values == 1).sum()
        print('Flagged faulty percentages: ', faultyPercentages)
        return df
    
    
    def flag_implausible_negative_values(df,listOfVariableNames):
        '''
            Aim: Inspect if there are unexpected negative values

            Input: Geodataframa

            Output: Geodataframe with added column which contains 1 when values are negative
        '''   
        df["implausible_neg_value"] = 0
        for variable in listOfVariableNames:
            df.loc[df[variable] < 0, 'implausible_neg_value'] = 1
        implausibleNegativeValues = (df['implausible_neg_value'].values == 1).sum()
        print('Flagged implausible negative values: ', implausibleNegativeValues)
        return df
    
    
    
    def delete_dublicated_rows(df): 
        df.drop_duplicates(subset=['geometry', 'Engine Load.value', 'Calculated MAF.value',
                   'Speed.value', 'CO2.value', 'Intake Pressure.value', 'Rpm.value',
                   'Intake Temperature.value', 'Consumption (GPS-based).value',
                   'GPS Altitude.value', 'Throttle Position.value', 'GPS Bearing.value',
                   'Consumption.value', 'GPS Accuracy.value',
                   'CO2 Emission (GPS-based).value', 'GPS Speed.value', 
                   'track.length', 'track.begin', 'track.end', 'sensor.type',
                   'sensor.engineDisplacement', 'sensor.model', 'sensor.id',
                   'sensor.fuelType', 'sensor.constructionYear', 'sensor.manufacturer',
                   'track.appVersion', 'track.touVersion', 'GPS HDOP.value',
                   'GPS PDOP.value', 'GPS VDOP.value'], inplace=True, keep='last')
        return df
    
    
    
    def flag_outlier_in_sample(df, listOfVariableNames, dropOutlierColumn=False, setOutlierToNan=False):
        '''
            Aim: Find outlier with regard to the sample's distribution 

            Input: Geodataframa

            Output: Geodataframe with added column which values are '1' 
                        when a certain value of a variable in the list is considered to be an outlier regarding the samples's distribution
        '''
        df['outlier_in_sample'] = 0
        for variable in listOfVariableNames:
            variableName='outlier_in_sample_'+ variable
            df[variableName] = 0
            Q1 = df[variable].quantile(0.25)
            Q3 = df[variable].quantile(0.75)
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
        return df

    
    

    def flag_outlier_in_track(df, listOfVariableNames, dropLimits=True, dropOutlierColumn=False, setOutlierToNan=False):

        def low_limit(x):
                q1 = x.quantile(0.25)
                q3 = x.quantile(0.75)
                iqr = q3 - q1
                lower_limit = q1 - 1.5 * iqr
                return lower_limit

        def upper_limit(x):
                q1 = x.quantile(0.25)
                q3 = x.quantile(0.75)
                iqr = q3 - q1
                upper_limit = q3 + 1.5 * iqr
                return upper_limit

        df['outlier_in_track_all'] = 0
        for variable in listOfVariableNames:
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
        return df
        