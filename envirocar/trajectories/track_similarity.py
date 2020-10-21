import numpy as np
import pandas as pd
import similaritymeasures
from math import factorial
import matplotlib.pyplot as plt
from itertools import combinations
from timeit import default_timer as timer




def get_similarity_matrix(df):
    """ Returns a similarity matrix using the crossed similarity dataframe

        Keyword Arguments:
        df{df}         -- Crossed similarity dataframe

        Returns:

        df{dataframe}  -- Similarity matrix of trajectories (Symmetric matrix)

        """

    uniq_traj = np.unique(list(df['Trajectory_1'].unique())+list(
        df['Trajectory_2'].unique()))
    number_uniqtraj = len(uniq_traj)

    similarity_diagonal = [1] * number_uniqtraj
    df_diagonal = pd.DataFrame(list(zip(uniq_traj, uniq_traj,
                                        similarity_diagonal)), columns=['Trajectory_1',
                                                                        'Trajectory_2', 'Similarity'])
    frames = [df, df_diagonal]
    df = pd.concat(frames, ignore_index=True)

    df = df.sort_values(by=['Similarity'], ascending=False).reset_index(
        drop=True)

    df = df.pivot(index='Trajectory_1', columns='Trajectory_2',
                  values='Similarity').copy()

    return(df)


def plot_similarity_matrix(df_similarity_matrix, title):
    """ Generates similarity matrix plot

        Keyword Arguments:
        df{dataframe}      -- Similarity matrix of trajectories
        """

    sum_corr = list(df_similarity_matrix.sum(
    ).sort_values(ascending=True).index.values)
    df_similarity_matrix = df_similarity_matrix[sum_corr]
    df = df_similarity_matrix.reindex(sum_corr)

    f = plt.figure(figsize=(19, 15))
    plt.matshow(df, fignum=f.number)
    plt.title(title, y=1.2, fontsize=25)
    plt.xticks(range(df.shape[1]), df.columns, fontsize=10, rotation=90)
    plt.yticks(range(df.shape[1]), df.columns, fontsize=10)
    cb = plt.colorbar()
    cb.ax.tick_params(labelsize=14)
