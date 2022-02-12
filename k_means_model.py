import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from random_cluster_generator import generate_clusters

"""
	The following function fits a k-means model to the data with num_of_centroids centroids
	Parameters:
	num_of_centroids: int
"""


def k_means(num_of_centroids):
    """Since we have no real data to work with yet, we will be
    generating random clusters from a uniform distribution"""

    data = generate_clusters(50, num_of_centroids, 3, False)
    csv_data = pd.read_csv("data_sets/data-final.csv", sep="\t").iloc[0:10000, 1:50]
    csv_array = csv_data.to_numpy()

    km = KMeans(n_clusters=num_of_centroids)
    km.fit(csv_array)

    distance_to_centroids = np.empty((csv_array.shape[0], 0))

    print("score: " + str(km.score(csv_array)))

    for i in range(0, num_of_centroids):
        centroid = np.tile(km.cluster_centers_[i, :], (csv_array.shape[0], 1))
        distance = np.sum(np.square(csv_array - centroid), axis=1)
        distance_to_centroids = np.c_[distance_to_centroids, distance]
    labels = distance_to_centroids.argmax(axis=1)
    return labels


labels = k_means(5)
print("class 0:" + str(np.count_nonzero(labels == 0)))
print("class 1:" + str(np.count_nonzero(labels == 1)))
print("class 2:" + str(np.count_nonzero(labels == 2)))
print("class 3:" + str(np.count_nonzero(labels == 3)))
print("class 4:" + str(np.count_nonzero(labels == 4)))
