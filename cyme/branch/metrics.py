"""cyme.branch.metrics"""

from __future__ import absolute_import

import os
from math import ceil

from ..utils import cached_property


def load_average():
    return tuple(ceil(l * 1e2) / 1e2 for l in os.getloadavg())


class df(object):

    def __init__(self, path):
        self.path = path

    @property
    def total_blocks(self):
        return self.stat.f_blocks * self.stat.f_frsize / 1024

    @property
    def available(self):
        return self.stat.f_bavail * self.stat.f_frsize / 1024

    @property
    def capacity(self):
        avail = self.stat.f_bavail
        used = self.stat.f_blocks - self.stat.f_bfree
        return int(ceil(used * 100.0 / (used + avail) + 0.5))

    @cached_property
    def stat(self):
        return os.statvfs(self.path)
