# folder_syncv

<!-- [![Built Status](https://api.cirrus-ci.com/github/george-cm/folder-syncv.svg?branch=main)](https://cirrus-ci.com/github/george-cm/folder_syncv) -->
[![Github Actions Workflow main branch](https://github.com/george-cm/folder-syncv/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/george-cm/folder-syncv/actions/workflows/ci.yml/badge.svg?branch=main)
[![ReadTheDocs](https://readthedocs.org/projects/folder-syncv/badge/?version=latest)](https://folder-syncv.readthedocs.io/en/stable/)
[![Coverage Status](https://coveralls.io/repos/github/george-cm/folder-syncv/badge.svg?branch=main)](https://coveralls.io/github/george-cm/folder-syncv?branch=main)

[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

> CLI program to synchronize one-way a source folder to a replica.

A program that synchronizes two folders: source and replica. The program maintains a full, identical copy of the source folder at replica folder.

Synchronization is one-way: after the synchronization content of the replica folder exactly matches content of the source folder.

Synchronization is performed periodically.

File creation/copying/removal operations are logged to a file and to the console output.

Folder paths, synchronization interval and log file path should be provided using the command line arguments.

<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see <https://pyscaffold.org/>.
