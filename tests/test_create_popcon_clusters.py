#!/usr/bin/env python

import unittest
import numpy as np

import create_popcon_clusters as cpc

class CreatePopconClustersTests(unittest.TestCase):

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
        all_pkgs = ['vim', 'vagrant', 'chef', 'python', 'ruby', 'git']
        popcon_entries = [['vim', 'chef', 'ruby'],
                          ['vagrant', 'python', 'ruby'],
                          ['vim', 'chef', 'python', 'git'],
                          ['vagrant', 'chef', 'python', 'ruby', 'git']]

        users_binary = [[1, 0, 1, 0, 1, 0],
                        [0, 1, 0, 1, 1, 0],
                        [1, 0, 1, 1, 0, 1],
                        [0, 1, 1, 1, 1, 1]]

        assert_all_pkgs_rate = [0.5, 0.5, 0.75, 0.75, 0.75, 0.5]

        all_pkgs_rate = cpc.get_all_pkgs_rate(users_binary)

        self.assertEqual(assert_all_pkgs_rate, all_pkgs_rate)
