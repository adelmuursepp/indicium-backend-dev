import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from random_cluster_generator import generate_clusters
from kmodes.kmodes import KModes


def k_modes(data, size_of_group):
    num_centroids = 5
    answers_matrix = np.array([*data.values()])
    students = np.array([*data.keys()])
    students = students.reshape(students.shape[0], 1)
    kmodes = KModes(n_clusters=num_centroids, init="Huang")

    predictions = kmodes.fit_predict(answers_matrix, categorical=range(15))
    predictions = predictions.reshape(predictions.shape[0], 1)

    groupings = np.concatenate((students, predictions), axis=1)
    groupings = (groupings[np.argsort(groupings[:, 1])])[:, 0]
    groupings_sets = []
    python_groups_arr = []
    i = 0
    # convert back into python strings
    for uid in groupings:
        python_groups_arr.append(str(uid))

    while i < len(python_groups_arr):
        if i + size_of_group > students.shape[0]:
            groupings_sets[-1] = (
                groupings_sets[-1] + python_groups_arr[i : students.shape[0]]
            )
            break
        groupings_sets.append(python_groups_arr[i : i + size_of_group])
        i += size_of_group

    return groupings_sets
    # groupings_of_size = np.array_split(groupings, groupings.shape[0]//size_of_group)
    # groupings_of_size = np.array(groupings_of_size)
    # print(groupings_of_size)


# ------- Below is the API contract this function expects for reference -----------
data = {
    "user_id1": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
    "user_id2": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
    "user_id3": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
    "user_id4": [1, 2, 3, 4, 5, 1, 2, 5, 4, 5, 1, 2, 3, 3, 5],
    "user_id5": [1, 2, 3, 4, 5, 3, 2, 3, 4, 5, 1, 1, 3, 4, 5],
    "user_id6": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
    "user_id7": [1, 2, 3, 4, 1, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
    "user_id8": [1, 2, 3, 4, 5, 1, 2, 3, 3, 5, 1, 2, 3, 4, 5],
    "user_id9": [1, 2, 3, 4, 5, 1, 3, 3, 4, 5, 1, 2, 3, 4, 5],
    "user_id10": [1, 2, 1, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
    "user_id11": [1, 1, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
}

# labels = k_modes(data, 2)
# print(labels)
