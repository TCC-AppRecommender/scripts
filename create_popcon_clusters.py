#!/usr/bin/env python

import argparse
import commands
import glob
import os
import random
import re
import sys

import numpy as np
import scipy.sparse as sp

from multiprocessing import Process, Queue, Manager
from sklearn.cluster import MiniBatchKMeans


CLUSTERS_FILE = 'clusters.txt'
PKGS_CLUSTERS = 'pkgs_clusters.txt'

MIRROR_BASE = '/srv/mirrors/debian'

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


def read_pkgs_from_file(mirror_path):
    pkgs = set()
    glob_mirror_path = glob.glob(mirror_path)
    pkgs_regex = re.compile(r'^Package:\s(.+)', re.MULTILINE)

    for file_path in glob_mirror_path:
        text = commands.getoutput('zcat {}'.format(file_path))
        pkgs |= set(pkgs_regex.findall(text))

    return pkgs


def get_all_pkgs():
    pkgs = set()
    mirror = '{}/dists/{}/*/binary-i386/Packages.gz'
    stable_mirror = mirror.format(MIRROR_BASE, 'stable')
    unstable_mirror = mirror.format(MIRROR_BASE, 'unstable')

    print 'Loading packages on files of stable'
    pkgs |= read_pkgs_from_file(stable_mirror)

    print 'Loading packages on files of unstable'
    pkgs |= read_pkgs_from_file(unstable_mirror)

    pkgs = sorted(list(pkgs))

    all_pkgs = [pkg for pkg in pkgs if not re.match(r'^lib.*', pkg) and
                not re.match(r'.*doc$', pkg)]

    return all_pkgs


def get_submissions(all_pkgs, submissions_paths, n_submissions_paths,
                    len_submissions, out_queue):
    all_pkgs_np = np.array(all_pkgs)

    matrix_dimensions = (len(submissions_paths), len(all_pkgs))
    submissions = sp.lil_matrix(matrix_dimensions, dtype=np.uint8)

    pkg_regex = re.compile(r'^\d+\s\d+\s([^\/\s]+)(?!.*<NOFILES>)',
                           re.MULTILINE)

    n_file = 0
    for file_path in submissions_paths:
        text = commands.getoutput('cat {}'.format(file_path))

        pkgs = pkg_regex.findall(text)
        indices = np.where(np.in1d(all_pkgs_np, pkgs))[0]
        submissions[n_file, indices] = 1

        n_file += 1
        n_submissions_paths.value += 1

        print_percentage(n_submissions_paths.value, len_submissions)

    out_queue.put(submissions)


def get_submissions_paths(popcon_entries_path):
    command = 'find {}* -type f'.format(popcon_entries_path)
    submissions_paths = commands.getoutput(command).splitlines()
    random.shuffle(submissions_paths)
    initial_index = 0
    if len(submissions_paths) < 1000:
        initial_index = len(submissions_paths) / 10
    else:
        initial_index = 100
    submissions_paths = submissions_paths[initial_index:]

    return submissions_paths


def get_popcon_submissions(all_pkgs, popcon_entries_path, n_processors):
    submissions_paths = get_submissions_paths(popcon_entries_path)

    manager = Manager()
    n_submissions_paths = manager.Value('i', 0)

    out_queues = []
    process_submissions = []
    len_submissions = len(submissions_paths)
    block = len_submissions / n_processors

    for index in range(n_processors - 1):
        index += 1
        begin = index * block
        end = (index + 1) * block

        if index < n_processors - 1:
            submissions_paths_block = submissions_paths[begin:end]
        else:
            submissions_paths_block = submissions_paths[begin:]

        out_queue = Queue()
        process_submission = Process(
            target=get_submissions, args=(all_pkgs, submissions_paths_block,
                                          n_submissions_paths,
                                          len_submissions, out_queue))
        process_submission.start()
        out_queues.append(out_queue)
        process_submissions.append(process_submission)

    out_queue = Queue()
    submissions_paths_block = submissions_paths[:block]
    get_submissions(all_pkgs, submissions_paths_block, n_submissions_paths,
                    len_submissions, out_queue)

    submissions = [out_queue.get()]
    for out_queue in out_queues:
        submission = out_queue.get()
        submissions.append(submission)

    for process_submission in process_submissions:
        process_submission.join()

    submissions = sp.vstack(submissions, 'csr')

    return submissions


def discard_nonpupular_pkgs(all_pkgs, submissions):
    cols = 1
    rows = submissions.shape[0]
    vector_ones = np.ones((rows, cols))

    sum_cols = submissions.T.dot(vector_ones).T
    indices = np.where(sum_cols == 0)[1].tolist()
    csr_indices = np.where(sum_cols != 0)[1].tolist()

    all_pkgs = np.matrix(all_pkgs)
    all_pkgs = np.delete(all_pkgs, indices, 1).tolist()[0]

    submissions = submissions[:, csr_indices]

    return all_pkgs, submissions


