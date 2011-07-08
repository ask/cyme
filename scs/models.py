import shlex

from subprocess import Popen, PIPE

from django.db import models
from django.utils.translation import ugettext_lazy as _

from scs.managers import NodeManager, QueueManager
from scs.utils import shellquote


CWD = "/var/run/scs"


def _exec(cmd, cwd=CWD):
    return Popen(shlex.split(cmd), stdout=PIPE, cwd=cwd).communicate()[0]


class Queue(models.Model):
    objects = QueueManager()

    name = models.CharField(_(u"name"), max_length=128, unique=True)
    is_default = models.BooleanField(_("is default"), default=False)
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _(u"queue")
        verbose_name_plural = _(u"queues")

    def __unicode__(self):
        return self.name


class Node(models.Model):
    Queue = Queue
    objects = NodeManager()

    name = models.CharField(_(u"name"), max_length=128, unique=True)
    queues = models.ManyToManyField(Queue, null=True)
    concurrency = models.IntegerField(default=None, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _(u"node")
        verbose_name_plural = _(u"nodes")

    def __unicode__(self):
        return self.name

    def start(self, multi="celeryd-multi"):
        return _exec("%s start %s %s" % (multi, self.name, self.strargv))

    def stop(self, multi="celeryd-multi"):
        return _exec("%s stop %s %s" % (multi, self.name, self.strargv))

    @property
    def strargv(self):
        return " ".join("%s %s" % (k, shellquote(str(v)))
                            for k, v in self.argv if v)

    @property
    def argv(self):
        return (("-c", self.concurrency),
                ("-Q", ",".join(q.name for q in self.queues.active())))
