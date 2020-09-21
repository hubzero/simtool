import os
import uuid
import copy
import tempfile
import stat
from subprocess import call
import traceback
try:
   from hubzero.submit.SubmitCommand import SubmitCommand
except ImportError:
   submitAvailable = False
else:
   submitAvailable = True

import papermill as pm
import yaml
from .db import DB
from .experiment import get_experiment
from .datastore import FileDataStore
from .utils import _get_inputs_dict, _get_extra_files, _get_inputFiles, _get_inputs_cache_dict, getSimToolOutputs

# FIXME: the three xxxRUN classes all start the same.  Extract into a common method.

class LocalRun:
    """
    Run a notebook without using submit.
    """

    def __init__(self,simToolLocation,inputs,run_name,cache):
        nbName = simToolLocation['simToolName'] +'.ipynb'
        self.inputs = copy.deepcopy(inputs)
        self.input_dict = _get_inputs_dict(self.inputs,inputFileRunPrefix=Run.inputFileRunPrefix)
        self.inputFiles = _get_inputFiles(self.inputs)
        self.outputs = copy.deepcopy(getSimToolOutputs(simToolLocation))

        if cache:
            hashableInputs = _get_inputs_cache_dict(self.inputs)
            self.dstore = Run.ds_handler(simToolLocation['simToolName'],simToolLocation['simToolRevision'],hashableInputs,'user')
            del hashableInputs

        if run_name is None:
            run_name = str(uuid.uuid4()).replace('-','')
        self.run_name = run_name
        self.outdir = os.path.join(get_experiment(),run_name)
        os.makedirs(self.outdir)
        self.outname = os.path.join(self.outdir,nbName)

        print("runname   = %s" % (self.run_name))
        print("outdir    = %s" % (self.outdir))
        self.cached = False
        if cache:
            self.cached = self.dstore.read_cache(self.outdir)
        print("cached    = %s" % (self.cached))
        print("published = %s" % (simToolLocation['published']))

        if not self.cached:
            # Prepare output directory by copying any files that the notebook
            # depends on.
            sdir = os.path.dirname(simToolLocation['notebookPath'])
            if simToolLocation['published']:
                # We want to allow simtools to be more than just the notebook,
                # so we recursively copy the notebook directory.
                call("cp -sRf %s/* %s" % (sdir,self.outdir),shell=True)
                # except the notebook itself
                os.remove(os.path.join(self.outdir,nbName))
            else:
                files = _get_extra_files(simToolLocation['notebookPath'])
                # print("EXTRA FILES:",files)
                if   files == "*":
                    call("cp -sRf %s/* %s" % (sdir,self.outdir),shell=True)
                    os.remove(os.path.join(self.outdir,nbName))
                elif files is not None:
                    for f in files:
                        os.symlink(os.path.abspath(os.path.join(sdir,f)),os.path.join(self.outdir,f))

            if Run.inputFileRunPrefix:
                inputFileRunPath = os.path.join(self.outdir,Run.inputFileRunPrefix)
                os.makedirs(inputFileRunPath)
                for inputFile in self.inputFiles:
                    call("cp -p %s %s" % (inputFile,inputFileRunPath),shell=True)
            else:
                for inputFile in self.inputFiles:
                    call("cp -p %s %s" % (inputFile,self.outdir),shell=True)

            prerunFiles = os.listdir(os.getcwd())
            prerunFiles.append(nbName)

            # FIXME: run in background. wait or check status.
            pm.execute_notebook(simToolLocation['notebookPath'],self.outname,parameters=self.input_dict,cwd=self.outdir)

            self.db = DB(self.outname,dir=self.outdir)
            self.savedOutputs     = self.db.getSavedOutputs()
            self.savedOutputFiles = self.db.getSavedOutputFiles()
