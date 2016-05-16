#!/usr/bin/env python

import commands
import random
import sys


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


def create_submission(pkgs, actual_time, submission_id, folder_path):
    header_message = get_header_message(actual_time, submission_id)
    pkgs_time = get_pkgs_time(pkgs, actual_time)
    file_path = "{}{}popcon".format(folder_path, submission_id)
    save_submission(header_message, pkgs, pkgs_time, file_path)


def get_pkgs():
    lines = commands.getoutput('./popularity-contest').splitlines()
    pkgs = {line.split()[-2]: line.split()[-1] for line in lines[1:]}

    return pkgs

def filter_pkgs(pkgs):
    filtered_pkgs = {}

    for pkg, path in pkgs.iteritems():
        number = random.randint(0, 100)
        if number > 50:
            filtered_pkgs[pkg] = path

    return filtered_pkgs

def run(number_of_submissions, folder_path):
    actual_time = random.randint(100000000, 1000000000)
    pkgs = get_pkgs()

    for submission_id in range(1, number_of_submissions + 1):
        pkgs = filter_pkgs(pkgs)
        create_submission(pkgs, actual_time, submission_id, folder_path)


def usage():
    print("USAGE: %s [number_of_submissions] [folder_path]" % (sys.argv[0]))


if __name__ == '__main__':
    folder_path = sys.argv[2]
    number_of_submissions = int(sys.argv[1])
    run(number_of_submissions, folder_path)
    # try:
    #     folder_path = sys.argv[2]
    #     number_of_submissions = int(sys.argv[1])
    #     run(number_of_submissions, folder_path)
    # except:
    #     usage()
    #     sys.exit()

