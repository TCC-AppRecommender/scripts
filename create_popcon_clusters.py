#!/usr/bin/env python

import gc
import os
import re
import sys
import mmap
import pickle
import shutil
import commands

import numpy as np
from scipy.sparse import csr_matrix

from sklearn.cluster import KMeans


BASE_FOLDER = 'popcon_clusters/'

ALL_PKGS_FILE = BASE_FOLDER + 'all_pkgs.txt'
CLUSTERS_FILE = BASE_FOLDER + 'clusters.txt'
SUBMISSIONS_CLUSTERS_FILE = BASE_FOLDER + 'submissions_clusters.txt'

SUBMISSIONS_FOLDER = BASE_FOLDER + 'submissions/'
SUBMISSION_FILE = SUBMISSIONS_FOLDER + 'submission_{}.txt'

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


def get_popcon_submissions(all_pkgs, popcon_entries_path):
    folders = os.listdir(popcon_entries_path)

    file_paths = commands.getoutput('find {}* -type f'.format(popcon_entries_path)).splitlines()

    len_all_pkgs = len(all_pkgs)
    len_submissions = len(file_paths)

    n_submission = 0
    cols = len_all_pkgs
    rows = len_submissions
    submissions = csr_matrix((rows, cols), dtype=np.uint8).todense()

    for file_path in file_paths:
        with open(file_path) as infile:
            m = mmap.mmap(infile.fileno(), 0, prot=mmap.ACCESS_READ)
            for line in iter(m.readline, ""):
                line = line.strip()
                try:
                    pkg = line.split()[2]
                    pkg_index = all_pkgs.index(pkg)
                    submissions[n_submission, pkg_index] = 1
                except KeyboardInterrupt:
                    exit(1)
                except:
                    continue
            m.close()

        n_submission += 1
        print_percentage(n_submission, len_submissions)

    return submissions


def remove_unused_pkgs(all_pkgs, submissions):
    cols = 1
    rows = submissions.shape[0]
    vector_ones = np.ones((rows, cols))

    sum_cols = submissions.T.dot(vector_ones).T
    indices = np.where(sum_cols == 0)[1].tolist()

    all_pkgs = np.matrix(all_pkgs)
    all_pkgs = np.delete(all_pkgs, indices, 1).tolist()[0]

    submissions = np.delete(submissions, indices, 1)

    return all_pkgs, submissions


def filter_little_used_packages(all_pkgs, submissions):
    cols = 1
    rows = submissions.shape[0]
    vector_ones = np.ones((rows, cols))

    histogram = submissions.T.dot(vector_ones)
    submissions_rate = histogram / rows

    indices = np.where(submissions_rate < PERCENT_USERS_FOR_RATE)[1].tolist()

    all_pkgs = np.matrix(all_pkgs)
    all_pkgs = np.delete(all_pkgs, indices, 1).tolist()[0]

    submissions = np.delete(submissions, indices, 1)

    return all_pkgs, submissions


def save_all_pkgs(all_pkgs):
    with open(ALL_PKGS_FILE, 'w') as text:
        len_all_pkgs = len(all_pkgs)

        for index, pkg in enumerate(all_pkgs):
            text.write(pkg + '\n')
            print_percentage(index + 1, len_all_pkgs)


def save_clusters(clusters):
    with open(CLUSTERS_FILE, 'w') as text:
        len_clusters = len(clusters)

        for index, cluster in enumerate(clusters):
            line = '; '.join([str(value) for value in cluster])
            text.write(line + '\n')
            print_percentage(index + 1, len_clusters)


def save_submissions(submissions, all_pkgs):
    len_submissions = len(submissions)

    for submission_index, submission in enumerate(submissions):
        with open(SUBMISSION_FILE.format(submission_index), 'w') as text:
            for index, value in enumerate(np.nditer(submission)):
                if value == 1:
                    pkg = all_pkgs[index]
                    text.write(pkg + '\n')

        print_percentage(submission_index + 1, len_submissions)


def save_submissions_clusters(submissions_clusters):
    with open(SUBMISSIONS_CLUSTERS_FILE, 'w') as text:
        len_submissions_clusters = len(submissions_clusters)

        for index, user_cluster in enumerate(submissions_clusters):
            line = "{}: {}".format(index, user_cluster)
            text.write(line + '\n')
            print_percentage(index + 1, len_submissions_clusters)


def save_data(all_pkgs, clusters, submissions_clusters, submissions):
    if os.path.exists(BASE_FOLDER):
        shutil.rmtree(BASE_FOLDER)
    os.makedirs(BASE_FOLDER)
    os.makedirs(SUBMISSIONS_FOLDER)

    print "Saving all_pkgs.txt"
    save_all_pkgs(all_pkgs)

    print "Saving clusters.txt"
    save_clusters(clusters)

    print "Saving submissions_clusters.txt"
    save_submissions_clusters(submissions_clusters)

    print "Saving submissions"
    save_submissions(submissions, all_pkgs)


def main(random_state, n_clusters, popcon_entries_path):

    print "Getting all debian packages"
    all_pkgs = get_all_pkgs()

    print "Loading popcon submissions"
    submissions = get_popcon_submissions(all_pkgs, popcon_entries_path)

    print "Remove unused packages"
    all_pkgs, submissions = remove_unused_pkgs(all_pkgs, submissions)

    print "Filter little used packages"
    all_pkgs, submissions = filter_little_used_packages(all_pkgs, submissions)

    print "Creating KMeans data"
    k_means = KMeans(n_clusters=n_clusters, random_state=random_state)
    k_means.fit(submissions)
    submissions_clusters = k_means.labels_.tolist()
    clusters = k_means.cluster_centers_.tolist()

    save_data(all_pkgs, clusters, submissions_clusters, submissions)

    print "\nFinish, files saved on: {}".format(BASE_FOLDER)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        usage = "Usage: {} [random_state] [n_clusters] [popcon-entries_path]"
        print usage.format(sys.argv[0])
        print "\n[options]"
        print "  random_state - Its a number of random_state of KMeans"
        print "  n_clusters   - Its the number of clusters are been used"
        exit(1)

    n_clusters = int(sys.argv[2])
    random_state = int(sys.argv[1])
    popcon_entries_path = os.path.expanduser(sys.argv[3])

    main(random_state, n_clusters, popcon_entries_path)
