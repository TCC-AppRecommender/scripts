#!/usr/bin/env python3

import argparse
import getpass
import glob
import gnupg
import hashlib
import os
import random
import re
import shutil
import sys
import tarfile

import numpy as np
import scipy.sparse as sp

from multiprocessing import Process, Queue, Manager
from sklearn.cluster import MiniBatchKMeans


INRELEASE_FILE = 'InRelease'

CLUSTERS_FILE = 'clusters.txt'
PKGS_CLUSTERS = 'pkgs_clusters.txt'

CLUSTERS_FILE_TAR = 'clusters.tar.xz'
PKGS_CLUSTERS_TAR = 'pkgs_clusters.tar.xz'

CLUSTERS_FILE_TAR = 'clusters.tar.xz'

MIRROR_BASE = '/srv/mirrors/debian'

PERCENT_USERS_FOR_RATE = 0.05

VERBOSE = False


def verbose_print(message):
    if VERBOSE:
        print(message)


def print_percentage(number, n_numbers, message='Percent', bar_length=40):
    if not VERBOSE:
        return

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
        print('\n')


def get_tarfile_text(tarfile_path):
    text = ''
    tar = tarfile.open(tarfile_path)

    for member in tar.members:
        ifile = tar.extractfile(member)
        text = ifile.read().decode('utf-8')

    tar.close()

    return text


def read_pkgs_from_mirror(mirror_path):
    pkgs = set()
    glob_mirror_path = glob.glob(mirror_path)
    pkgs_regex = re.compile(r'^Package:\s(.+)', re.MULTILINE)

    for file_path in glob_mirror_path:
        text = get_tarfile_text(file_path)
        pkgs |= set(pkgs_regex.findall(text))

    return pkgs


def get_all_pkgs():
    all_pkgs = set()
    mirror = '{}/dists/{}/*/binary-i386/Packages.xz'
    stable_mirror = mirror.format(MIRROR_BASE, 'stable')
    unstable_mirror = mirror.format(MIRROR_BASE, 'unstable')

    verbose_print('Loading packages names of Debian stable')
    all_pkgs |= read_pkgs_from_mirror(stable_mirror)

    verbose_print('Loading packages names of Debian unstable')
    all_pkgs |= read_pkgs_from_mirror(unstable_mirror)

    all_pkgs = sorted(list(all_pkgs))

    return all_pkgs


def get_submissions_matrix(all_pkgs, submissions_paths, n_readed_submissions,
                           len_submissions, out_queue):
    all_pkgs_np = np.array(all_pkgs)

    matrix_dimensions = (len(submissions_paths), len(all_pkgs))
    submissions_matrix = sp.lil_matrix(matrix_dimensions, dtype=np.uint8)

    pkg_regex = re.compile(r'^\d+\s\d+\s([^\/\s]+)(?!.*<NOFILES>)',
                           re.MULTILINE)

    n_file = 0
    for file_path in submissions_paths:
        ifile = open(file_path, 'rb')
        text = ifile.read().decode('utf-8')
        ifile.close()

        pkgs = pkg_regex.findall(text)
        indices = np.where(np.in1d(all_pkgs_np, pkgs))[0]
        submissions_matrix[n_file, indices] = 1

        n_file += 1
        n_readed_submissions.value += 1

        print_percentage(n_readed_submissions.value, len_submissions)

    out_queue.put(submissions_matrix)


def get_submissions_paths(popcon_entries_path):
    submissions_paths = []
    for dirpath, dirnames, filenames in os.walk(popcon_entries_path):
        submissions_paths += [os.path.join(dirpath, filename)
                              for filename in filenames]

    random.shuffle(submissions_paths)
    initial_index = 0
    if len(submissions_paths) < 1000:
        initial_index = int(len(submissions_paths) / 10)
    else:
        initial_index = 100
    submissions_paths = submissions_paths[initial_index:]

    return submissions_paths


def get_submissions_path_block(index, submissions_paths, block_size,
                               n_processors):
    index += 1
    begin = int(index * block_size)
    end = int((index + 1) * block_size)

    if index < n_processors - 1:
        submissions_paths_block = submissions_paths[begin:end]
    else:
        submissions_paths_block = submissions_paths[begin:]

    return submissions_paths_block


