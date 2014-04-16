import pkg_resources

from runlog.loggage import CancelLog, RunLogger


version_file = pkg_resources.resource_filename(__name__, 'VERSION')
with open(version_file) as vf:
    __version__ = vf.read()
del version_file


__all__ = ['CancelLog', 'RunLogger', '__version__']
