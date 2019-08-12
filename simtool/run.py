import os
import uuid
import copy
from subprocess import call

import papermill as pm
from .db import DB
from .experiment import get_experiment
from .datastore import FileDataStore
from .utils import _find_simtool, _get_dict, _get_extra_files

class Run:
    """Runs a SimTool.

        A copy of the SimTool will be created in the subdirectory with the same
        name as the current experiment.  It will be run with the provided inputs.

        If cache is True and the tool is published, the global cache will be used.
        If the tool is not published, and cache is True, a local user cache will be used.

        Args:
            simtool_name: The name of a published SimTool or the path to a notebook
                containing a SimTool.
            inputs: A SimTools Params object or a dictionary of key-value pairs.
            run_name: An optional name for the run.  A unique name will be generated
                if none was supplied.
            cache:  If the SimTool was run with the same inputs previously, return
                the results from the cache.  Otherwise cache the results.  If this
                parameter is False, do neither of these.
        """
    ds_handler = FileDataStore  # local files or NFS

    def __init__(self, simtool_name, inputs, run_name=None, cache=True):
        simtool_path, simtool_name, published = _find_simtool(simtool_name)
        self.inputs = copy.deepcopy(inputs)
        self.input_dict = _get_dict(self.inputs)

        if cache:
            self.dstore = Run.ds_handler(simtool_name, self.input_dict, published)
            # print("Created cache: ", self.dstore.rdir)

        if run_name is None:
            run_name = str(uuid.uuid4()).replace('-', '')
        self.run_name = run_name
        self.outdir = os.path.join(get_experiment(), run_name) 
        os.makedirs(self.outdir)

        # FIXME: cache file operation belong in datastore.py
        sdir = os.path.dirname(simtool_path)
        if published:
            # We want to allow simtools to be more than just the notebook,
            # so we recursively copy the notebook directory.
            call("cp -sRf %s/* %s" % (sdir, self.outdir), shell=True)
            # except the notebook itself
            os.remove(os.path.join(self.outdir, simtool_name+'.ipynb'))
        else:
            files = _get_extra_files(simtool_path)
            # print("EXTRA FILES:", files)
            if files == "*":
                call("cp -sRf %s/* %s" % (sdir, self.outdir), shell=True)
                os.remove(os.path.join(self.outdir, simtool_name+'.ipynb'))
            elif files is not None:
                for f in files:
                    os.symlink(os.path.abspath(os.path.join(sdir, f)), os.path.join(self.outdir, f))

        self.outname = os.path.join(self.outdir, simtool_name+'.ipynb')
        # FIXME: run in background. wait or check status.

        self.cached = False
        if cache:
            if os.path.exists(self.dstore.rdir):
                if published:
                    print("CACHED. Fetching results from Data Store.")
                else:
                    print("CACHED. Fetching results from user cache. (%s)" % self.dstore.USER_FILEDIR)
                call('/bin/cp -sRf %s/* %s' % (self.dstore.rdir, self.outdir), shell=True)
                self.cached = True

        if not self.cached:
            pm.execute_notebook(simtool_path, self.outname, parameters=self.input_dict, cwd=self.outdir)
            if cache:
                # copy notebook to data store
                os.makedirs(self.dstore.rdir)
                call('/bin/cp -prL %s/* %s' % (self.outdir, self.dstore.rdir), shell=True)
                call('chmod -R g+w %s' % self.dstore.rdir, shell=True)
                # FIXME: should be config option in datasore
                call('chown -R :strachangroup %s' % self.dstore.rdir, shell=True)


        self.db = DB(self.outname, dir=self.outdir)


# To use with Submit:
# - write inputs to yaml file
# - use papermill cli https://papermill.readthedocs.io/en/latest/usage-cli.html
# - copy results to self.outdir and/or datastore
