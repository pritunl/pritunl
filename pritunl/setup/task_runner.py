from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

def setup_task_runner():
    from pritunl.task.runner import TaskRunner
    TaskRunner().start()
