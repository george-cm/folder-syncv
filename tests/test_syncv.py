import random
import string
from datetime import datetime, timedelta
from hashlib import md5
from os import utime
from pathlib import Path
from shutil import copy2

import pytest

from folder_syncv.syncv import (
    compute_hash,
    is_file_in_other,
    is_folder_in_other_as_file,
    is_folder_in_other_as_folder,
    setup_logging,
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


def test_is_file_in_other_file_not_in_other(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_path.mkdir(parents=True)
    destination_path = tmp_path / "destination"
    destination_path.mkdir(parents=True)
    source_file: Path = source_path / "dummy.txt"
    with source_file.open("w", encoding="utf-8") as f:
        f.write("")
    assert is_file_in_other(source_file, source_path, destination_path) is False


def test_is_file_in_other_file_in_other_same_mtime(tmp_path: Path) -> None:
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
    assert is_file_in_other(source_file, source_path, destination_path) is True


def test_is_file_in_other_file_in_other_different_mtime_same_content(
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
    assert is_file_in_other(source_file, source_path, destination_path) is True


def test_is_file_in_other_file_in_other_different_mtime_different_content(
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
    assert is_file_in_other(source_file, source_path, destination_path) is False


def test_is_folder_in_other_as_file_not_in_other(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2"
    destination_folder_path.mkdir(parents=True)

    assert (
        is_folder_in_other_as_file(source_folder_path, source_path, destination_path)
        is False
    )


def test_is_folder_in_other_as_file_is_in_other_as_folder(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2/level3"
    destination_folder_path.mkdir(parents=True)

    assert (
        is_folder_in_other_as_file(source_folder_path, source_path, destination_path)
        is False
    )


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

    assert (
        is_folder_in_other_as_file(source_folder_path, source_path, destination_path)
        is True
    )


def test_is_folder_in_other_as_folder_not_in_other(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2"
    destination_folder_path.mkdir(parents=True)

    assert (
        is_folder_in_other_as_folder(source_folder_path, source_path, destination_path)
        is False
    )


def test_is_folder_in_other_as_folder_is_in_other_as_folder(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "source"
    source_folder_path: Path = source_path / "level1/level2/level3"
    source_folder_path.mkdir(parents=True)

    destination_path: Path = tmp_path / "destination"
    destination_folder_path: Path = destination_path / "level1/level2/level3"
    destination_folder_path.mkdir(parents=True)

    assert (
        is_folder_in_other_as_folder(source_folder_path, source_path, destination_path)
        is True
    )


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

    assert (
        is_folder_in_other_as_folder(source_folder_path, source_path, destination_path)
        is False
    )
