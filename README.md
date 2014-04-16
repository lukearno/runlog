# Runlog

Managable detaied per-run logs for recurring jobs.

"Why did X happen the last time the Foo job ran for user Bar?"

"Job Y blew up when it ran yesterday. Where and why did it fail?"

Runlog provides a Python standard library logging-based, Redis-backed
way to store and access logs for the last N interesting runs of a job.
It's very simple to add detailed logging to code that runs inside
your recurring jobs without cluttering up your normal log files with
noisy, interleaving output.

It is very easy to add this logging to your code. An unambitious,
CLI allows you to list jobs, list previous and ongoing runs and to output
their logs. (Pipe them to your favorite unix utilities and enjoy.)

## Logging a Job

Job logging is done with normal log calls and a job-logging context
manager.

```python
import logging
from runlog import RunLogger

rl = RunLogger(redis_config={'host': 'localhost'},
               max_logs=10)

rl.debug("You will never see this.")

with rl.runlog('recurring-job-32') as logger:
    logger.setLevel(logging.DEBUG)
    rl.debug("You will see this in the log of a run of this job.")

rl.error("You don't see this either.")
```

Caveat: you will actually see all log messages if you add handlers
to the root logger. But if that is the case you are drinking from
the firehose and it's probably what you want to happen anyway.

## Finding The Output

Assuming you have a `.runlog.conf` that looks like this

```ini
[runlog]
max-logs: 10

[runlog-redis]
host: localhost
```

... you can find the logs for your job like this:

```bash
$ runlog list-jobs
recurring-job-32

$ runlog list-runs recurring-job-32
recurring-job-32 2014-04-16-04:35:23.562999
recurring-job-32 2014-04-15-04:33:11.463847
...

$ runlog logs recurring-job-32 2014-04-15-04:33:11.463847 2014-04-16-04:35:23.562999 
[ ... LOGS OF THE TWO RUNS SPECIFIED ... ]
```

Coming soon: range queries over log messages.

## Handling Errors

If something blows up inside the job-loggging context manager,
the traceback will be added to the log for the current run and
the exception will be re-raise. Errors will not be swallowed.

## Throwing Away Boring Logs

If your job turns out of be a no-op or is in some other way boring
to you, you can raise a `CancelLog` and just forget the whole thing.

```
with rl.runlog('job-127') as logger:
     things_processed = run_job(127)
     if things_processed == []:
         raise CancelLog()  # This run is forgotten.
```

CancelLog will be swallowed, but only _inside_ the context manager.

## Managing Data

Set up a dedicated Redis instance. Cap the memory. Throw away logs
that are not interesting. Look at data growth and adjust `max_logs`
or be more picky about which jobs you log. Archive really interesting
things and/or some random samples into some kind of cold storage.
