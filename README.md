# folder_syncv

<!-- [![Built Status](https://api.cirrus-ci.com/github/george-cm/folder-syncv.svg?branch=main)](https://cirrus-ci.com/github/george-cm/folder_syncv) -->

[![Github Actions Workflow main branch](https://github.com/george-cm/folder-syncv/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/george-cm/folder-syncv/actions/workflows/ci.yml/badge.svg?branch=main)
[![ReadTheDocs](https://readthedocs.org/projects/folder-syncv/badge/?version=latest)](https://folder-syncv.readthedocs.io/en/latest/)
[![Coverage Status](https://coveralls.io/repos/github/george-cm/folder-syncv/badge.svg?branch=main&kill_cache=1)](https://coveralls.io/github/george-cm/folder-syncv?branch=main)

[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

> CLI program to synchronize one-way a source folder to a replica.

A very unoptimized, synchronous implementation of program that synchronizes two folders: source and replica.

> **WARNING**
>
> Use at your own risk!
> The program deletes or overwrites all files and folders in the replica folder if they are not in the source folder or are different.
>
> If you pass a REPLICA folder with files or folders in it they will be **DELETED!!!**

The program maintains a full, identical copy of the source folder at replica folder.

Synchronization is one-way: after the synchronization content of the replica folder exactly matches content of the source folder.

Synchronization is performed periodically.

File creation/copying/removal operations are logged to a file and to the console output.

Folder paths, synchronization interval and log file path should be provided using command line arguments.

## Installation

Install in a virtual environment using:

```sh
python -m pip install "git+https://github.com/george-cm/folder-syncv.git#egg=folder-syncv"
```

Tested on Ubuntu 22.04 in Python 3.10 and Python 3.11.

Might possibly work on Windows and Mac but it's not tested.

In case you are new to Python and virtual environments here's an excelent primer from the nice poeple of Real Python: [Python Virtual Environments: A Primer][def].

## Usage

```sh
syncv [OPTIONS] SOURCE REPLICA

  Main entrypoint

Options:
  --syncinterval INTEGER RANGE    Seconds bettwen synchronizations. min = 0
                                  (sync only once),  max = 2678400 (31 days).
                                  Default = 0  [0<=x<=2678400; required]
  --logfile PATH                  path to log file  [required]
  --loglevel [debug|info|warn|error|critical]
                                  Default = info
  --version                       Show the version and exit.
  -h, --help                      Show this message and exit.
```

<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see <https://pyscaffold.org/>.

[def]: https://realpython.com/python-virtual-environments-a-primer/ "Python Virtual Environments: A Primer"
