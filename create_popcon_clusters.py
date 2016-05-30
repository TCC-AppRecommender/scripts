#!/usr/bin/env python

import os
import pickle
import re
import shutil
import sys

import numpy as np

from sklearn.cluster import KMeans


BASE_FOLDER = 'popcon_clusters/'

ALL_PKGS_FILE = BASE_FOLDER + 'all_pkgs.txt'
CLUSTERS_FILE = BASE_FOLDER + 'clusters.txt'
USERS_CLUSTERS_FILE = BASE_FOLDER + 'users_clusters.txt'

USERS_FOLDER = BASE_FOLDER + 'users/'
USER_FILE = USERS_FOLDER + 'user_{}.txt'

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


def get_users(all_pkgs, popcon_entries):
    rows = len(all_pkgs)
    cols = len(popcon_entries)
    users = [[0 for x in range(rows)] for y in range(cols)]

    for pkg_index, pkg in enumerate(all_pkgs):
        for entry_index, popcon_entry in enumerate(popcon_entries):
            if pkg in popcon_entry:
                users[entry_index][pkg_index] = 1

        print_percentage(pkg_index + 1, len(all_pkgs))

    return users


def get_all_pkgs_rate(users_binary):
    number_of_users = len(users_binary)
    matrix_pkgs = np.matrix(users_binary)
    vector_ones = np.ones((len(users_binary), 1))

    histogram = matrix_pkgs.T.dot(vector_ones)
    all_pkgs_rate = histogram / number_of_users

    return all_pkgs_rate.T.tolist()[0]


def get_filtered_users_pkgs(all_pkgs, users_pkgs, users_binary):
    number_of_users = len(users_binary)

    all_pkgs_rate = get_all_pkgs_rate(users_binary)
    min_pkg_rate = number_of_users * PERCENT_USERS_FOR_RATE

    removed_pkgs = [pkg for index, pkg in enumerate(all_pkgs)
                    if all_pkgs_rate[index] < min_pkg_rate]

    filtered_users_pkgs = []
    len_users_pkgs = len(users_pkgs)
    for index, user_pkgs in enumerate(users_pkgs):
        filtered_user_pkgs = [pkg for pkg in user_pkgs
                              if pkg not in removed_pkgs]

        filtered_users_pkgs.append(filtered_user_pkgs)
        print_percentage(index + 1, len_users_pkgs)

    return filtered_users_pkgs


def get_all_pkgs(popcon_entries):
    all_pkgs = set()

    len_popcon_entries = len(popcon_entries)

    for index, popcon_entry in enumerate(popcon_entries):
        for pkg in popcon_entry:
            all_pkgs.add(pkg)

        print_percentage(index + 1, len_popcon_entries)

    all_pkgs = list(sorted(all_pkgs))
    return all_pkgs


def read_popcon_file(file_path):
    popcon_entry = []
    with open(file_path, 'r') as text:
        lines = text.readlines()
        for line in lines[1:-1]:
            pkg = line.split()[2]

            if (not re.match(r'^lib.*', pkg) and
               not re.match(r'.*doc$', pkg) and '/' not in line.split()[2]):
                popcon_entry.append(pkg)

    return sorted(popcon_entry)


def old_get_popcon_entries(popcon_entries_path):
    popcon_files = os.listdir(popcon_entries_path)
    len_files = len(popcon_files)

    popcon_entries = []
    for index, popcon_file in enumerate(popcon_files):
        popcon_file_path = os.path.join(popcon_entries_path, popcon_file)
        popcon_entry = read_popcon_file(popcon_file_path)

        if len(popcon_entry) > 0:
            popcon_entries.append(popcon_entry)

        print_percentage(index + 1, len_files)

    return popcon_entries


def get_popcon_files(popcon_entries_path):
    folders = os.listdir(popcon_entries_path)

    popcon_files = []
    for folder in folders:
        folder_path = os.path.join(popcon_entries_path, folder)
        file_names = os.listdir(folder_path)

        if type(file_names) is not list:
            file_names = [file_names]

        for file_name in file_names:
            popcon_files.append(os.path.join(folder_path, file_name))

    return popcon_files


def get_popcon_entries(popcon_entries_path):
    popcon_files = get_popcon_files(popcon_entries_path)

    popcon_entries = []
    len_popcon_files = len(popcon_files)
    for index, popcon_file in enumerate(popcon_files):
        popcon_entry = read_popcon_file(popcon_file)

        if len(popcon_entry) > 0:
            popcon_entries.append(popcon_entry)

        print_percentage(index + 1, len_popcon_files)

    return popcon_entries


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


def save_users(users_pkgs):
    len_users_pkgs = len(users_pkgs)

    for index, user_pkgs in enumerate(users_pkgs):
        with open(USER_FILE.format(index), 'w') as text:
            for pkg in user_pkgs:
                text.write(pkg + '\n')

        print_percentage(index + 1, len_users_pkgs)


def save_users_clusters(users_clusters):
    with open(USERS_CLUSTERS_FILE, 'w') as text:
        len_users_clusters = len(users_clusters)

        for index, user_cluster in enumerate(users_clusters):
            line = "{}: {}".format(index, user_cluster)
            text.write(line + '\n')
            print_percentage(index + 1, len_users_clusters)


def save_data(all_pkgs, clusters, users_clusters, users_pkgs):
    if os.path.exists(BASE_FOLDER):
        shutil.rmtree(BASE_FOLDER)
    os.makedirs(BASE_FOLDER)
    os.makedirs(USERS_FOLDER)

    print "Saving all_pkgs.txt"
    save_all_pkgs(all_pkgs)

    print "Saving clusters.txt"
    save_clusters(clusters)

    print "Saving users_clusters.txt"
    save_users_clusters(users_clusters)

    print "Saving users_pkgs.txt"
    save_users(users_pkgs)


def main():
    if len(sys.argv) < 4:
        usage = "Usage: {} [random_state] [n_clusters] [popcon-entries_path]"
        print usage.format(sys.argv[0])
        print "\n[options]"
        print "  random_state - Its a number of random_state of KMeans"
        print "  n_clusters   - Its the number of clusters are been used"
        exit(1)

    popcon_entries_path = os.path.expanduser(sys.argv[3])

    print "Loading popcon files:"
    popcon_entries = get_popcon_entries(popcon_entries_path)

    print "Get all packages of popcon files:"
    all_pkgs = get_all_pkgs(popcon_entries)

    print "Creating matrix of users"
    users_pkgs = popcon_entries
    users_binary = get_users(all_pkgs, users_pkgs)

    print "Filtering little used packages"
    users_pkgs = get_filtered_users_pkgs(all_pkgs, users_pkgs, users_binary)

    print "Creating KMeans data"
    n_clusters = int(sys.argv[2])
    random_state = int(sys.argv[1])
    k_means = KMeans(n_clusters=n_clusters, random_state=random_state)
    k_means.fit(users_binary)
    users_clusters = k_means.labels_.tolist()
    clusters = k_means.cluster_centers_.tolist()

    save_data(all_pkgs, clusters, users_clusters, users_pkgs)

    print "\nFinish, files saved on: {}".format(BASE_FOLDER)

if __name__ == '__main__':
    main()
