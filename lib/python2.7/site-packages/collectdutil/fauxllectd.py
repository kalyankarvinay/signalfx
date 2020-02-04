"""To be imported as collectd module for unit testing (conftest.py) and development.
from collectdutil import fauxllectd as collectd  # for any references in current module.
import sys
sys.modules['collectd'] = collectd

Desired functionality beyond dummy functions TBD.
"""
import logging


log = logging.getLogger(__name__)


class Values(object):

    def __init__(self, *args, **kwargs):
        pass

    def dispatch(self):
        pass


def register_config(*args, **kwargs):
    pass


def register_read(*args, **kwargs):
    pass


def register_flush(*args, **kwargs):
    pass


def register_shutdown(*args, **kwargs):
    pass


def register_log(*args, **kwargs):
    pass


def debug(*args, **kwargs):
    log.debug(*args, **kwargs)


def info(*args, **kwargs):
    log.info(*args, **kwargs)


def notice(*args, **kwargs):
    pass


def warning(*args, **kwargs):
    log.warn(*args, **kwargs)


def error(*args, **kwargs):
    log.error(*args, **kwargs)


def register_notification(*args, **kwargs):
    pass