#           if len(self.savedOutputFiles) > 0:
#               print("Saved output files: %s" % (self.savedOutputFiles))

            requiredOutputs  = set(self.outputs.keys())
            deliveredOutputs = set(self.savedOutputs)
            missingOutputs = requiredOutputs - deliveredOutputs
            extraOutputs   = deliveredOutputs - requiredOutputs
            if 'simToolSaveErrorOccurred' in extraOutputs:
                extraOutputs.remove('simToolSaveErrorOccurred')
            if 'simToolAllOutputsSaved' in extraOutputs:
                extraOutputs.remove('simToolAllOutputsSaved')
            if len(missingOutputs) > 0:
                print("The following outputs are missing: %s" % (list(missingOutputs)))
            if len(extraOutputs) > 0:
                print("The following additional outputs were returned: %s" % (list(extraOutputs)))

            simToolSaveErrorOccurred = self.db.getSimToolSaveErrorOccurred()
#           print("simToolSaveErrorOccurred = %d" % (simToolSaveErrorOccurred))
            simToolAllOutputsSaved = self.db.getSimToolAllOutputsSaved()
#           print("simToolAllOutputsSaved = %d" % (simToolAllOutputsSaved))

            if cache:
                self.dstore.write_cache(self.outdir,prerunFiles,self.savedOutputFiles)
        else:
            self.db = DB(self.outname,dir=self.outdir)


    def getResultSummary(self):
        return self.db.nb.scrap_dataframe


    def read(self, name, display=False, raw=False):
        return self.db.read(name,display,raw)


class SubmitLocalRun:
    """
    Run a notebook using submit --local.
    """

    def __init__(self,simToolLocation,inputs,run_name,cache):
        nbName = simToolLocation['simToolName'] +'.ipynb'
        self.inputs = copy.deepcopy(inputs)
        self.input_dict = _get_inputs_dict(self.inputs,inputFileRunPrefix=Run.inputFileRunPrefix)
        self.inputFiles = _get_inputFiles(self.inputs)
        self.outputs = copy.deepcopy(getSimToolOutputs(simToolLocation))

        if cache:
            hashableInputs = _get_inputs_cache_dict(self.inputs)
            self.dstore = Run.ds_handler(simToolLocation['simToolName'],simToolLocation['simToolRevision'],hashableInputs,'user')
            del hashableInputs

        if run_name is None:
            run_name = str(uuid.uuid4()).replace('-','')
        self.run_name = run_name
        self.outdir = os.path.join(get_experiment(),run_name)
        os.makedirs(self.outdir)
        self.outname = os.path.join(self.outdir,nbName)

        print("runname   = %s" % (self.run_name))
        print("outdir    = %s" % (self.outdir))
        self.cached = False
        if cache:
            self.cached = self.dstore.read_cache(self.outdir)
        print("cached    = %s" % (self.cached))
        print("published = %s" % (simToolLocation['published']))

        if not self.cached:
            # Prepare output directory by copying any files that the notebook
            # depends on.
            sdir = os.path.dirname(simToolLocation['notebookPath'])
            if simToolLocation['published']:
                # We want to allow simtools to be more than just the notebook,
                # so we recursively copy the notebook directory.
                call("cp -sRf %s/* %s" % (sdir,self.outdir),shell=True)
                # except the notebook itself
                os.remove(os.path.join(self.outdir,nbName))
            else:
                files = _get_extra_files(simToolLocation['notebookPath'])
                # print("EXTRA FILES:",files)
                if   files == "*":
                    call("cp -sRf %s/* %s" % (sdir,self.outdir),shell=True)
                    os.remove(os.path.join(self.outdir,nbName))
                elif files is not None:
                    for f in files:
                        os.symlink(os.path.abspath(os.path.join(sdir,f)),os.path.join(self.outdir,f))

            if Run.inputFileRunPrefix:
                inputFileRunPath = os.path.join(self.outdir,Run.inputFileRunPrefix)
                os.makedirs(inputFileRunPath)
                for inputFile in self.inputFiles:
                    call("cp -p %s %s" % (inputFile,inputFileRunPath),shell=True)
            else:
                for inputFile in self.inputFiles:
                    call("cp -p %s %s" % (inputFile,self.outdir),shell=True)

            cwd = os.getcwd()
            os.chdir(self.outdir)

            with open('inputs.yaml','w') as fp:
                yaml.dump(self.input_dict,fp)

            prerunFiles = os.listdir(os.getcwd())
            prerunFiles.append(nbName)

            # FIXME: run in background. wait or check status.
            submitCommand = SubmitCommand()
            submitCommand.setLocal()
            submitCommand.setCommand("papermill")
            submitCommand.setCommandArguments(["-f","inputs.yaml",simToolLocation['notebookPath'],nbName])
            submitCommand.show()
            try:
               result = submitCommand.submit()
            except:
               exitCode = 1
               print(traceback.format_exc())
            else:
               exitCode = result['exitCode']
               if exitCode != 0:
                   print("SimTool execution failed")

            os.chdir(cwd)

            self.db = DB(self.outname,dir=self.outdir)
            self.savedOutputs     = self.db.getSavedOutputs()
            self.savedOutputFiles = self.db.getSavedOutputFiles()
