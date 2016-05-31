#!/usr/bin/env python

import os
import shutil
import unittest
import create_popcon_clusters as cpc


class CreatePopconClustersTests(unittest.TestCase):

    def create_popcon_file(self, file_path, pkgs):
        popcon_header = 'POPULARITY-CONTEST-0 TIME:370542026 ID:1popcon' \
                        'ARCH:amd64 POPCONVER: VENDOR:Debian\n'

        with open(file_path, 'wb') as text:
            text.write(popcon_header)
            for pkg in pkgs:
                line = '15019500 154428337 {0} /usr/bin/{0}\n'.format(pkg)
                text.write(line)
            text.write('END-POPULARITY-CONTEST-0 TIME:1464009355\n')

    def test_get_users_binary(self):
        all_pkgs = ['vim', 'vagrant', 'chef', 'python', 'ruby', 'git']
        popcon_entries = [['vim', 'chef', 'ruby'],
                          ['vagrant', 'python', 'ruby'],
                          ['vim', 'chef', 'python', 'git'],
                          ['vagrant', 'chef', 'python', 'ruby', 'git']]

        assert_users_binary = [[1, 0, 1, 0, 1, 0],
                               [0, 1, 0, 1, 1, 0],
                               [1, 0, 1, 1, 0, 1],
                               [0, 1, 1, 1, 1, 1]]

        users_binary = cpc.get_users_binary(all_pkgs, popcon_entries)

        self.assertEqual(assert_users_binary, users_binary)

    def test_get_all_pkgs_rate(self):
        users_binary = [[1, 0, 1, 0, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [1, 0, 1, 1, 0, 1],
                        [0, 1, 1, 1, 1, 1]]

        assert_all_pkgs_rate = [0.5, 0.5, 0.75, 0.75, 0.75, 0.5]

        all_pkgs_rate = cpc.get_all_pkgs_rate(users_binary)

        self.assertEqual(assert_all_pkgs_rate, all_pkgs_rate)

    def test_get_filtered_users_pkgs(self):
        all_pkgs = ['vim', 'vagrant', 'chef', 'python', 'ruby', 'git']
        users_pkgs = [['vim', 'chef', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vagrant', 'python', 'ruby'],
                      ['vim', 'chef', 'python', 'ruby'],
                      ['vagrant', 'chef', 'python', 'ruby', 'git']]

        users_binary = [[1, 0, 1, 0, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [1, 0, 1, 1, 1, 0],
                        [0, 1, 1, 1, 1, 1]]

        assert_filtered_users_pkgs = [['vim', 'chef', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vagrant', 'python', 'ruby'],
                                      ['vim', 'chef', 'python', 'ruby'],
                                      ['vagrant', 'chef', 'python', 'ruby']]

        filtered_users_pkgs = cpc.get_filtered_users_pkgs(all_pkgs,
                                                          users_pkgs,
                                                          users_binary)

        self.assertEqual(assert_filtered_users_pkgs, filtered_users_pkgs)

    def test_get_all_pkgs(self):
        popcon_entries = [['vim', 'chef', 'ruby'],
                          ['vagrant', 'python', 'ruby'],
                          ['vim', 'chef', 'python', 'git'],
                          ['vagrant', 'chef', 'python', 'ruby', 'git']]

        assert_all_pkgs = ['vim', 'chef', 'ruby', 'vagrant', 'python', 'git']

        all_pkgs = cpc.get_all_pkgs(popcon_entries)

        self.assertEqual(sorted(assert_all_pkgs), sorted(all_pkgs))

    def test_read_popcon_file(self):
        file_path = '1apopcon'
        pkgs = ['vim', 'git', 'ruby', 'python', 'libruby', 'pythondoc']
        self.create_popcon_file(file_path, pkgs)

        assert_popcon_entry = ['git', 'python', 'ruby', 'vim']

        popcon_entry = cpc.read_popcon_file(file_path)
        os.remove(file_path)

        self.assertEqual(assert_popcon_entry, popcon_entry)

    def test_get_popcon_files(self):
        popcon_entries_path = 'popcon_entries_for_tests/'
        popcon_folders = [popcon_entries_path + '1a/',
                          popcon_entries_path + '2a/']
        popcon_files_path = [popcon_folders[0] + '1a1popcon',
                             popcon_folders[0] + '1a2popcon',
                             popcon_folders[0] + '1a3popcon',
                             popcon_folders[1] + '2a1popcon']

        if os.path.exists(popcon_entries_path):
            shutil.rmtree(popcon_entries_path)
        os.mkdir(popcon_entries_path)
        for popcon_folder in popcon_folders:
            os.mkdir(popcon_folder)
        for popcon_file_path in popcon_files_path:
            popcon_file = open(popcon_file_path, 'a')
            popcon_file.close()

        popcon_files = cpc.get_popcon_files(popcon_entries_path)
        shutil.rmtree(popcon_entries_path)

        self.assertEqual(sorted(popcon_files_path), sorted(popcon_files))

    def test_get_popcon_entries(self):
        popcon_entries_path = 'popcon_entries_for_tests/'
        popcon_folders = [popcon_entries_path + '1a/',
                          popcon_entries_path + '2a/']
        popcon_files_path = [popcon_folders[0] + '1a1popcon',
                             popcon_folders[0] + '1a2popcon',
                             popcon_folders[0] + '1a3popcon',
                             popcon_folders[1] + '2a1popcon']

        file_pkgs = {popcon_files_path[0]: ['vim', 'git'],
                     popcon_files_path[1]: ['vagrant', 'ruby'],
                     popcon_files_path[2]: ['python', 'ruby'],
                     popcon_files_path[3]: ['git', 'ruby']}

        assert_popcon_entries = [['ruby', 'vagrant'],
                                 ['git', 'vim'],
                                 ['python', 'ruby'],
                                 ['git', 'ruby']]

        if os.path.exists(popcon_entries_path):
            shutil.rmtree(popcon_entries_path)
        os.mkdir(popcon_entries_path)
        for popcon_folder in popcon_folders:
            os.mkdir(popcon_folder)
        for file_path in popcon_files_path:
            self.create_popcon_file(file_path, file_pkgs[file_path])

        popcon_entries = cpc.get_popcon_entries(popcon_entries_path)
        shutil.rmtree(popcon_entries_path)

        self.assertEqual(assert_popcon_entries, popcon_entries)
