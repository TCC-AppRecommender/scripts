#!/usr/bin/env python

import gc
import os
import re
import sys
import shutil
import commands

import numpy as np
import scipy.sparse as sp

from multiprocessing import Process, Queue, Manager
from sklearn.cluster import MiniBatchKMeans


BASE_FOLDER = 'popcon_clusters/'

ALL_PKGS_FILE = BASE_FOLDER + 'all_pkgs.txt'
CLUSTERS_FILE = BASE_FOLDER + 'clusters.txt'
PKGS_CLUSTERS = BASE_FOLDER + 'pkgs_clusters.txt'
SUBMISSIONS_CLUSTERS_FILE = BASE_FOLDER + 'submissions_clusters.txt'

PERCENT_USERS_FOR_RATE = 0.05

def print_percentage(number, n_numbers, message='Percent', bar_length=40):
    percent = float(number) / float(n_numbers)
    hashes = '#' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(hashes))
    percent = int(round(percent * 100))

    percent_message = "\r{}: [{}] [{} / {}] {}%".format(message,
                                                        hashes + spaces,
                                                        number, n_numbers,
                                                        percent)
    sys.stdout.write(percent_message)
    sys.stdout.flush()

    if number == n_numbers:
        print '\n'


def get_all_pkgs():
    pkgs = commands.getoutput('apt-cache pkgnames').splitlines()
    pkgs = sorted(pkgs)

    all_pkgs = [pkg for pkg in pkgs if not re.match(r'^lib.*', pkg) and
               not re.match(r'.*doc$', pkg)]

    return all_pkgs


def get_submissions(all_pkgs, submissions_paths, n_submission_index,
                    n_submission_paths, len_submissions, out_queue):
    all_pkgs_np = np.array(all_pkgs)

    cols = len(all_pkgs)
    rows = len(submissions_paths)
    submissions = sp.lil_matrix((rows, cols), dtype=np.uint8)
    n_file = 0

    match = re.compile(r'^\d+\s\d+\s([^\/\s]+)(?!.*<NOFILES>)', re.MULTILINE)

    for file_path in submissions_paths:
        text = commands.getoutput('cat {}'.format(file_path))

        pkgs = match.findall(text)
        indices = np.where(np.in1d(all_pkgs_np, pkgs))[0]
        submissions[n_file, indices] = 1

        n_file += 1
        n_submission_paths.value += 1

        del text, pkgs, indices
        if n_submission_paths.value % 500 == 0:
            gc.collect()

        print_percentage(n_submission_paths.value, len_submissions)

    out_queue.put(submissions)


def get_popcon_submissions(popcon_entries_path, n_processors):
    all_pkgs = get_all_pkgs()
    folders = os.listdir(popcon_entries_path)

    command = 'find {}* -type f'.format(popcon_entries_path)
    submissions_paths = commands.getoutput(command).splitlines()

    manager = Manager()
    n_submission_paths = manager.Value('i', 0)

    out_queues = []
    process_submissions = []
    len_submissions = len(submissions_paths)
    block = len_submissions / n_processors

    for index in range(n_processors - 1):
        index += 1
        begin = index*block
        end = (index+1)*block

        if index < n_processors - 1:
            submissions_paths_block = submissions_paths[begin:end]
        else:
            submissions_paths_block = submissions_paths[begin:]

        out_queue = Queue()
        process_submission = Process(
            target=get_submissions, args=(all_pkgs, submissions_paths_block,
                                          index, n_submission_paths,
                                          len_submissions, out_queue))
        process_submission.start()
        out_queues.append(out_queue)
        process_submissions.append(process_submission)

    out_queue = Queue()
    submissions_paths_block = submissions_paths[:block]
    get_submissions(all_pkgs, submissions_paths_block, 0,
                    n_submission_paths, len_submissions, out_queue)

    submissions = [out_queue.get()]
    for out_queue in out_queues:
        submission = out_queue.get()
        submissions.append(submission)

    for process_submission in process_submissions:
        process_submission.join()

    submissions = sp.vstack(submissions, 'csr')

    return all_pkgs, submissions


def remove_unused_pkgs(all_pkgs, submissions):
    cols = 1
    rows = submissions.shape[0]
    vector_ones = np.ones((rows, cols))

    sum_cols = submissions.T.dot(vector_ones).T
    indices = np.where(sum_cols == 0)[1].tolist()
    csr_indices = np.where(sum_cols != 0)[1].tolist()

    all_pkgs = np.matrix(all_pkgs)
    all_pkgs = np.delete(all_pkgs, indices, 1).tolist()[0]

    submissions = submissions[:,csr_indices]

    return all_pkgs, submissions


