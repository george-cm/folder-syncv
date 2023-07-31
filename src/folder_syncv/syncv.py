"""
Provides functions to sync folder to replica.
"""

import logging
from collections import deque
from hashlib import md5
from pathlib import Path
from shutil import copy2, copytree, rmtree
from time import sleep
from timeit import default_timer
from typing import Literal, TypeAlias

import click

__author__ = "George Murga"
__copyright__ = "George Murga"
__license__ = "MIT"

_logger: logging.Logger = logging.getLogger(__name__)


LOGLEVEL: TypeAlias = Literal["debug", "info", "warn", "error", "critical"]


def sync_folder(source: Path, replica: Path, syncinterval: int, logfile: Path, loglevel: LOGLEVEL) -> None:
    """Synchronizes SOURCE folder to REPLICA folder.

    Args:
        source (pathlib.Path): path of the source folder
        replica (pathlib.Path): path of the target folder
        syncinterval (int): period with which to repeat the sync in seconds
        logfile (pathlib.Path): path of the logfile
        loglevel (LOGLEVEL): level of the log

    Returns:
        None
    """
    source = Path(source).resolve()
    replica = Path(replica).resolve()
    logfile = Path(logfile).resolve()
    sync_count: int = 1
    setup_logging(loglevel, logfile=logfile)

    validate_source(source)
    validate_replica(replica)

    _logger.info("Starting sync every %s seconds. SOURCE: %s -> REPLICA: %s" % (syncinterval, source.resolve(), replica.resolve()))
    try:
        while True:
            _logger.info("Syncing round %d (every %d seconds)" % (sync_count, syncinterval))

            start_time: float = default_timer()

            files_count: int = 0
            folders_count: int = 0
            files_copied: int = 0
            files_updated: int = 0
            folders_copied: int = 0
            files_deleted: int = 0
            folders_deleted: int = 0
            folders_deleted1: int = 0
            folders_deleted2: int = 0
            files_count, folders_count, files_copied, files_updated, folders_copied, folders_deleted1 = sync_source_to_replica(
                source, replica
            )
            files_deleted, folders_deleted2 = sync_replica_to_source(source, replica)
            folders_deleted = folders_deleted1 + folders_deleted2
            _logger.info(
                "processed: total files = %d, total folders = %d, files copied = %d, files_updated = %d, folders_copied = %d, "
                "files_deleted = %d, folders_deleted = %d"
                % (files_count, folders_count, files_copied, files_updated, folders_copied, files_deleted, folders_deleted)
            )
            if syncinterval == 0:
                break
            end_time: float = default_timer()
            _logger.info("Waiting for next sync round...")
            while True:
                if end_time - start_time < syncinterval:
                    sleep(1)
                    end_time = default_timer()
                else:
                    break
            sync_count += 1
    except KeyboardInterrupt:
        _logger.warn("Sync interrupted by keyboard")
    except FileNotFoundError as e:
        _logger.exception(e, exc_info=True)
    except ExpectedFileIsAFolder as e:
        _logger.exception(e, exc_info=True)
    except PermissionError as e:
        _logger.exception(e, exc_info=True)
    finally:
        _logger.info("Syncing stopped.")


