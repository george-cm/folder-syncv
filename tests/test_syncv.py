import pytest

from folder_syncv.syncv import setup_logging

__author__ = "George Murga"
__copyright__ = "George Murga"
__license__ = "MIT"


def test_setup_logging_logfile_parent_doesnt_exist(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        setup_logging(loglevel="debug", logfile=tmp_path / "subpath1/syncv.log")