def filter_little_used_packages(all_pkgs, submissions):
    cols = 1
    rows = submissions.shape[0]
    vector_ones = np.ones((rows, cols))

    histogram = submissions.T.dot(vector_ones)
    submissions_rate = histogram / rows

    indices = np.where(submissions_rate < PERCENT_USERS_FOR_RATE)[0].tolist()
    csr_indices = np.where(submissions_rate >= PERCENT_USERS_FOR_RATE)[0].tolist()

    all_pkgs = np.matrix(all_pkgs)
    all_pkgs = np.delete(all_pkgs, indices, 1).tolist()[0]

    submissions = submissions[:,csr_indices]

    return all_pkgs, submissions


def create_pkgs_clusters(all_pkgs, submissions, submissions_clusters,
                         n_clusters):
    rows = len(all_pkgs)
    cols = n_clusters
    pkgs_clusters = sp.lil_matrix((rows, cols), dtype=np.uint8)

    all_pkgs_np = np.matrix(all_pkgs)
    len_submissions_clusters = len(submissions_clusters)

    for submission_index, cluster in enumerate(submissions_clusters):
        submission = submissions[submission_index]
        indices = submission.nonzero()[1].tolist()

        increment = 1 + pkgs_clusters[indices, cluster].todense()
        pkgs_clusters[indices, cluster] = increment

        print_percentage(submission_index + 1, len_submissions_clusters)

    return pkgs_clusters


def save_clusters(clusters):
    lines = []
    len_clusters = len(clusters)

    for index, cluster in enumerate(clusters):
        line = ';'.join([str(value) for value in cluster])
        lines.append(line)
        print_percentage(index + 1, len_clusters)

    with open(CLUSTERS_FILE, 'w') as text:
        text.write("\n".join(lines))


def save_pkgs_clusters(all_pkgs, pkgs_clusters):
    lines = []

    for index, pkg_cluster in enumerate(pkgs_clusters):
        clusters = pkg_cluster.todense().tolist()[0]
        str_clusters = ";".join(("{}:{}".format(cluster, times)
                                for cluster, times in enumerate(clusters)))
        line = "{}-{}".format(all_pkgs[index], str_clusters)
        lines.append(line)
        print_percentage(index, pkgs_clusters.shape[0])

    with open(PKGS_CLUSTERS, 'w') as text:
        text.write("\n".join(lines))


def save_data(all_pkgs, clusters, pkgs_clusters):
    if os.path.exists(BASE_FOLDER):
        shutil.rmtree(BASE_FOLDER)
    os.makedirs(BASE_FOLDER)

    print "Saving clusters.txt"
    save_clusters(clusters)

    print "Saving pkgs_clusters.txt"
    save_pkgs_clusters(all_pkgs, pkgs_clusters)


def generate_kmeans_data(n_clusters, random_state, n_processors, submissions):
    k_means = MiniBatchKMeans(n_clusters=n_clusters, init='k-means++',
                              random_state=random_state, batch_size=1000)
    k_means.fit(submissions)
    submissions_clusters = k_means.labels_.tolist()
    clusters = k_means.cluster_centers_.tolist()

    return clusters, submissions_clusters


def main(random_state, n_clusters, n_processors, popcon_entries_path):

    print "Loading popcon submissions"
    all_pkgs, submissions = get_popcon_submissions(popcon_entries_path,
                                                   n_processors)
    gc.collect()

    print "Remove unused packages"
    all_pkgs, submissions = remove_unused_pkgs(all_pkgs, submissions)
    gc.collect()

    print "Filter little used packages"
    all_pkgs, submissions = filter_little_used_packages(all_pkgs, submissions)
    gc.collect()

    print "Creating KMeans data"
    data = generate_kmeans_data(n_clusters, random_state, n_processors,
                                submissions)
    clusters, submissions_clusters = data
    gc.collect()

    print "Creating packages clusters"
    pkgs_clusters = create_pkgs_clusters(all_pkgs, submissions,
                                         submissions_clusters, len(clusters))
    gc.collect()

    save_data(all_pkgs, clusters, pkgs_clusters)

    print "\nFinish, files saved on: {}".format(BASE_FOLDER)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage = "Usage: {} [popcon-entries_path] [random_state] "\
                "[n_clusters] [n_processors]"
        print usage.format(sys.argv[0])
        print "\n[options]"
        print "  popcon-entries_path     - Its the path of folder with the"
        print "                            popularity-contest submissions"
        print "  random_state (optional) - Its a number of random_state of KMeans"
        print "  n_clusters   (optional) - Its the number of clusters are been used"
        print "  n_processors (optional) - Its the number of processors to be used"
        exit(1)

    len_argv = len(sys.argv)
    n_clusters = int(sys.argv[3]) if 3 < len_argv else 20
    random_state = int(sys.argv[2]) if 2 < len_argv else 170
    n_processors = int(sys.argv[4]) if 4 < len_argv else 1
    popcon_entries_path = os.path.expanduser(sys.argv[1])

    if not os.path.exists(popcon_entries_path):
        print "Folder not exists: {}".format(popcon_entries_path)
        exit(1)

    main(random_state, n_clusters, n_processors, popcon_entries_path)