#           if len(self.savedOutputFiles) > 0:
#               print("Saved output files: %s" % (self.savedOutputFiles))

            requiredOutputs  = set(self.outputs.keys())
            deliveredOutputs = set(self.savedOutputs)
            missingOutputs = requiredOutputs - deliveredOutputs
            extraOutputs   = deliveredOutputs - requiredOutputs
            if 'simToolSaveErrorOccurred' in extraOutputs:
                extraOutputs.remove('simToolSaveErrorOccurred')
            if 'simToolAllOutputsSaved' in extraOutputs:
                extraOutputs.remove('simToolAllOutputsSaved')
            if len(missingOutputs) > 0:
                print("The following outputs are missing: %s" % (list(missingOutputs)))
            if len(extraOutputs) > 0:
                print("The following additional outputs were returned: %s" % (list(extraOutputs)))

            simToolSaveErrorOccurred = self.db.getSimToolSaveErrorOccurred()
#           print("simToolSaveErrorOccurred = %d" % (simToolSaveErrorOccurred))
            simToolAllOutputsSaved = self.db.getSimToolAllOutputsSaved()
#           print("simToolAllOutputsSaved = %d" % (simToolAllOutputsSaved))

            if cache:
                self.dstore.write_cache(self.outdir,prerunFiles,self.savedOutputFiles)
        else:
            self.db = DB(self.outname,dir=self.outdir)


    def getResultSummary(self):
        return self.db.nb.scrap_dataframe


    def read(self, name, display=False, raw=False):
        return self.db.read(name,display,raw)



class TrustedUserRun:
    """
    Prepare and run of a notebook as a trusted user.
    """

    def __init__(self,simToolLocation,inputs,run_name,cache):
        if simToolLocation['published']:
# Only published simTool can be run with trusted user
            nbName = simToolLocation['simToolName'] +'.ipynb'
            self.inputs = copy.deepcopy(inputs)
            self.input_dict = _get_inputs_dict(self.inputs,inputFileRunPrefix=Run.inputFileRunPrefix)
            self.inputFiles = _get_inputFiles(self.inputs)
            self.outputs = copy.deepcopy(getSimToolOutputs(simToolLocation))

# Create landing area for results
            if run_name is None:
                run_name = str(uuid.uuid4()).replace('-','')
            self.run_name = run_name
            self.outdir = os.path.join(get_experiment(),run_name)
            os.makedirs(self.outdir)
            self.outname = os.path.join(self.outdir,nbName)
 
            if Run.inputFileRunPrefix:
                inputFileRunPath = os.path.join(self.outdir,Run.inputFileRunPrefix)
                os.makedirs(inputFileRunPath)
                for inputFile in self.inputFiles:
                    call("cp -p %s %s" % (inputFile,inputFileRunPath),shell=True)
            else:
                for inputFile in self.inputFiles:
                    call("cp -p %s %s" % (inputFile,self.outdir),shell=True)