def sync_source_to_replica(source: Path, replica: Path) -> tuple[int, int, int, int, int, int]:
    """Sync source contents to replica.
    Args:
        source (pathlib.Path): path of the source folder
        replica (pathlib.Path): path of the target folder
    Returns:
        Tuple[int, int, int, int]:
            files_count - how many files were processed,
            folders_count - how many folders were processed,
            files_copied - how many files were copied to the replica,
            folders_copied - how many folders were copied to the replica.
    """
    _logging: logging.Logger = logging.getLogger(__name__)
    files_count: int = 0
    folders_count: int = 0
    files_copied: int = 0
    files_updated: int = 0
    folders_copied: int = 0
    folders_deleted: int = 0
    folder_queue: deque = deque()
    folder_queue.append(source)
    _logging.debug("added source folder to queue: %s" % source.as_posix())
    while len(folder_queue) > 0:
        current_folder: Path = folder_queue.popleft()
        for el in current_folder.glob("*"):
            if el.is_file():
                _logging.debug("processing file: %s" % el.as_posix())
                files_count += 1
                if is_file_in_other_as_folder(el, source, replica):
                    replica_folder: Path = replica / (el.as_posix().replace(source.as_posix(), "").lstrip("/"))
                    replica_folder.rmdir()
                    _logging.info("deleted folder %s" % replica_folder.as_posix())
                    folders_deleted += 1
                if is_file_in_other(el, source, replica):
                    if is_file_in_other_modified(el, source, replica):
                        replica_file: Path = Path(
                            copy2(
                                el,
                                replica / (el.as_posix().replace(source.as_posix(), "").lstrip("/")),
                            )
                        )
                        _logging.info("updated file %s to %s" % (el.as_posix(), replica_file.as_posix()))
                        files_updated += 1
                else:
                    replica_file = Path(
                        copy2(
                            el,
                            replica / (el.as_posix().replace(source.as_posix(), "").lstrip("/")),
                        )
                    )
                    _logging.info("copied file %s to %s" % (el.as_posix(), replica_file.as_posix()))
                    files_copied += 1
            elif el.is_dir():
                folders_count += 1
                if is_folder_in_other_as_folder(el, source, replica):
                    folder_queue.append(el)
                    _logging.debug("added to queue: %s" % el.as_posix())
                else:
                    if is_folder_in_other_as_file(el, source, replica):
                        replica_file = Path(
                            copy2(
                                el,
                                replica / (el.as_posix().replace(source.as_posix(), "").lstrip("/")),
                            )
                        )
                        replica_file.unlink()
                        _logging.info("deleted file %s" % replica_file.as_posix())
                    destination_folder = Path(el.as_posix().replace(source.as_posix(), replica.as_posix()))
                    replica_folder = Path(copytree(el, destination_folder))
                    _logging.info("copied whole folder to replica %s" % replica_folder.as_posix())
                    folders_copied += 1
    return files_count, folders_count, files_copied, files_updated, folders_copied, folders_deleted


def sync_replica_to_source(source: Path, replica: Path) -> tuple[int, int]:
    """Remove files and folders from replica which are not in source.
    Args:
        source (pathlib.Path): path of the source folder
        replica (pathlib.Path): path of the target folder
    Returns:
        Tuple[int, int, int, int]:
            files_deleted - how many files were deleted,
            folders_deleted - how many folders were deleted,
    """
    _logging: logging.Logger = logging.getLogger(__name__)
    files_deleted: int = 0
    folders_deleted: int = 0
    folder_queue: deque = deque()
    folder_queue.append(replica)
    _logging.debug("added replica to folder queue: %s" % replica.as_posix())
    while len(folder_queue) > 0:
        current_folder: Path = folder_queue.popleft()
        for el in current_folder.glob("*"):
            if el.is_file():
                _logging.debug("processing file: %s" % el.as_posix())
                if not is_file_in_other(el, replica, source):
                    el.unlink()
                    _logger.info("deleted file from replica: %s" % el.as_posix())
                    files_deleted += 1
            elif el.is_dir():
                if is_folder_in_other_as_folder(el, replica, source):
                    pass
                else:
                    rmtree(el)
                    _logger.info("deleted folder from replica: %s" % el.as_posix())
                    folders_deleted += 1
    return files_deleted, folders_deleted


def is_folder_in_other_as_folder(folder_to_check: Path, source: Path, destination: Path) -> bool:
    """Return true if the folder_to_check path is in destination and is a folder.

    Args:
        folder_to_check (pathlib.Path): the folder to search for in destination (relative path must match)
        source (pathlib.Path): path of the soruce folder
        destination (pathlib.Path): path of the destination

    Returns:
        bool: True if the folder searched is in the destination folder and is a file. False otherwise.
    """
    glob_str: str = folder_to_check.as_posix().replace(source.as_posix(), "").lstrip("/")
    potential_matches = list(destination.glob(glob_str))
    if len(potential_matches) > 0:
        match_folder: Path = potential_matches[0]
        if match_folder.is_dir():
            return True
    return False


