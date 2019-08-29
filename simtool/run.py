import os
import uuid
import copy
from subprocess import call

import papermill as pm
import yaml
from .db import DB
from .experiment import get_experiment
from .datastore import FileDataStore
from .utils import _find_simtool, _get_dict, _get_extra_files

# FIXME: the three xxxRUN classes all start the same.  Extract into a common method.

class LocalRun:
    """
    Run a notebook without using Submit.
    """

    def __init__(self, simtool_name, inputs, run_name, cache):
        simtool_path, simtool_name, published = _find_simtool(simtool_name)
        self.inputs = copy.deepcopy(inputs)
        self.input_dict = _get_dict(self.inputs)

        if cache:
            self.dstore = Run.ds_handler(simtool_name, self.input_dict, published)

        if run_name is None:
            run_name = str(uuid.uuid4()).replace('-', '')
        self.run_name = run_name
        self.outdir = os.path.join(get_experiment(), run_name) 
        os.makedirs(self.outdir)
        self.outname = os.path.join(self.outdir, simtool_name+'.ipynb')

        self.cached = False
        if cache:
            self.cached = self.dstore.read_cache(self.outdir, published)

        if not self.cached:
            # Prepare output directory by copying any files that the notebook
            # depends on.
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

            # FIXME: run in background. wait or check status.
            pm.execute_notebook(simtool_path, self.outname, parameters=self.input_dict, cwd=self.outdir)
            if cache:
                self.dstore.write_cache(self.outdir)

        self.db = DB(self.outname, dir=self.outdir)


class SubmitLocalRun:
    """
    Run a notebook using submit --local.
    """

    def __init__(self, simtool_name, inputs, run_name, cache):
        simtool_path, simtool_name, published = _find_simtool(simtool_name)
        self.inputs = copy.deepcopy(inputs)
        self.input_dict = _get_dict(self.inputs)

        if cache:
            self.dstore = Run.ds_handler(simtool_name, self.input_dict, published)

        if run_name is None:
            run_name = str(uuid.uuid4()).replace('-', '')
        self.run_name = run_name
        self.outdir = os.path.join(get_experiment(), run_name)
        os.makedirs(self.outdir)
        localname = simtool_name + '.ipynb'
        self.outname = os.path.join(self.outdir, localname)

        self.cached = False
        if cache:
            self.cached = self.dstore.read_cache(self.outdir, published)

        if not self.cached:
            # Prepare output directory by copying any files that the notebook
            # depends on.
            sdir = os.path.dirname(simtool_path)
            if published:
                # We want to allow simtools to be more than just the notebook,
                # so we recursively copy the notebook directory.
                call("cp -sRf %s/* %s" % (sdir, self.outdir), shell=True)
                # except the notebook itself
                os.remove(os.path.join(self.outdir, localname))
            else:
                files = _get_extra_files(simtool_path)
                # print("EXTRA FILES:", files)
                if files == "*":
                    call("cp -sRf %s/* %s" % (sdir, self.outdir), shell=True)
                    os.remove(os.path.join(self.outdir, localname))
                elif files is not None:
                    for f in files:
                        os.symlink(os.path.abspath(os.path.join(sdir, f)), os.path.join(self.outdir, f))
            
            # FIXME: run in background. wait or check status.
            cwd = os.getcwd()
            os.chdir(self.outdir)
            with open('inputs.yaml', 'w') as fp:
                yaml.dump(self.input_dict, fp)
            cmd = f"submit --local papermill -f inputs.yaml {simtool_path} {localname}"
            call(cmd, shell=True)
            os.chdir(cwd)

            if cache:
                self.dstore.write_cache(self.outdir)

        self.db = DB(self.outname, dir=self.outdir)


class SubmitRun:
    """
    A run of a notebook using submit.
    """

    def __init__(self, simtool_name, inputs, run_name, cache, venue):
        simtool_path, simtool_name, published = _find_simtool(simtool_name)
        self.inputs = copy.deepcopy(inputs)
        self.input_dict = _get_dict(self.inputs)

        if cache:
            self.dstore = Run.ds_handler(simtool_name, self.input_dict, published)

        if run_name is None:
            run_name = str(uuid.uuid4()).replace('-', '')
        self.run_name = run_name
        self.outdir = os.path.join(get_experiment(), run_name)
        os.makedirs(self.outdir)
        localname = simtool_name + '.ipynb'
        self.outname = os.path.join(self.outdir, localname)

        self.cached = False
        if cache:
            self.cached = self.dstore.read_cache(self.outdir, published)

        if not self.cached:
            # Prepare output directory by copying any files that the notebook
            # depends on.
            sdir = os.path.dirname(simtool_path)
            if published:
                # We want to allow simtools to be more than just the notebook,
                # so we recursively copy the notebook directory.
                call("cp -sRf %s/* %s" % (sdir, self.outdir), shell=True)
                # except the notebook needs to not be a link because it will be overwrittem
                os.remove(os.path.join(self.outdir, localname))
                call("cp %s %s" % (simtool_path, self.outdir), shell=True)
            else:
                files = _get_extra_files(simtool_path)
                # print("EXTRA FILES:", files)
                if files == "*":
                    call("cp -sRf %s/* %s" % (sdir, self.outdir), shell=True)
                    os.remove(os.path.join(self.outdir, localname))
                elif files is not None:
                    for f in files:
                        os.symlink(os.path.abspath(os.path.join(sdir, f)), os.path.join(self.outdir, f))
            
            # FIXME: run in background. show progress. wait or check status.
            cwd = os.getcwd()
            os.chdir(self.outdir)
            includes = '-i ' + ' -i '.join([f for f in os.listdir() if f != localname])
            with open('inputs.yaml', 'w') as fp:
                yaml.dump(self.input_dict, fp)
            cmd = f"submit {includes} anaconda-6_papermill -f inputs.yaml {localname} {localname}"
            print('cmd=', cmd)
            call(cmd, shell=True)
            os.chdir(cwd)

            if cache:
                self.dstore.write_cache(self.outdir)

        self.db = DB(self.outname, dir=self.outdir)




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
            venue:  'submit' to use submit.  'local' to use 'submit --local'.  Default
                is None, which runs locally without submit.
        Returns:
            A Run object.
        """
    ds_handler = FileDataStore  # local files or NFS.  should be config option

    def __new__(cls, simtool_name, inputs, run_name=None, cache=True, venue=None):
        # cls.__init__(cls, desc)
        if venue == 'local':
            newclass = SubmitLocalRun(simtool_name, inputs, run_name, cache)
        elif venue == 'submit': 
            newclass = SubmitRun(simtool_name, inputs, run_name, cache, venue)
        elif venue is None:
            newclass = LocalRun(simtool_name, inputs, run_name, cache)
        else:
            raise ValueError('Bad Venue')
        return newclass