def filter_little_used_packages(all_pkgs, submissions):
    cols = 1
    rows = submissions.shape[0]
    vector_ones = np.ones((rows, cols))

    histogram = submissions.T.dot(vector_ones)
    submissions_rate = histogram / rows

    indices = np.where(submissions_rate < PERCENT_USERS_FOR_RATE)[0].tolist()
    csr_indices = np.where(submissions_rate >= PERCENT_USERS_FOR_RATE)[0]
    csr_indices = csr_indices.tolist()

    all_pkgs = np.matrix(all_pkgs)
    all_pkgs = np.delete(all_pkgs, indices, 1).tolist()[0]

    submissions = submissions[:, csr_indices]

    return all_pkgs, submissions


def create_pkgs_clusters(all_pkgs, submissions, submissions_clusters,
                         n_clusters):
    rows = len(all_pkgs)
    cols = n_clusters
    pkgs_clusters = sp.lil_matrix((rows, cols), dtype=np.uint8)

    len_submissions_clusters = len(submissions_clusters)

    for submission_index, cluster in enumerate(submissions_clusters):
        submission = submissions[submission_index]
        indices = submission.nonzero()[1].tolist()

        increment = 1 + pkgs_clusters[indices, cluster].todense()
        pkgs_clusters[indices, cluster] = increment

        print_percentage(submission_index + 1, len_submissions_clusters)

    return pkgs_clusters


def save_clusters(clusters, output_folder):
    lines = []
    len_clusters = len(clusters)

    for index, cluster in enumerate(clusters):
        line = ';'.join([str(value) for value in cluster])
        lines.append(line)
        print_percentage(index + 1, len_clusters)

    with open(output_folder + CLUSTERS_FILE, 'w') as text:
        text.write("\n".join(lines))


def save_pkgs_clusters(all_pkgs, pkgs_clusters, output_folder):
    lines = []

    for index, pkg_cluster in enumerate(pkgs_clusters):
        clusters = pkg_cluster.todense().tolist()[0]
        str_clusters = ";".join(("{}:{}".format(cluster, times)
                                for cluster, times in enumerate(clusters)
                                if times > 0))
        line = "{}-{}".format(all_pkgs[index], str_clusters)
        lines.append(line)
        print_percentage(index, pkgs_clusters.shape[0])

    with open(output_folder + PKGS_CLUSTERS, 'w') as text:
        text.write("\n".join(lines))


def save_data(all_pkgs, clusters, pkgs_clusters, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print "Saving clusters.txt"
    save_clusters(clusters, output_folder)

    print "Saving pkgs_clusters.txt"
    save_pkgs_clusters(all_pkgs, pkgs_clusters, output_folder)


def generate_kmeans_data(n_clusters, random_state, n_processors, submissions):
    k_means = MiniBatchKMeans(n_clusters=n_clusters, init='k-means++',
                              random_state=random_state, batch_size=1000)
    k_means.fit(submissions)
    submissions_clusters = k_means.labels_.tolist()
    clusters = k_means.cluster_centers_.tolist()

    return clusters, submissions_clusters


def main(random_state, n_clusters, n_processors, popcon_entries_path,
         output_folder):

    print "Loading all packages"
    all_pkgs = get_all_pkgs()

    print "Loading popcon submissions"
    submissions = get_popcon_submissions(all_pkgs, popcon_entries_path,
                                         n_processors)

    print "Discarding non packages"
    all_pkgs, submissions = discard_nonpupular_pkgs(all_pkgs, submissions)

    print "Filter little used packages"
    all_pkgs, submissions = filter_little_used_packages(all_pkgs, submissions)

    print "Creating KMeans data"
    data = generate_kmeans_data(n_clusters, random_state, n_processors,
                                submissions)
    clusters, submissions_clusters = data

    print "Creating packages clusters"
    pkgs_clusters = create_pkgs_clusters(all_pkgs, submissions,
                                         submissions_clusters, len(clusters))

    save_data(all_pkgs, clusters, pkgs_clusters, output_folder)

    print "\nFinish, files saved on: {}".format(output_folder)


def get_expand_folder_path(folder_path):
    expand_folder_path = os.path.expanduser(folder_path)
    if expand_folder_path[-1] != '/':
        expand_folder_path += '/'

    return expand_folder_path


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('popcon_entries_path', type=str,
                        help='path of folder with the popularity-contest '
                             'submissions')
    parser.add_argument('-o', '--output', type=str, metavar='',
                        default='.', help='path of folder to output data')
    parser.add_argument('-c', '--n_clusters', type=int, metavar='',
                        default=200, help='Number of clusters are been used')
    parser.add_argument('-p', '--n_processors', type=int, metavar='',
                        default=1, help='Number of processors to be used')
    parser.add_argument('-r', '--random_state', type=int, metavar='',
                        default=170, help='Number of processors to be used')

    return parser


if __name__ == '__main__':
    parser = create_parser()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    args.output = get_expand_folder_path(args.output)
    args.popcon_entries_path = get_expand_folder_path(args.popcon_entries_path)

    if not os.path.exists(args.popcon_entries_path):
        print "Folder not exists: {}".format(args.popcon_entries_path)
        exit(1)

    main(args.random_state, args.n_clusters, args.n_processors,
         args.popcon_entries_path, args.output)
