from contextlib import contextmanager
import datetime
import logging
import threading
import time

from redis import StrictRedis


# Without this we will get "no handlers" lines in stderr.
class DoNothing(logging.Handler):

    def emit(self, record):
        pass


donothing = logging.getLogger('donothing')
donothing.addHandler(DoNothing())


class CancelLog(Exception):
    """Run canceled so it's ok to forget the current run."""


class RunlogHandler(logging.Handler):

    def __init__(self, redis, job_id, run_id):
        logging.Handler.__init__(self)
        self.redis = redis
        self.job_id = job_id
        self.run_id = run_id

    def emit(self, record):
        try:
            msg = self.format(record)
            self.redis.rpush('%s|%s|log' % (self.job_id, self.run_id), msg)
        except (KeyboardInterrupt, SystemExit):  # pragma: no cover
            raise
        except:  # pragma: no cover
            self.handleError(record)


class RunLogger(object):

    def __init__(self, redis_config, max_logs=1000):
        self._redis = StrictRedis(**redis_config)
        self._lock = threading.Lock()
        self._logger = donothing  # All logger calls ignored
        self._job_id = None
        self.max_logs = max_logs

    @contextmanager
    def runlog(self, job_id, run_id=None):
        if not self._lock.acquire(False):
            raise Exception("Can't start %s. %s already started."
                            % (job_id, self._job_id))
        if run_id is None:
            run_id = str(datetime.datetime.now()).replace(' ', '-')
        try:
            hdlr = RunlogHandler(self._redis, job_id, run_id)
            self._logger = logging.getLogger("%s|%s" % (job_id, run_id))
            self._job_id = job_id
            self._logger.addHandler(hdlr)
            timestamp = time.time()
            self._redis.zadd('jobs', timestamp, job_id)
            self._redis.zadd('%s|runs' % job_id, timestamp, run_id)
            self._redis.set('%s|%s|start' % (job_id, run_id), timestamp)
            try:
                try:
                    yield self._logger
                finally:
                    self._redis.set('%s|%s|end' % (job_id, run_id),
                                    time.time())
            except CancelLog:
                self.forget_run(job_id, run_id)
            except Exception as ex:
                self._redis.zadd('exceptions',
                                 timestamp,
                                 "%s|%s" % (job_id, run_id))
                self._logger.exception(ex)
                del logging.Logger.manager.loggerDict[
                    "%s|%s" % (job_id, run_id)]
                raise ex  # Don't swallow errors.
        finally:
            self.forget_old_runs(job_id)
            self._job_id = None
            self._logger = donothing
            self._lock.release()

    def forget_run(self, job_id, run_id):
        self._redis.zrem('%s|runs' % job_id, run_id)
        self._redis.delete('%s|%s|start' % (job_id, run_id))
        self._redis.delete('%s|%s|end' % (job_id, run_id))
        self._redis.delete('%s|%s|log' % (job_id, run_id))

    def forget_old_runs(self, job_id):
        for run_id in self._redis.zrange('%s|runs' % job_id,
                                         self.max_logs,
                                         -1):
            self.forget_run(job_id, run_id)

    def debug(self, *a, **kw):
        self._logger.debug(*a, **kw)

    def info(self, *a, **kw):
        self._logger.info(*a, **kw)

    def warn(self, *a, **kw):
        self._logger.warn(*a, **kw)

    def warning(self, *a, **kw):
        self._logger.warning(*a, **kw)

    def error(self, *a, **kw):
        self._logger.error(*a, **kw)

    def critical(self, *a, **kw):
        self._logger.critical(*a, **kw)

    def exception(self, *a, **kw):
        self._logger.exception(*a, **kw)

    def list_jobs(self):
        return self._redis.zrevrange('jobs', 0, -1)

    def list_runs(self, job_id):
        return self._redis.zrange('%s|runs' % job_id, 0, -1)

    def run_times(self, job_id, run_id):
        return (self._redis.get('%s|%s|start' % (job_id, run_id)),
                self._redis.get('%s|%s|end' % (job_id, run_id)))

    def get_log(self, job_id, run_id):
        return self._redis.lrange('%s|%s|log' % (job_id, run_id), 0, -1)