def create_one_submission_process(all_pkgs, submissions_paths_block,
                                  n_readed_submissions, len_submissions):
    out_queue = Queue()
    submission_process = Process(
        target=get_submissions_matrix, args=(all_pkgs, submissions_paths_block,
                                             n_readed_submissions,
                                             len_submissions, out_queue))
    submission_process.start()

    return submission_process, out_queue


def create_submissions_processes(submissions_paths, block_size, n_processors,
                                 all_pkgs, n_readed_submissions):
    out_queues = []
    submissions_processes = []
    len_submissions = len(submissions_paths)

    for index in range(n_processors - 1):
        submissions_paths_block = get_submissions_path_block(
            index, submissions_paths, block_size, n_processors)

        process_data = create_one_submission_process(
            all_pkgs, submissions_paths_block, n_readed_submissions,
            len_submissions)

        submission_process, out_queue = process_data

        out_queues.append(out_queue)
        submissions_processes.append(submission_process)

    return submissions_processes, out_queues


def get_popcon_submissions(all_pkgs, popcon_entries_path, n_processors):
    submissions_paths = get_submissions_paths(popcon_entries_path)

    manager = Manager()
    n_readed_submissions = manager.Value('i', 0)

    len_submissions = len(submissions_paths)
    block_size = int(len_submissions / n_processors)

    processes_data = create_submissions_processes(
        submissions_paths, block_size, n_processors, all_pkgs,
        n_readed_submissions)
    submissions_processes, out_queues = processes_data

    out_queue = Queue()
    submissions_paths_block = submissions_paths[:block_size]
    get_submissions_matrix(all_pkgs, submissions_paths_block,
                           n_readed_submissions, len_submissions, out_queue)

    submissions = [out_queue.get()]
    for out_queue in out_queues:
        submission = out_queue.get()
        submissions.append(submission)

    for submission_process in submissions_processes:
        submission_process.join()

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


def compress_file(output_folder, file_path):
    compressed_file_name = '{}.tar.xz'.format(file_path.split('.')[0])

    if os.path.exists(compressed_file_name):
        os.remove(compressed_file_name)

    tar = tarfile.open(compressed_file_name, 'w:xz')
    tar.add(file_path)
    tar.close()

    os.remove(file_path)


def save_clusters(clusters, output_folder):
    lines = []
    len_clusters = len(clusters)

    for index, cluster in enumerate(clusters):
        line = ';'.join([str(value) for value in cluster])
        lines.append(line)
        print_percentage(index + 1, len_clusters)

    with open(CLUSTERS_FILE, 'w') as text:
        text.write("\n".join(lines))

    compress_file(output_folder, CLUSTERS_FILE)


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

    with open(PKGS_CLUSTERS, 'w') as text:
        text.write("\n".join(lines))

    compress_file(output_folder, PKGS_CLUSTERS)


def move_compressed_file(output_folder, file_name):
    if not os.path.exists(output_folder + file_name):
        shutil.move(file_name, output_folder)


def get_sha256sum():
    files = [CLUSTERS_FILE_TAR, PKGS_CLUSTERS_TAR]

    sha256sum = ''
    for file_name in files:
        ifile = open(file_name, 'rb')
        content = ifile.read()
        ifile.close()

        checksum = hashlib.sha256(content).hexdigest()

        sha256sum += '{}  {}\n'.format(checksum, file_name)

    sha256sum = sha256sum[:-1]

    return sha256sum


def generate_inrelease_file(output_folder, gnupg_home):
    sha256sum = get_sha256sum()

    gpg = gnupg.GPG(gnupghome=gnupg_home)
    gpg.encoding = 'utf-8'

    signed_data = gpg.sign(sha256sum, clearsign=True)

    while len(signed_data.data) == 0:
        passphrase = getpass.getpass('GPG Passphrase: ')
        signed_data = gpg.sign(sha256sum, passphrase=passphrase,
                               clearsign=True)
        if len(signed_data.data) == 0:
            verbose_print('Wrong passphrase')

    with open(output_folder + INRELEASE_FILE, 'w') as ifile:
        ifile.write(signed_data.data.decode('utf-8'))


