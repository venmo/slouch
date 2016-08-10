import logging

from libfaketime import reexec_if_needed


def pytest_configure():
    reexec_if_needed()
    logging.getLogger('slouch').addHandler(logging.NullHandler())
