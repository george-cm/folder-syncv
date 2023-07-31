import random
import string
from datetime import datetime, timedelta
from hashlib import md5
from os import utime
from pathlib import Path
from shutil import copy2

import pytest

from folder_syncv.syncv import (
    ExpectedFileIsAFolder,
    compute_hash,
    is_file_in_other,
    is_file_in_other_as_folder,
    is_file_in_other_modified,
    is_folder_in_other_as_file,
    is_folder_in_other_as_folder,
    setup_logging,
    sync_folder,
    sync_replica_to_source,
    sync_source_to_replica,
)

__author__ = "George Murga"
__copyright__ = "George Murga"
__license__ = "MIT"


def create_random_string(length: int) -> str:
    return "".join(random.choice(string.printable) for i in range(length))


def test_setup_logging_logfile_parent_doesnt_exist(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        setup_logging(loglevel="debug", logfile=tmp_path / "subpath1/syncv.log")


def test_compute_hash_non_empty_file(tmp_path: Path) -> None:
    s: str = create_random_string(10_000)
    valid_hash: str = md5(s.encode(encoding="utf-8")).hexdigest()
    temp_file: Path = tmp_path / "tmp.txt"
    with temp_file.open("w", encoding="utf-8") as f:
        f.write(s)
    computed_hash = compute_hash(temp_file)
    assert computed_hash == valid_hash


def test_compute_hash_empty_file(tmp_path: Path) -> None:
    s: str = ""
    valid_hash: str = md5(s.encode(encoding="utf-8")).hexdigest()
    temp_file: Path = tmp_path / "tmp.txt"
    with temp_file.open("w", encoding="utf-8") as f:
        f.write(s)
    computed_hash = compute_hash(temp_file)
    assert computed_hash == valid_hash


def test_is_file_in_other_modified_file_not_in_other(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_path.mkdir(parents=True)
    destination_path = tmp_path / "destination"
    destination_path.mkdir(parents=True)
    source_file: Path = source_path / "dummy.txt"
    with source_file.open("w", encoding="utf-8") as f:
        f.write("")
    with pytest.raises(FileNotFoundError):
        is_file_in_other_modified(source_file, source_path, destination_path)


def test_is_file_in_other_modified_file_in_other_same_mtime(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    # source_path.mkdir(parents=True)
    source_file_path: Path = source_path / "level1/level2/level3"
    source_file_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    # destination_path.mkdir(parents=True)
    destination_file_path: Path = destination_path / "level1/level2/level3"
    destination_file_path.mkdir(parents=True)

    source_file: Path = source_file_path / "dummy.txt"

    with source_file.open("w", encoding="utf-8") as f:
        f.write("")

    destination_file: Path = Path(copy2(source_file, destination_file_path))
    # print(f" {source_file.stat().st_mtime=} - {destination_file.stat().st_mtime=}")
    assert source_file.stat().st_mtime == destination_file.stat().st_mtime
    assert is_file_in_other_modified(source_file, source_path, destination_path) is False


def test_is_file_in_other_modified_file_in_other_different_mtime_same_content(
    tmp_path: Path,
) -> None:
    source_path: Path = tmp_path / "source"
    source_file_path: Path = source_path / "level1/level2/level3"
    source_file_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_file_path: Path = destination_path / "level1/level2/level3"
    destination_file_path.mkdir(parents=True)

    source_file: Path = source_file_path / "dummy.txt"

    with source_file.open("w", encoding="utf-8") as f:
        f.write(create_random_string(100))

    destination_file: Path = Path(copy2(source_file, destination_file_path))
    utime(
        destination_file,
        (
            destination_file.stat().st_ctime,
            (timedelta(days=1) + datetime.today()).timestamp(),
        ),
    )
    # print(f" {source_file.stat().st_mtime=} - {destination_file.stat().st_mtime=}")
    assert source_file.stat().st_mtime != destination_file.stat().st_mtime
    assert is_file_in_other_modified(source_file, source_path, destination_path) is False


def test_is_file_in_other_modified_file_in_other_different_mtime_different_content(
    tmp_path: Path,
) -> None:
    source_path: Path = tmp_path / "source"
    source_file_path: Path = source_path / "level1/level2/level3"
    source_file_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_file_path: Path = destination_path / "level1/level2/level3"
    destination_file_path.mkdir(parents=True)

    source_file: Path = source_file_path / "dummy.txt"

    with source_file.open("w", encoding="utf-8") as f:
        f.write(create_random_string(100))

    destination_file: Path = Path(copy2(source_file, destination_file_path))
    with destination_file.open("w", encoding="utf-8") as f2:
        f2.write(create_random_string(50))

    utime(
        destination_file,
        (
            destination_file.stat().st_ctime,
            (timedelta(days=1) + datetime.today()).timestamp(),
        ),
    )
    # print(f" {source_file.stat().st_mtime=} - {destination_file.stat().st_mtime=}")
    assert source_file.stat().st_mtime != destination_file.stat().st_mtime
    assert is_file_in_other_modified(source_file, source_path, destination_path) is True


def test_is_file_in_other_not_in_ohter(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_path.mkdir(parents=True)
    source_file = source_path / "test.txt"
    with source_file.open("w", encoding="utf-8") as f:
        f.write("")
    destination_path: Path = tmp_path / "destination"
    destination_path.mkdir(parents=True)
    assert is_file_in_other(source_file, source_path, destination_path) is False


def test_is_file_in_other_in_ohter_as_file(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_path.mkdir(parents=True)
    source_file = source_path / "test.txt"
    with source_file.open("w", encoding="utf-8") as f:
        f.write("")
    destination_path: Path = tmp_path / "destination"
    destination_path.mkdir(parents=True)
    copy2(source_file, destination_path)
    assert is_file_in_other(source_file, source_path, destination_path) is True


def test_is_file_in_other_in_ohter_as_folder(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_path.mkdir(parents=True)
    source_file = source_path / "test.txt"
    with source_file.open("w", encoding="utf-8") as f:
        f.write("")
    destination_path: Path = tmp_path / "destination"
    destination_folder: Path = destination_path / "test.txt"
    destination_folder.mkdir(parents=True)
    with pytest.raises(ExpectedFileIsAFolder):
        is_file_in_other(source_file, source_path, destination_path)


def test_is_file_in_other_as_folder_not_in_ohter(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_path.mkdir(parents=True)
    source_file = source_path / "test.txt"
    with source_file.open("w", encoding="utf-8") as f:
        f.write("")
    destination_path: Path = tmp_path / "destination"
    destination_path.mkdir(parents=True)
    assert is_file_in_other_as_folder(source_file, source_path, destination_path) is False


def test_is_file_in_other_as_folder_is_in_other_as_file(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_path.mkdir(parents=True)
    source_file = source_path / "test.txt"
    with source_file.open("w", encoding="utf-8") as f:
        f.write("")
    destination_path: Path = tmp_path / "destination"
    destination_path.mkdir(parents=True)
    copy2(source_file, destination_path)
    assert is_file_in_other_as_folder(source_file, source_path, destination_path) is False


def test_is_file_in_other_as_folder_is_in_other_as_folder(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_path.mkdir(parents=True)
    source_file = source_path / "test.txt"
    with source_file.open("w", encoding="utf-8") as f:
        f.write("")
    destination_path: Path = tmp_path / "destination"
    destination_folder: Path = destination_path / "test.txt"
    destination_folder.mkdir(parents=True)
    assert is_file_in_other_as_folder(source_file, source_path, destination_path) is True


def test_is_folder_in_other_as_file_not_in_other(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2"
    destination_folder_path.mkdir(parents=True)

    assert is_folder_in_other_as_file(source_folder_path, source_path, destination_path) is False


def test_is_folder_in_other_as_file_is_in_other_as_folder(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2/level3"
    destination_folder_path.mkdir(parents=True)

    assert is_folder_in_other_as_file(source_folder_path, source_path, destination_path) is False


def test_is_folder_in_other_as_file_is_in_other_as_file(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2"
    destination_folder_path.mkdir(parents=True)
    destination_file_path = destination_folder_path / "level3"
    with destination_file_path.open("w", encoding="utf-8") as f:
        f.write("")

    assert is_folder_in_other_as_file(source_folder_path, source_path, destination_path) is True


def test_is_folder_in_other_as_folder_not_in_other(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2"
    destination_folder_path.mkdir(parents=True)

    assert is_folder_in_other_as_folder(source_folder_path, source_path, destination_path) is False


def test_is_folder_in_other_as_folder_is_in_other_as_folder(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2/level3"
    destination_folder_path.mkdir(parents=True)

    assert is_folder_in_other_as_folder(source_folder_path, source_path, destination_path) is True


def test_is_folder_in_other_as_folder_is_in_other_as_file(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2"
    destination_folder_path.mkdir(parents=True)
    destination_file_path = destination_folder_path / "level3"
    with destination_file_path.open("w", encoding="utf-8") as f:
        f.write("")

    assert is_folder_in_other_as_folder(source_folder_path, source_path, destination_path) is False


def test_sync_source_to_replica_empty_replica(tmp_path: Path) -> None:
    source: Path = tmp_path / "source"
    l1: Path = source / "l1/l11/l111"
    l1.mkdir(parents=True)
    (l1 / "file111.txt").touch()
    (l1.parent / "file11.txt").touch()
    (l1.parent.parent / "file1.txt").touch()
    l2: Path = source / "l2/l22"
    l2.mkdir(parents=True)
    (l2 / "file22.txt").touch()
    (l2.parent / "file2.txt").touch()
    l3: Path = source / "l3"
    l3.mkdir(parents=True)
    (l3 / "file3.txt").touch()
    (source / "file0.txt").touch()

    destination: Path = tmp_path / "destination"
    destination.mkdir(parents=True)

    (files_count, folders_count, files_copied, files_updated, folders_copied, folders_deleted) = sync_source_to_replica(source, destination)
    assert files_count == 1
    assert folders_count == 3
    assert files_copied == 1
    assert files_updated == 0
    assert folders_copied == 3
    assert folders_deleted == 0
    source_files_and_folders: set[str] = set(x.as_posix().replace(source.as_posix(), "") for x in source.iterdir())
    destination_files_and_folders: set[str] = set(x.as_posix().replace(destination.as_posix(), "") for x in destination.iterdir())
    assert source_files_and_folders == destination_files_and_folders


def test_sync_source_to_replica_nonempty_replica(tmp_path: Path) -> None:
    source: Path = tmp_path / "source"
    l1: Path = source / "l1/l11/l111"
    l1.mkdir(parents=True)
    (l1 / "file111.txt").touch()
    (l1.parent / "file11.txt").touch()
    (l1.parent.parent / "file1.txt").touch()
    l2: Path = source / "l2/l22"
    l2.mkdir(parents=True)
    (l2 / "file22.txt").touch()
    (l2.parent / "file2.txt").touch()
    l3: Path = source / "l3"
    l3.mkdir(parents=True)
    (l3 / "file3.txt").touch()
    (source / "file0.txt").touch()

    destination: Path = tmp_path / "destination"
    destination.mkdir(parents=True)
    d1: Path = destination / "d1"
    d1.mkdir(parents=True)
    dl1: Path = destination / "l1"
    dl1.mkdir(parents=True)
    dl3: Path = destination / "l3/file3.txt"
    dl3.mkdir(parents=True)
    (d1 / "d1_file.txt").touch()
    (destination / "d_file.txt").touch()
    (destination / "file0.txt").touch()
    (destination / l3).touch()

    print("source")
    for e in source.rglob("*"):
        print(e.as_posix())
    print("destination")
    for e in destination.rglob("*"):
        print(e.as_posix())

    (files_count, folders_count, files_copied, files_updated, folders_copied, folders_deleted) = sync_source_to_replica(source, destination)
    assert files_count == 3
    assert folders_count == 4
    assert files_copied == 2
    assert files_updated == 0
    assert folders_copied == 2
    assert folders_deleted == 1
    source_files_and_folders: set[str] = set(x.as_posix().replace(source.as_posix(), "") for x in source.rglob("*"))
    destination_files_and_folders: set[str] = set(x.as_posix().replace(destination.as_posix(), "") for x in destination.rglob("*"))

    print(f"{source_files_and_folders=}")
    print(f"{destination_files_and_folders=}")
    print(f"{destination_files_and_folders - source_files_and_folders=}")
    assert destination_files_and_folders - source_files_and_folders == {
        "/d1",
        "/d1/d1_file.txt",
        "/d_file.txt",
    }


def test_sync_replica_to_source_empty_replica(tmp_path: Path) -> None:
    source: Path = tmp_path / "source"
    l1: Path = source / "l1/l11/l111"
    l1.mkdir(parents=True)
    (l1 / "file111.txt").touch()
    (l1.parent / "file11.txt").touch()
    (l1.parent.parent / "file1.txt").touch()
    l2: Path = source / "l2/l22"
    l2.mkdir(parents=True)
    (l2 / "file22.txt").touch()
    (l2.parent / "file2.txt").touch()
    l3: Path = source / "l3"
    l3.mkdir(parents=True)
    (l3 / "file3.txt").touch()
    (source / "file0.txt").touch()

    destination: Path = tmp_path / "destination"
    destination.mkdir(parents=True)
    d1: Path = destination / "d1"
    d1.mkdir(parents=True)
    dl1: Path = destination / "l1"
    dl1.mkdir(parents=True)
    (d1 / "d1_file.txt").touch()
    (destination / "d_file.txt").touch()
    (destination / l3).touch()

    print("source")
    for e in source.rglob("*"):
        print(e.as_posix())
    print("destination")
    for e in destination.rglob("*"):
        print(e.as_posix())

    files_deleted, folders_deleted = sync_replica_to_source(source, destination)
    assert files_deleted == 1
    assert folders_deleted == 1
    # source_files_and_folders: set[str] = set(x.as_posix().replace(source.as_posix(), "") for x in source.rglob("*"))
    destination_files_and_folders: set[str] = set(x.as_posix().replace(destination.as_posix(), "") for x in destination.rglob("*"))

    print(f"{destination_files_and_folders=}")
    assert destination_files_and_folders == {"/l1"}


def test_sync_folder(tmp_path: Path) -> None:
    source: Path = tmp_path / "source"
    l1: Path = source / "l1/l11/l111"
    l1.mkdir(parents=True)
    (l1 / "file111.txt").touch()
    (l1.parent / "file11.txt").touch()
    (l1.parent.parent / "file1.txt").touch()
    l2: Path = source / "l2/l22"
    l2.mkdir(parents=True)
    (l2 / "file22.txt").touch()
    (l2.parent / "file2.txt").touch()
    l3: Path = source / "l3"
    l3.mkdir(parents=True)
    (l3 / "file3.txt").touch()
    (source / "file0.txt").touch()

    destination: Path = tmp_path / "destination"
    destination.mkdir(parents=True)
    d1: Path = destination / "d1"
    d1.mkdir(parents=True)
    dl1: Path = destination / "l1"
    dl1.mkdir(parents=True)
    (d1 / "d1_file.txt").touch()
    (destination / "d_file.txt").touch()
    (destination / l3).touch()

    print("source")
    for e in source.rglob("*"):
        print(e.as_posix())
    print("destination")
    for e in destination.rglob("*"):
        print(e.as_posix())

    sync_folder(source, destination, 0, tmp_path / "tmp.log", "debug")

    source_files_and_folders: set[str] = set(x.as_posix().replace(source.as_posix(), "") for x in source.rglob("*"))
    destination_files_and_folders: set[str] = set(x.as_posix().replace(destination.as_posix(), "") for x in destination.rglob("*"))

    print(f"{source_files_and_folders=}")
    print(f"{destination_files_and_folders=}")
    print(f"{destination_files_and_folders - source_files_and_folders=}")
    assert destination_files_and_folders == source_files_and_folders
