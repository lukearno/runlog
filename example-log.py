import logging
import sys

from runlog import RunLogger
jobid = sys.argv[1]


rl = RunLogger(redis_config={'db': 3}, max_logs=4)

for _ in range(9):
    with rl.runlog(jobid) as bar_log:
        bar_log.setLevel(logging.DEBUG)
        bar_log.warn("WTF")
