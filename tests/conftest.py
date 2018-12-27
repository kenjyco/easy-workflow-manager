import pytest
import os
import shutil
from . import *


@pytest.fixture(autouse=True, scope='class')
def repos():
    base = os.path.join('/tmp', str(os.getpid()))
    if os.path.isdir(base):
        shutil.rmtree(base)
    paths = {
        'remote': os.path.join(base, 'remote_repo'),
        'local': os.path.join(base, 'local_repo'),
    }
    init_clone_cd_repo(paths['remote'], paths['local'])
    yield paths
    os.chdir(os.environ['HOME'])
    print('\nDeleting {}'.format(repr(base)))
    shutil.rmtree(base)
