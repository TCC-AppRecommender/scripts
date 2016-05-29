#!/usr/bin/env python

import os
import pickle
import re
import sys

from sklearn.cluster import KMeans


DATA_FILE = 'knn_data'


def print_percentage(number, n_numbers, message='Percent', bar_length=40):
    percent = float(number) / float(n_numbers)
    hashes = '#' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(hashes))
    percent = int(round(percent * 100))

    percent_message = ("\r{}: [{}] [{} / {}] {}%".format(message,
        hashes + spaces, number, n_numbers, percent))

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


def get_all_pkgs(popcon_entries):
    all_pkgs = set()

    len_popcon_entries = len(popcon_entries)

    for index, popcon_entry in enumerate(popcon_entries):
        print_percentage(index + 1, len_popcon_entries)

        for pkg in popcon_entry:
            all_pkgs.add(pkg)

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

    return popcon_entry


def get_popcon_entries(popcon_entries_path):
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


def main():
    if len(sys.argv) < 2:
        print "Usage: {} [popcon-entries_path]".format(sys.argv[0])
        exit(1)

    popcon_entries_path = os.path.expanduser(sys.argv[1])

    print "Loading popcon files:"
    popcon_entries = get_popcon_entries(popcon_entries_path)

    print "Get all packages of popcon files:"
    all_pkgs = get_all_pkgs(popcon_entries)

    print "Creating matrix of users"
    users = get_users(all_pkgs, popcon_entries)


    print "Creating KMeans data"
    random_state = 170
    k_means = KMeans(n_clusters=3, random_state=random_state)
    k_means.fit(users)
    users_clusters = k_means.labels_.tolist()
    clusters = k_means.cluster_centers_.tolist()

    saved_data = {'all_pkgs': all_pkgs, 'clusters': clusters, 'users': users,
                  'users_clusters': users_clusters}
    with open(DATA_FILE, 'wb') as text:
        pickle.dump(saved_data, text)

    print "\nFinish, generated file: {}".format(DATA_FILE)

if __name__ == '__main__':
    main()
