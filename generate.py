#!/usr/bin/env python

import random
import commands


def get_header_message(actual_time, submission_id):
  header_message = "POPULARITY-CONTEST-0 TIME:{} ID:{} ARCH:amd64" \
                   " POPCONVER: VENDOR:Debian"
  header_message = header_message.format(actual_time, submission_id)

  return header_message


def get_pkgs_time(actual_time):
  pkgs = commands.getoutput('apt-mark showmanual').splitlines()
  pkgs_time = {}
  for pkg in pkgs:
    last_time = random.randint(1, actual_time)
    first_time = random.randint(1, last_time)

    pkgs_time[pkg] = (first_time, last_time)

  return pkgs_time


def save_submission(pkgs_time, file_path):
  with open(file_path, 'w') as text:
    text.write(header_message + '\n')

    line = "{} {} {}\n"
    for pkg, times in pkgs_time.iteritems():
      text.write(line.format(times[0], times[1], pkg))


def create_submission(actual_time, submission_id, folder_path):
  header_message = get_header_message(actual_time, submission_id)
  pkgs_time = get_pkgs_time(actual_time)
  file_path = "{}{}".format(folder_path, submission_id)
  save_submission(pkgs_time, file_path)


if __name__ == '__main__':
  folder_path = '/home/luciano/Documents/unb/tcc/popcon_generate_data/'
  actual_time = random.randint(100000000, 1000000000)
  create_submission(actual_time, 1, folder_path)
