import logging
from unittest import TestCase

from runlog import CancelLog, RunLogger


class RunloggerTests(TestCase):

    def setUp(self):
        self.rl = RunLogger(redis_config={'db': 3}, max_logs=4)
        self.rl._redis.flushdb()

    def log_all_the_things(self):
        self.rl.debug("DEBUG")
        self.rl.info("INFO")
        self.rl.warn("WARN")
        self.rl.warning("WARNING")
        self.rl.error("ERROR")
        self.rl.critical("CRITICAL")
        try:
            raise Exception("Exception!")
        except Exception as ex:
            self.rl.exception(ex)

    def test_no_logs_outside_of_context_manager(self):
        self.log_all_the_things()
        self.assertEqual(self.rl.list_jobs(), [])

    def test_log_a_job(self):
        with self.rl.runlog('foo') as logger:
            logger.setLevel(logging.DEBUG)
            self.log_all_the_things()
        self.assertEqual(self.rl.list_jobs(), [b'foo'])
        self.assertEqual(len(self.rl.list_runs('foo')), 1)
        run_id = self.rl.list_runs('foo')[0].decode()
        log = self.rl.get_log('foo', run_id)
        self.assertEqual(len(log), 7)
        self.assertEqual(log[:6], [b'DEBUG',
                                   b'INFO',
                                   b'WARN',
                                   b'WARNING',
                                   b'ERROR',
                                   b'CRITICAL'])
        self.assertTrue(log[6].startswith(b'Exception!\n'))
        start, end = self.rl.run_times('foo', run_id)
        self.assertTrue(0 < float(end) - float(start) < 1)

    def test_log_a_job_that_blows_up(self):

        def log_blows_up():
            with self.rl.runlog('foo') as logger:
                logger.setLevel(logging.DEBUG)
                self.log_all_the_things()
                raise Exception("Kaboom!")

        self.assertRaises(Exception, log_blows_up)
        self.assertEqual(self.rl.list_jobs(), [b'foo'])
        self.assertEqual(len(self.rl.list_runs('foo')), 1)
        log = self.rl.get_log('foo', self.rl.list_runs('foo')[0].decode())
        self.assertEqual(len(log), 8)
        self.assertEqual(log[:6], [b'DEBUG',
                                   b'INFO',
                                   b'WARN',
                                   b'WARNING',
                                   b'ERROR',
                                   b'CRITICAL'])
        self.assertTrue(log[6].startswith(b'Exception!\n'))
        self.assertTrue(log[7].startswith(b'Kaboom!\n'))

    def test_log_already_running(self):

        def log_already_running():
            with self.rl.runlog('foo') as logger:
                logger.setLevel(logging.DEBUG)
                with self.rl.runlog('bar') as logger:
                    self.log_all_the_things()

        self.assertRaises(Exception, log_already_running)
        self.assertEqual(self.rl.list_jobs(), [b'foo'])
        self.assertEqual(len(self.rl.list_runs('foo')), 1)
        log = self.rl.get_log('foo', self.rl.list_runs('foo')[0].decode())
        self.assertEqual(len(log), 1)
        self.assertTrue(log[0].startswith(b"Can't start bar."))

    def test_log_cancel(self):

        with self.rl.runlog('foo') as logger:
            logger.setLevel(logging.DEBUG)
            raise CancelLog

        self.assertEqual(self.rl.list_jobs(), [b'foo'])
        self.assertEqual(len(self.rl.list_runs('foo')), 0)

    def test_max_logs(self):

        for _ in range(5):
            with self.rl.runlog('foo') as logger:
                logger.setLevel(logging.DEBUG)
                self.log_all_the_things()

        self.assertEqual(self.rl.list_jobs(), [b'foo'])
        self.assertEqual(len(self.rl.list_runs('foo')), 4)
