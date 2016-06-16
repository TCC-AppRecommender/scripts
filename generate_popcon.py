#!/usr/bin/env python

import commands
import random
import sys
import re


SUBMISSION_SIFIX = 'popcon'


def get_submission_id(submission_number):
    submission_str = str(submission_number)[::-1]

    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'x', 'w',
                'y', 'z']
    alphabet_index = 0

    submission_id = ""
    for index, character in enumerate(submission_str):
        submission_id = alphabet[index] + submission_id
        submission_id = character + submission_id

    submission_id = submission_id + SUBMISSION_SIFIX

    return submission_id


def get_header_message(actual_time, submission_id):
    header_message = "POPULARITY-CONTEST-0 TIME:{} ID:{}popcon ARCH:amd64" \
                     " POPCONVER: VENDOR:Debian"
    header_message = header_message.format(actual_time, submission_id)

    return header_message


def get_pkgs_time(pkgs, actual_time):
    pkgs_time = {}
    for pkg, _ in pkgs.iteritems():
        last_time = random.randint(1, actual_time)
        first_time = random.randint(1, last_time)

        pkgs_time[pkg] = (first_time, last_time)

    return pkgs_time


def save_submission(header_message, pkgs, pkgs_time, file_path):
    with open(file_path, 'w') as text:
        text.write(header_message + '\n')

        line = "{} {} {} {}\n"
        for pkg, path in pkgs.iteritems():
            text.write(line.format(pkgs_time[pkg][0], pkgs_time[pkg][1],
                                   pkg, path))


def create_submission(pkgs, actual_time, submission_number, folder_path):
    submission_id = get_submission_id(submission_number)
    header_message = get_header_message(actual_time, submission_id)
    pkgs_time = get_pkgs_time(pkgs, actual_time)
    file_path = "{}{}".format(folder_path, submission_id)
    save_submission(header_message, pkgs, pkgs_time, file_path)


def get_pkgs(popcon_submission_path):
    match_pkg = re.compile(r'^\d+\s\d+\s([^\/\s]+)(?!.*<NOFILES>)', re.MULTILINE)
    match_path = re.compile(r'^\d+\s\d+\s[^\/\s]+\s([^\s]+)', re.MULTILINE)

    ifile = open(popcon_submission_path, 'r')
    text = ifile.read()
    ifile.close()

    pkgs = match_pkg.findall(text)
    paths = match_path.findall(text)

    pkgs_path = {pkg: path for pkg, path in zip(pkgs, paths)}

    return pkgs_path


def filter_pkgs(pkgs):
    filtered_pkgs = {}

    for pkg, path in pkgs.iteritems():
        number = random.randint(0, 100)
        if number > 50:
            filtered_pkgs[pkg] = path

    return filtered_pkgs


def run(popcon_submission_path, number_of_submissions, folder_path):
    actual_time = random.randint(100000000, 1000000000)
    pkgs = get_pkgs(popcon_submission_path)

    for submission_number in range(1, number_of_submissions + 1):
        filtered_pkgs = filter_pkgs(pkgs)
        create_submission(filtered_pkgs, actual_time, submission_number,
                          folder_path)


def usage():
    usage_message = "USAGE: {} [popcon_submission_path] " \
                    "[number_of_submissions] [folder_to_save]"
    print usage_message.format(sys.argv[0])


if __name__ == '__main__':
    try:
        folder_path = sys.argv[3]
        popcon_submission_path = sys.argv[1]
        number_of_submissions = int(sys.argv[2])
        run(popcon_submission_path, number_of_submissions, folder_path)
    except:
        usage()
        sys.exit()
