"""runlog - Managable per-run logs for recurring jobs.

Usage:
 runlog [--config=<CONF>] list-jobs
 runlog [--config=<CONF>] list-runs <JOBID>
 runlog [--config=<CONF>] logs <JOBID> [<RUNID> ...]

Arguments:
 <JOBID>        The id string of a job.
 <RUNID>        The id of an individual run of a job.

Options:
 -c, --config=<CONF>             A config file with a [runlog] section.
"""

from ConfigParser import SafeConfigParser

import docopt

from runlog import RunLogger, __version__


# TODO: Validate all the inputs!


def do_list_jobs(rl, args):
    for jobid in rl.list_jobs():
        print(jobid)


def do_list_runs(rl, args):
    jobid = args['<JOBID>']
    for runid in rl.list_runs(jobid):
        print("%s\t%s" % (jobid, runid))


def do_logs(rl, args):
    jobid = args['<JOBID>']
    runids = args['<RUNID>']
    for runid in runids:
        print("\n".join(rl.get_log(jobid, runid)))


def run():
    args = docopt.docopt(__doc__, help=True, version=__version__)
    config_file = args['--config'] or '.runlog.conf'
    parser = SafeConfigParser()
    parser.read([config_file])
    conf = dict(parser.items('runlog'))
    try:
        redis_conf = dict(parser.items('runlog-redis'))
    except:
        redis_conf = {}
    command = [k for k, v in args.items() if v and k[0].isalpha()][0]
    max_logs = conf.get('max_logs')
    rl = RunLogger(redis_config=redis_conf,
                   max_logs=int(max_logs) if max_logs else None)
    func = globals()['do_' + command.replace('-', '_')]
    func(rl, args)
