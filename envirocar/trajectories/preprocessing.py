# import os
from math import floor, ceil
from scipy import interpolate
from statistics import mean
import pandas as pd
import geopandas as gpd
import numpy as np
import datetime
import random
import string
from copy import copy

import folium

# from shapely.geometry import Point, LineString, Polygon
from shapely.geometry import Polygon
import json
from branca.colormap import linear
# import enum


class Preprocessing():
    def __init__(self):
        print("Initializing pre-processing class")   # do we need anything?

    def calculateAcceleration(self, points_df):
        """ Calculates acceleration for each point in the dataframe
            based on the speed and time of itself and the previous point

        Keyword Arguments:
            points_df {GeoDataFrame} -- A GeoDataFrame containing the track
                points

        Returns:
            combined_again -- new GeoDataFrame with "Acceleration.value" column
        """

        points_df['t'] = pd.to_datetime(
             points_df['time'], format='%Y-%m-%dT%H:%M:%S')

        dict_of_tracks = dict(iter(points_df.groupby('track.id')))

        for track_id in dict_of_tracks:
            time_arr = dict_of_tracks[track_id]['t'].tolist()
            speed_arr = dict_of_tracks[track_id]['Speed.value'].to_numpy()
            acceleration_array = [0]

            for i in range(1, len(time_arr)):
                # using speed not to calculate velocity because we don't care
                # about direction anyway
                velocity_change = speed_arr[i] - speed_arr[i-1]
                time_change = (time_arr[i] - time_arr[i-1]).total_seconds()

                if (time_change != 0):
                    acceleration = (velocity_change / time_change)
                else:
                    acceleration = 0

                # print(velocity_change, time_change, acceleration)
                acceleration_array.append(acceleration)

            dict_of_tracks[track_id]['Acceleration.value'] = acceleration_array

        combined_again = pd.concat(dict_of_tracks.values())

        return combined_again

    def split_by_time(self, points_df, seconds_start, seconds_end):
        """ Takes some part of the track

        Keyword Arguments:
            points {GeoDataFrame} -- A GeoDataFrame containing the track points
            seconds_start, seconds_end {int} -- desired start end end seconds

        Returns:
            combined_again -- Some part of the tracks
        """

        def seconds_since_start(x, start):
            # print(x, start)
            if (isinstance(x, str)):
                x = datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')
            seconds = (x-start).total_seconds()
            return int(seconds)

        dict_of_tracks = dict(iter(points_df.groupby('track.id')))
        beginnings = []

        for track_id in dict_of_tracks:
            start_time = datetime.datetime.strptime(
                dict_of_tracks[track_id].time.iloc[0], '%Y-%m-%dT%H:%M:%S')

            dict_of_tracks[track_id]['Seconds since start'] = \
                np.vectorize(seconds_since_start)(
                    np.array(dict_of_tracks[track_id]['time'].values.tolist()),
                    start_time)

            beginning = dict_of_tracks[track_id][(dict_of_tracks[track_id]
                                                 ['Seconds since start']
                                                 < seconds_end) &
                                                 (dict_of_tracks[track_id]
                                                 ['Seconds since start']
                                                 > seconds_start)]
            beginnings.append(beginning)

        combined_again = pd.concat(beginnings)

        return combined_again

    def remove_outliers(self, points, column):
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
            first_quartile = points[column].quantile(0.01)
            third_quartile = points[column].quantile(0.99)
            iqr = third_quartile-first_quartile   # Interquartile range
            fence_low = first_quartile - 1.5 * iqr
            fence_high = third_quartile + 1.5 * iqr

            new_points = points.loc[(points[column] > fence_low) & (
                points[column] < fence_high)]

        return new_points

    def interpolate(self, points, step_type="meters", step_pr=10):
        """ Interpolates points

        Keyword Arguments:
            points {GeoDataFrame} -- A GeoDataFrame containing the track points
            step_type {string} -- either "meters" or "seconds"
            step_pr {int} -- step precision. In case of "meters" can be 1 or 10

        Returns:
            new_points -- An interpolated trajectory
        """

        def date_to_seconds(x):
            date_time_obj = datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')
            seconds = (date_time_obj-datetime.datetime(1970, 1, 1)
                       ).total_seconds()
            return int(seconds)

        def seconds_to_date(x):
            date = datetime.datetime.fromtimestamp(x, datetime.timezone.utc)
            return date

        def randStr(chars=string.ascii_uppercase + string.digits, N=24):
            return ''.join(random.choice(chars) for _ in range(N))

        def interpolate_coords(x, input_array, step):
            # interpolations_methods = ['slinear', 'quadratic', 'cubic']
            points = np.array(input_array).T
            interpolator = interpolate.interp1d(x, points, kind='slinear',
                                                axis=0)
            ynew = interpolator(step)
            transposed = ynew.T
            return_values = [np.array(transposed[0]), np.array(transposed[1])]

            # # spline interpolation works better but takes different
            # # steps as an input, thus shifting all the points
            # step_norm = (step-min(step))/(max(step)-min(step))
            # tck, u = interpolate.splprep(input_array, s=0)
            # interpolated = interpolate.splev(step_norm, tck)

            return return_values

        def interpolate_linear(x, y, xnew):
            f = interpolate.interp1d(x, y)
            values_new = f(xnew)
            return values_new

        print('Amount of points before interpolation',
              points.shape)

        # to have flat attributes for coordinates
        points['lat'] = points['geometry'].apply(lambda coord: coord.y)
        points['lng'] = points['geometry'].apply(lambda coord: coord.x)
        points_df = pd.DataFrame(points)

        tracks_dict = dict(iter(points_df.groupby('track.id')))
        interpolated = []

        for track_id in tracks_dict:
            # removing duplicates because interpolation won't work otherwise
            points_df_cleaned = tracks_dict[track_id].drop_duplicates(
                ['lat', 'lng'], keep='last')

            # input for datetime in seconds
            points_df_cleaned['time_seconds'] = np.vectorize(date_to_seconds)(
                np.array(points_df_cleaned.time.values.tolist()))

            # creating the column name lists
            names_interpolate = [s for s in points_df_cleaned.columns if
                                 '.value' in s]
            # adding the other column names at front
            names_interpolate = ['lng', 'lat', 'time_seconds'] + \
                names_interpolate
            names_replicatate = np.setdiff1d(points_df_cleaned.columns,
                                             names_interpolate)
            names_extra = ['geometry', 'id', 'time']
            names_replicatate = [x for x in names_replicatate if x
                                 not in names_extra]

            time_seconds_array = points_df_cleaned[
                    'time_seconds'].to_numpy()

            passed_time = [(time_seconds_array[i+1]-time_seconds_array[i])
                           for i in range(len(time_seconds_array)-1)]
            passed_time = np.insert(passed_time, 0, 0, axis=0)
            # to interpolate for every meter or every 10 meters
            if (step_pr != 1):
                step_pr = 10
            dist = (points_df_cleaned['Speed.value']/3.6 * passed_time)/step_pr
            dist_between = [sum(dist[:i+1]) for i in range(len(dist))]
            dist_between = list(map(int, dist_between))
            # print(dist_between)

            points_df_cleaned['dist_between'] = dist_between

            points_df_cleaned.drop_duplicates(
                ['dist_between'], keep='first', inplace=True)

            dist_between = np.array(
                points_df_cleaned['dist_between'].values.tolist())
            # print(dist_between)

            del points_df_cleaned['dist_between']
            # measurements themselves
            columns_interpolate = [np.array(
                points_df_cleaned[column].values.tolist()) for column
                in names_interpolate]

            # split dataframe because splprep cannot take more than 11
            dfs = np.split(columns_interpolate, [2], axis=0)

            """ Interpolation itself """
            # Find the B-spline representation of the curve
            # tck (t,c,k): is a tuple containing the vector of knots,
            # the B-spline coefficients, and the degree of the spline.
            # u: is an array of the values of the parameter.

            if (step_type == 'seconds'):
                step_interp = np.linspace(
                    points_df_cleaned['time_seconds'].iloc[0],
                    points_df_cleaned['time_seconds'].iloc[-1],
                    points_df_cleaned['time_seconds'].iloc[-1]
                    - points_df_cleaned['time_seconds'].iloc[0])
                step_original = np.array(
                    points_df_cleaned['time_seconds'].values.tolist())
            else:
                step_interp = np.linspace(dist_between[0],
                                          dist_between[-1],
                                          dist_between[-1] -
                                          dist_between[0],
                                          dtype='int32')
                step_original = dist_between

            new_points = interpolate_coords(step_original, dfs[0], step_interp)

            for idx, column in enumerate(dfs[1]):
                new_points.append(interpolate_linear(step_original, column,
                                                     step_interp))

            # transposing the resulting matrix to fit it in the dataframe
            data = np.transpose(new_points)

            # constructing the new dataframe
            interpolated_df = pd.DataFrame(data)

            interpolated_df.columns = names_interpolate
            interpolated_df['time'] = np.vectorize(
                seconds_to_date)(interpolated_df['time_seconds'])

            # these should all be the same for one ride, so just replicating
            columns_replicate = [np.repeat(points_df_cleaned[column].iloc[0],
                                 len(step_interp)) for column
                                 in names_replicatate]

            replicated_transposed = np.transpose(columns_replicate)
            replicated_df = pd.DataFrame(replicated_transposed)
            replicated_df.columns = names_replicatate

            # combining replicated with interpolated
            full_df = pd.concat([interpolated_df, replicated_df], axis=1,
                                sort=False)

            # adding ids
            full_df['id'] = 0
            for row in full_df.index:
                full_df['id'][row] = randStr()

            # transforming back to a geodataframe
            full_gdf = gpd.GeoDataFrame(
                full_df, geometry=gpd.points_from_xy(full_df.lng, full_df.lat))

            # remove full_gdf['lng'], full_gdf['lat'] ?
            del full_gdf['time_seconds']

            # print(full_gdf['track.length'])
            interpolated.append(full_gdf)

            combined_again = pd.concat(interpolated)
        print('Amount of points after interpolation',
              combined_again.shape)
        return combined_again
