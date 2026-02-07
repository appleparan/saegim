"""saegim package.

(Backend) human-in-the-loop labeling platform for Korean document benchmarks
"""

from importlib.metadata import PackageNotFoundError, version

from saegim.app import create_app

try:
    __version__ = version('saegim')
except PackageNotFoundError:
    __version__ = 'unknown'

__author__ = """Jongsu Kim"""
__email__ = 'jongsukim8@gmail.com'

__all__ = ['create_app']