def is_folder_in_other_as_file(folder_to_check: Path, source: Path, destination: Path) -> bool:
    """Return true if the folder_to_check path is in destination but it's a file not a folder.

    Args:
        folder_to_check (pathlib.Path): the folder to search for in destination (relative path must match)
        source (pathlib.Path): path of the soruce folder
        destination (pathlib.Path): path of the destination

    Returns:
        bool: True if the folder searched is in the destination folder but it's a file. False otherwise.
    """
    glob_str: str = folder_to_check.as_posix().replace(source.as_posix(), "").lstrip("/")
    potential_matches = list(destination.glob(glob_str))
    if len(potential_matches) > 0:
        match_folder: Path = potential_matches[0]
        if match_folder.is_file():
            return True
    return False


def is_file_in_other_as_folder(file_to_check: Path, source: Path, destination: Path) -> bool:
    """Check if file_to_check is in destination folder but it's a folder.

    Args:
        file_to_check (pathlib.Path): path of the file to check from the source folder
        source (pathlib.Path): path of the source folder
        destination (pathlib.Path): path of the destination folder

    Returns:
        bool: True if the file is found in the destination and is a folder. False otherwise
    """
    glob_str: str = file_to_check.as_posix().replace(source.as_posix(), "").lstrip("/")
    potential_matches = list(destination.glob(glob_str))
    if len(potential_matches) > 0:
        match_file: Path = potential_matches[0]
        if match_file.is_dir():
            return True
    return False


def is_file_in_other(file_to_check: Path, source: Path, destination: Path) -> bool:
    """Check if file_to_check is in destination folder.

    Args:
        file_to_check (pathlib.Path): path of the file to check from the source folder
        source (pathlib.Path): path of the source folder
        destination (pathlib.Path): path of the destination folder

    Returns:
        bool: True if the file is found in the destination False otherwise
    Raises:
        ExpectedFileIsAFolder custom exception if the file is found but it's a folder
    """
    glob_str: str = file_to_check.as_posix().replace(source.as_posix(), "").lstrip("/")
    potential_matches = list(destination.glob(glob_str))
    if len(potential_matches) > 0:
        match_file: Path = potential_matches[0]
        if match_file.is_file():
            return True
        else:
            raise ExpectedFileIsAFolder(f"Expected {match_file.as_posix()} to be a file but it's a folder.")
    return False


class ExpectedFileIsAFolder(Exception):
    pass


def is_file_in_other_modified(file_to_check: Path, source: Path, destination: Path) -> bool:
    """Check if file_to_check is in destination folder and it's the same file.
    Given there is a file with the same name in the destination folder (same relative path)
    assume if modification times are the same the files are the same.
    If the modifications time are different compare the files' content using md5.

    Args:
        file_to_check (pathlib.Path): path of the file to check from the source folder
        source (pathlib.Path): path of the source folder
        destination (pathlib.Path): path of the destination folder

    Returns:
        bool: False of the file is found in the destination at the same relative path and either
        the modification times are the same or the md5 hash of the contents are the same. True otherwise
    Raises:
        FileNotFoundError if the file is not found in the destination folder
    """
    glob_str: str = file_to_check.as_posix().replace(source.as_posix(), "").lstrip("/")
    potential_matches = list(destination.glob(glob_str))
    if len(potential_matches) > 0:
        match_file: Path = potential_matches[0]
        destination_mdate: float = match_file.stat().st_mtime
        source_mdate: float = file_to_check.stat().st_mtime
        if source_mdate == destination_mdate:
            return False
        source_hash: str = compute_hash(file_to_check)
        destination_hash: str = compute_hash(match_file)
        if source_hash == destination_hash:
            return False
    else:
        raise FileNotFoundError
    return True


