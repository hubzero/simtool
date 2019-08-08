import os
import shutil

class Exp:
    """Experiment class without context manager"""
    def __init__(self, name, append=True):
        if name.startswith('.'):
            raise ValueError('Invalid experiment name')
        if append is False and os.path.exists(name):
            shutil.rmtree(name)
        if not os.path.exists(name):
            os.makedirs(name)
        self.name = name

    def __str__(self):
        return self.name

class Experiment(Exp):
    """Content manager for Experiments

    Create a subdirectory named {name} in which to place new runs.
    If *append* is False, any existing subdirectory with the same
    name is removed.

    You can also use set_experiment() to set the current experiment.

        with Experiment('my_test', append=False):
            Run(nb, inputs1)
            Run(nb, inputs2)

    Attributes:
        name: The experiment name.  When this context is entered
            it will create a subdirectory named {name}.
        append: If True, adds runs to any existing experiment of the
            same name.  If False, removes previous runs.

    """
    _experiments = []  # default name
    active = None

    def __init__(self, name, append=True):
        self.name = name
        Exp.__init__(self, name, append)

    def __enter__(self):
        Experiment._experiments.append(self)
        Experiment.active = self
    def __exit__(self, type, value, traceback):
        Experiment._experiments.pop()
        if Experiment._experiments:
            Experiment.active = Experiment._experiments[-1]
        else:
            Experiment.active = None


def set_experiment(name, append=True):
    """Create a new experiment.

    Create a subdirectory named {name} in which to place new runs.
    If *append* is False, any existing subdirectory with the same
    name is removed.  The default experiment name is 'RUNS'.

    You can also use the Experiment content manager to set the current
    experiment.

    Args:
        name: The name of the experiment (and the subdirectory).
        append: If True, adds runs to any existing experiment of the
            same name.  If False, removes previous runs.
    """
    exp = Exp(name, append)
    Experiment._experiments = [exp]
    Experiment.active = exp

# set_experiment('RUNS')  # set the default name

def get_experiment():
    """Get the current experiment name.

    Returns:
        The current experiment name.  This is the name of directory
        where new runs will be placed.
    """
    if Experiment.active is None:
        return 'RUNS'
    return Experiment.active.name
