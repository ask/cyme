"""cyme.utils"""
from __future__ import absolute_import

import sys

from importlib import import_module

from celery import current_app as celery
from celery.utils import get_symbol_by_name
from cl.utils.functional import promise, maybe_promise # noqa
from kombu.utils import gen_unique_id as uuid          # noqa
from kombu.utils import cached_property                # noqa
from unipath import Path as _Path

_pkg_cache = {}


def force_list(obj):
    if not hasattr(obj, "__iter__"):
        return [obj]
    return obj


def find_package(mod, _s=None):
    pkg = None
    _s = _s or mod
    if not mod:
        return
    if mod in _pkg_cache:
        pkg = _pkg_cache[_s] = _pkg_cache[mod]
    else:
        _mod = sys.modules[mod]
        if _mod.__package__:
            pkg = _pkg_cache[_s] = _mod.__package__
    return pkg or find_package('.'.join(mod.split('.')[:-1]), _s)


def find_symbol(origin, sym):
    return get_symbol_by_name(sym,
                package=find_package(getattr(origin, "__module__", None
                                        or origin.__class__.__module__)))


def instantiate(origin, sym, *args, **kwargs):
    return find_symbol(origin, sym)(*args, **kwargs)


class Path(_Path):
    """Path that can use the ``/`` operator to combine paths.

        >>> p = Path("foo")
        >>> p / "bar" / "baz"
        Path("foo/bar/baz")
    """

    def __div__(self, other):
        return Path(self, other)


def shellquote(v):
    # XXX Not currently used, but may be of use later,
    # and don't want to write it again.
    return "\\'".join("'" + p + "'" for p in v.split("'"))


def imerge_settings(a, b):
    """Merge two django settings modules,
    keys in ``b`` have precedence."""
    orig = import_module(a.SETTINGS_MODULE)
    for key, value in vars(b).iteritems():
        if not hasattr(orig, key):
            setattr(a, key, value)


def setup_logging(loglevel="INFO", logfile=None):
    from celery.utils import LOG_LEVELS
    if isinstance(loglevel, basestring):
        loglevel = LOG_LEVELS[loglevel]
    return celery.log.setup_logging_subsystem(loglevel, logfile)


def redirect_stdouts_to_logger(loglevel="INFO", logfile=None,
        redirect_level="WARNING", stdout=False, stderr=True):
    log = celery.log
    handled = setup_logging(loglevel, logfile)
    if not handled:
        return log.redirect_stdouts_to_logger(
                    log.get_default_logger(name="cyme"),
                    redirect_level, stdout=stdout, stderr=stderr)


class LazyProgressBar(object):

    def __init__(self, size, description=None, endtext=None):
        self.size = size
        self.current = 0
        self.description = description
        self.endtext = endtext
        self._finished = False

    def step(self, i=1, **kwargs):
        if not self._finished:
            if not self.current:
                # implicit start
                self.current = 1
                if self.description:
                    sys.stderr.write("\n\n%s\n" % (self.description, ))
                return self._bar   ## noqa
            self.current += i
            if self.current >= self.size:
                self.size = self._bar.maxval = self.current
            self._bar.update(self.current)

    def finish(self, **kwargs):
        if not self._finished:
            self._bar.finish()
            self._finished = True
            if self.endtext:
                sys.stderr.write(self.endtext)

    @cached_property
    def _bar(self):
        from progressbar import ProgressBar
        return ProgressBar(maxval=self.size).start()