def compute_hash(file_to_check: Path) -> str:
    hash = md5()
    with file_to_check.open("rb") as f:
        chunk: bytes = f.read(4096)
        while chunk:
            hash.update(chunk)
            chunk = f.read(4096)
    return hash.hexdigest()


def validate_source(path: Path) -> bool:
    """Validate source folder

    Args:
        path (pathlib.Path): source folder path

    Returns:
        bool: True if path exists and is a folder

    Raises:
        SystemExit: path does not exist
        SystemExit: path is not a folder
    """
    _logger: logging.Logger = logging.getLogger(__name__)
    if not path.exists():
        _logger.error("SOURCE folder: %s doesn't exist" % path.as_posix())
        raise SystemExit(1)
    if not path.is_dir():
        _logger.error("SOURCE: %s is not a folder" % path.as_posix())
        raise SystemExit(1)
    return True


def validate_replica(path: Path) -> bool:
    """Validate replica folder.
    If it doesn't exist, create it.
    If it exists but it's not a folder raise SystemExit.
    If it can't create it raise PermissionError

    Args:
        path (pathlib.Path): replica folder path

    Returns:
        bool: True if path exists and is a folder or if it doesn't exist but it created it successfuelly.

    Raises:
        SystemExit: path is not a folder
        SystemExit: could not create replica folder
    """
    _logger: logging.Logger = logging.getLogger(__name__)
    if not path.exists():
        try:
            path.mkdir(parents=True)
        except PermissionError:
            _logger.error("Permission denied trying to create REPLICA folder: %s" % path.as_posix())
            raise SystemExit()
    if not path.is_dir():
        _logger.error("REPLICA: %s is not a folder" % path.as_posix())
        raise SystemExit(1)
    return True


def setup_logging(loglevel: LOGLEVEL, logfile: str | Path) -> None:
    """Setup logging

    Args:
      loglevel (logging._Level): minimum loglevel for emitting messages

    Returns:
        None
    """
    _logger: logging.Logger = logging.getLogger(__name__)
    loglevels: dict[str, int] = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    _logger.setLevel(loglevels[loglevel])
    logformat = "[%(asctime)s.%(msecs)03d] %(levelname)s:%(name)s:- %(message)s"
    formatter = logging.Formatter(fmt=logformat, datefmt="%Y-%m-%d %H:%M:%S")

    # setup file logging
    fh = logging.FileHandler(logfile, encoding="utf-8", errors="replace")
    fh.setLevel(loglevels[loglevel])
    fh.setFormatter(formatter)

    # setup console logging
    ch = logging.StreamHandler()  # type: ignore
    ch.setLevel(loglevels[loglevel])
    ch.setFormatter(formatter)

    _logger.addHandler(fh)
    _logger.addHandler(ch)


@click.command()
@click.argument("source", type=click.Path(path_type=Path))
@click.argument("replica", type=click.Path(path_type=Path))
@click.option(
    "--syncinterval",
    type=click.IntRange(min=0, max=2_678_400),
    help="Seconds bettwen synchronizations.\nmin = 0 (sync only once), \nmax = 2678400 (31 days). Default = 0",
    required=True,
    default=0,
)
@click.option("--logfile", type=click.Path(path_type=Path), help="path to log file", required=True)
@click.option(
    "--loglevel",
    type=click.Choice(["debug", "info", "warn", "error", "critical"], case_sensitive=False),
    default="info",
    help="Default = info",
)
@click.version_option()
@click.help_option("-h", "--help")
def main(
    source: Path,
    replica: Path,
    syncinterval: int,
    logfile: Path,
    loglevel: LOGLEVEL,
    # loglevel: Literal["debug", "info", "warn", "error", "critical"],
) -> None:
    """Main entrypoint"""

    sync_folder(source, replica, syncinterval, logfile, loglevel)


if __name__ == "__main__":
    main()