# Generate inputs file for cache comparison and/or job input
            inputsPath = os.path.join(self.outdir,'inputs.yaml')
            with open(inputsPath,'w') as fp:
                yaml.dump(self.input_dict,fp)

            submitCommand = SubmitCommand()
            submitCommand.setLocal()
            submitCommand.setCommand(os.path.join(os.sep,'apps','bin','ionhelperGetSimToolResult.sh'))
            submitCommand.setCommandArguments([simToolLocation['simToolName'],simToolLocation['simToolRevision'],inputsPath,self.outdir])
            submitCommand.show()
            try:
                result = submitCommand.submit()
            except:
                exitCode = 1
                print(traceback.format_exc())
            else:
                exitCode = result['exitCode']
                if exitCode == 0:
                   print("Found cached result")

            self.cached = exitCode == 0
            if not self.cached:
                submitCommand = SubmitCommand()
                submitCommand.setLocal()
                submitCommand.setCommand(os.path.join(os.sep,'apps','bin','ionhelperRunSimTool.sh'))
                submitCommand.setCommandArguments([simToolLocation['simToolName'],simToolLocation['simToolRevision'],inputsPath])
                submitCommand.show()
                try:
                    result = submitCommand.submit()
                except:
                    exitCode = 1
                    print(traceback.format_exc())
                else:
                    exitCode = result['exitCode']
                    if exitCode != 0:
                        print("SimTool execution failed")
                self.cached = exitCode == 0

                if self.cached:
#                   Retrieve result from cache
                    submitCommand = SubmitCommand()
                    submitCommand.setLocal()
                    submitCommand.setCommand(os.path.join(os.sep,'apps','bin','ionhelperGetSimToolResult.sh'))
                    submitCommand.setCommandArguments([simToolLocation['simToolName'],simToolLocation['simToolRevision'],inputsPath,self.outdir])
                    submitCommand.show()
                    try:
                        result = submitCommand.submit()
                    except:
                        exitCode = 1
                        print(traceback.format_exc())
                    else:
                        exitCode = result['exitCode']
                        if exitCode != 0:
                            print("Retrieval of generated cached result failed")
                else:
#                   Retrieve error result from ionhelper delivery
                    submitCommand = SubmitCommand()
                    submitCommand.setLocal()
                    submitCommand.setCommand(os.path.join(os.sep,'apps','bin','ionhelperLoadSimToolResult.sh'))
                    submitCommand.setCommandArguments([self.outdir])
                    submitCommand.show()
                    try:
                        result = submitCommand.submit()
                    except:
                        exitCode = 1
                        print(traceback.format_exc())
                    else:
                        exitCode = result['exitCode']
                        if exitCode != 0:
                            print("Retrieval of failed execution result failed")

            self.db = DB(self.outname,dir=self.outdir)
        else:
            print("The simtool %s/%s is not published" % (simToolLocation['simToolName'],simToolLocation['simToolRevision']))


    def getResultSummary(self):
        return self.db.nb.scrap_dataframe


    def read(self, name, display=False, raw=False):
        return self.db.read(name,display,raw)


class Run:
    """Runs a SimTool.

        A copy of the SimTool will be created in the subdirectory with the same
        name as the current experiment.  It will be run with the provided inputs.

        If cache is True and the tool is published, the global cache will be used.
        If the tool is not published, and cache is True, a local user cache will be used.

        Args:
            simtoolName: The name of a published SimTool or the path to a notebook
                containing a SimTool.
            simtoolRevision: The revision of a published SimTool
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
    ds_handler         = FileDataStore  # local files or NFS.  should be config option
    inputFileRunPrefix = '.notebookInputFiles'

    def __new__(cls,simToolLocation,inputs,run_name=None,cache=True,venue=None):
       # cls.__init__(cls,desc)
       if venue is None and submitAvailable:
          if simToolLocation['published'] and cache:
             venue = 'trusted'
          else:
             venue = 'local'

       if simToolLocation['simToolRevision'] is None:
          cache = False

       if   venue == 'local':
          newclass = SubmitLocalRun(simToolLocation,inputs,run_name,cache)
       elif venue == 'trusted' and cache: 
          newclass = TrustedUserRun(simToolLocation,inputs,run_name,cache)
       elif venue is None:
          newclass = LocalRun(simToolLocation,inputs,run_name,cache)
       else:
          raise ValueError('Bad venue/cache combination')

       return newclass


