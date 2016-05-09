#!/usr/bin/env python

import random
import commands


def get_header_message(actual_time, submission_id):
    header_message = "POPULARITY-CONTEST-0 TIME:{} ID:{} ARCH:amd64" \
                     " POPCONVER: VENDOR:Debian"
    header_message = header_message.format(actual_time, submission_id)

    return header_message


def get_pkgs_time(pkgs, actual_time):
    pkgs_time = {}
    for pkg in pkgs:
        last_time = random.randint(1, actual_time)
        first_time = random.randint(1, last_time)

        pkgs_time[pkg] = (first_time, last_time)

    return pkgs_time


def save_submission(header_message, pkgs_time, file_path):
    with open(file_path, 'w') as text:
        text.write(header_message + '\n')

        line = "{} {} {}\n"
        for pkg, times in pkgs_time.iteritems():
            text.write(line.format(times[0], times[1], pkg))


def create_submission(pkgs, actual_time, submission_id, folder_path):
    header_message = get_header_message(actual_time, submission_id)
    pkgs_time = get_pkgs_time(pkgs, actual_time)
    file_path = "{}{}.txt".format(folder_path, submission_id)
    save_submission(header_message, pkgs_time, file_path)


def run(number_of_submissions):
    folder_path = '/home/luciano/Documents/unb/tcc/popcon_generate_data/'
    actual_time = random.randint(100000000, 1000000000)
    pkgs = commands.getoutput('apt-mark showmanual').splitlines()

    for submission_id in range(1, number_of_submissions + 1):
        create_submission(pkgs, actual_time, submission_id, folder_path)

if __name__ == '__main__':
    run(10)
