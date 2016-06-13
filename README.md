Scripts
=======

This repository contains the scripts used to help the work with
AppRecommender.

The following explains each script


popularity-contest
------------------

Its the same script of package popularity-contest, this script is in this
repository to dont needs install the popularity-contest, because to use this
script with the package needs run with sudo

Usage: popularity-contest


generate\_popcon.py
-------------------

Script to generate the fake popularity-contest submissions, this script runs
the popularity-contest for the user and use the lines of the user submission
to create multiples fake submissions.

Usage: generate\_popcon.py [number\_of\_submissions] [folder_to_save]


create\_popcon\_clusters.py
---------------------------

This script is used to separate the popularity-contest submissions in
clusters, this clustarization its made by the packages in each submission.

Usage:
create\_popcon\_clusters.py [popcon-entries\_path] [random\_state] [n\_clusters] [n\_processors]

[options]
  popcon-entries\_path - Its the path of folder with the popularity-contest
                         submissions
  random\_state - Its a number of random\_state of KMeans
  n\_clusters   - Its the number of clusters are been used

        usage = "Usage: {} [popcon-entries_path] [random_state] "\
                "[n_clusters] [n_processors]"
        print usage.format(sys.argv[0])
        print "\n[options]"
        print "  popcon-entries_path - Its the path of folder with the"
        print "                        popularity-contest submissions"
        print "  random_state - Its a number of random_state of KMeans"
        print "  n_clusters   - Its the number of clusters are been used"
        print "  n_processors - Its the number of processors to be used"

send\_popcon\_entries.sh
------------------------

Use this script to send the popularity-contest for an another folder using
the popularity-contest folder template, like this exemple:

  - Files: 1a2b, 1a3b, 2a2b, 2a3b
  - Folders: 1a, 2a
  - Files path: 1a/1a2b, 1a/1a3b, 2a/2a2b, 2a/3a4b

Usage: send\_popcon\_entries.sh [actual\_submissions\_folder] [destiny_submissions_folder]


unzip\_targz.sh
---------------
Script to unzip all tar.gz in a folder, and remove the tar.gz files

Usage: ./unzip\_targz.sh [folder\_with\_targz]
