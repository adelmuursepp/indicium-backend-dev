import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from random_cluster_generator import generate_clusters
from kmodes.kmodes import KModes


def k_modes(num_centroids):
    csv_data = pd.read_csv(
        "~/Downloads/IPIP-FFM-data-8Nov2018/data-final.csv", sep="\t" # taking data from ....
    ).iloc[0:1000, 0:50]
    csv_array = csv_data.to_numpy()
    kmodes = KModes(n_clusters=num_centroids, init="Huang")
    predictions = kmodes.fit_predict(csv_array, categorical=range(csv_array.shape[1]))

    # Feature selection
    kmodes_fs = KModes(n_clusters=num_centroids, init="Huang")
    added_features = []
    feature = None

    for i in range(5):
        min_score = float("inf")
        for j in range(50):
            if j in set(added_features):
                continue
            temp_added_features = added_features + [j]
            arr = csv_array[:, temp_added_features]
            predictions = kmodes_fs.fit_predict(arr, categorical=range(arr.shape[1]))
            score = kmodes_fs.cost_
            if score < min_score:
                min_score = score
                feature = j
            print(min_score)
        print(feature)
        added_features.append(feature)

    print(min_score)
    print(added_features)
    print(kmodes.cost_)
    return predictions


labels = k_modes(5)
print("class 0:" + str(np.count_nonzero(labels == 0)))
print("class 1:" + str(np.count_nonzero(labels == 1)))
print("class 2:" + str(np.count_nonzero(labels == 2)))
print("class 3:" + str(np.count_nonzero(labels == 3)))
print("class 4:" + str(np.count_nonzero(labels == 4)))