def remove_oldest_files(output_folder):
    files = [CLUSTERS_FILE_TAR, PKGS_CLUSTERS_TAR, INRELEASE_FILE]
    for file_name in files:
        if os.path.isfile(output_folder + file_name):
            os.remove(output_folder + file_name)


def save_data(all_pkgs, clusters, pkgs_clusters, output_folder, gnupg_home):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    remove_oldest_files(output_folder)

    verbose_print("Saving clusters.tar.xz")
    save_clusters(clusters, output_folder)

    verbose_print("Saving pkgs_clusters.tar.xz")
    save_pkgs_clusters(all_pkgs, pkgs_clusters, output_folder)

    verbose_print("Generating InRelease file")
    generate_inrelease_file(output_folder, gnupg_home)

    shutil.move(CLUSTERS_FILE_TAR, output_folder)
    shutil.move(PKGS_CLUSTERS_TAR, output_folder)
    finish_message = "Create clusters finished, files saved on: {}"
    print(finish_message.format(output_folder))


def generate_kmeans_data(n_clusters, random_state, n_processors, submissions):
    k_means = MiniBatchKMeans(n_clusters=n_clusters, init='k-means++',
                              random_state=random_state, batch_size=1000)
    k_means.fit(submissions)
    submissions_clusters = k_means.labels_.tolist()
    clusters = k_means.cluster_centers_.tolist()

    return clusters, submissions_clusters


def main(random_state, n_clusters, n_processors, popcon_entries_path,
         output_folder, gnupg_home):

    verbose_print("Loading all packages")
    all_pkgs = get_all_pkgs()

    verbose_print("Loading popcon submissions")
    submissions = get_popcon_submissions(all_pkgs, popcon_entries_path,
                                         n_processors)

    verbose_print("Discarding non popular packages")
    all_pkgs, submissions = discard_nonpupular_pkgs(all_pkgs, submissions)

    verbose_print("Filter little used packages")
    all_pkgs, submissions = filter_little_used_packages(all_pkgs, submissions)

    verbose_print("Creating KMeans data")
    data = generate_kmeans_data(n_clusters, random_state, n_processors,
                                submissions)
    clusters, submissions_clusters = data

    verbose_print("Creating packages clusters")
    pkgs_clusters = create_pkgs_clusters(all_pkgs, submissions,
                                         submissions_clusters, len(clusters))

    save_data(all_pkgs, clusters, pkgs_clusters, output_folder, gnupg_home)


def get_expand_folder_path(folder_path):
    expand_folder_path = os.path.expanduser(folder_path)
    expand_folder_path = os.path.abspath(expand_folder_path)

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

    default_gnupg_home = os.path.expanduser('~/.gnupg')
    parser.add_argument('-g', '--gnupg-home', type=str, metavar='',
                        default=default_gnupg_home, help='path of folder to '
                                                         'output data')

    parser.add_argument('-c', '--n_clusters', type=int, metavar='',
                        default=200, help='Number of clusters are been used')

    parser.add_argument('-p', '--n_processors', type=int, metavar='',
                        default=1, help='Number of processors to be used')

    parser.add_argument('-r', '--random_state', type=int, metavar='',
                        default=170, help='Number of processors to be used')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Disable recommendations when install a package '
                             'with apt')

    return parser


if __name__ == '__main__':
    parser = create_parser()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    args.output = get_expand_folder_path(args.output)
    args.popcon_entries_path = get_expand_folder_path(args.popcon_entries_path)
    args.gnupg_home = get_expand_folder_path(args.gnupg_home)

    VERBOSE = args.verbose

    if not os.path.exists(args.popcon_entries_path):
        verbose_print("Folder not exists: {}".format(args.popcon_entries_path))
        exit(1)

    main(args.random_state, args.n_clusters, args.n_processors,
         args.popcon_entries_path, args.output, args.gnupg_home)
