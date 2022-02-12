import numpy as np
import matplotlib.pyplot as plt

"""
	This function generates num_of_clusters clusters at random from a uniform distribution
	Parameters:
	num_of_students: int
	num_of_clusters: int
	num_of_questions: int
	show_graph: boolean
"""


def generate_clusters(num_of_students, num_of_clusters, num_of_questions, show_graph):
    all_rows = np.empty((0, num_of_questions))
    examples_per_cluster = int(num_of_students / num_of_clusters)
    low = 0
    high = 2

    for i in range(num_of_clusters):
        cluster = np.random.default_rng().uniform(
            low, high, examples_per_cluster * num_of_questions
        )
        cluster = cluster.reshape(examples_per_cluster, num_of_questions)
        all_rows = np.append(all_rows, cluster, axis=0)
        low += 4
        high = low + 2

    if show_graph and num_of_questions == 2:
        plt.scatter(all_rows[:, 0], all_rows[:, 1], s=50, c="blue")
        plt.show()
    return all_rows
