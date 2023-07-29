"""
Provides functions to sync folder to replica.
"""

import logging
from pathlib import Path
from typing import Literal, TypeAlias

import click

__author__ = "George Murga"
__copyright__ = "George Murga"
__license__ = "MIT"

_logger: logging.Logger = logging.getLogger(__name__)


LOGLEVEL: TypeAlias = Literal["debug", "info", "warn", "error", "critical"]


def validate_source(path: Path) -> bool:
    """Validate source folder

    Args:
        path (Path): source folder path

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
        path (Path): replica folder path

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
            _logger.error(
                "Permission denied trying to create REPLICA folder: %s"
                % path.as_posix()
            )
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
    ch = logging.StreamHandler()
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
    help="seconds bettwen synchronizations.\n0 - sync continuously\nmax = 2678400 (31 days)",
    required=True,
)
@click.option(
    "--logfile", type=click.Path(path_type=Path), help="path to log file", required=True
)
@click.option(
    "--loglevel",
    type=click.Choice(
        ["debug", "info", "warn", "error", "critical"], case_sensitive=False
    ),
    default="debug",
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
    """Synchronizes SOURCE folder to REPLICA folder."""

    source = Path(source).resolve()
    replica = Path(replica).resolve()
    logfile = Path(logfile).resolve()

    setup_logging(loglevel, logfile=logfile)

    validate_source(source)
    validate_replica(replica)

    _logger.info(
        "Starting sync every %s seconds. SOURCE: %s -> REPLICA: %s"
        % (syncinterval, source.resolve(), replica.resolve())
    )
    _logger.info("Sync stopped")


if __name__ == "__main__":
    main()
