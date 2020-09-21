import os
import sys
import re
import glob
import nbformat
from papermill.iorw import load_notebook_node
import yaml
import jsonpickle
from .params import Params

def parse(inputs):
   d = Params()
   for i in inputs:
      t = inputs[i]['type']
      if t in Params.types:
         d[i] = Params.types[t](**inputs[i])
      else:
         print('Unknown type:', t, file=sys.stderr)
   return d


def _get_extra_files(nbPath):
   """ Internal function to search the notebook for a cell tagged
   'FILES' with content 'EXTRA_FILES=xxx' where 'xxx' is a list of files
   or '*'
   """
   ecell = None
   nb = load_notebook_node(nbPath)
   for cell in nb.cells:
      if 'FILES' in cell.metadata.tags:
         ecell = cell['source']
         break
   if ecell is None:
      return None

   extra = None
   for line in ecell.split('\n'):
      if line.startswith('EXTRA_FILES'):
         extra = line
         break
   if extra is None:
      print("WARNING: cannot parse FILE cell:")
      return None

   try:
      val = extra.split('=')[1].replace("'", '"')
      return jsonpickle.loads(val)
   except:
      print("WARNING: cannot parse:", extra)

   return None


def _getSimToolDescription(nbPath):
   """ Internal function to search the notebook for a cell tagged
   'DESCRIPTION' with content 'DESCRIPTION=xxx' where 'xxx' is a
   string describing the simtool
   """
   ecell = None
   nb = load_notebook_node(nbPath)
   for cell in nb.cells:
      if 'DESCRIPTION' in cell.metadata.tags:
         ecell = cell['source']
         break
   if ecell is None:
      return None

   descriptionText = ecell.split('=')[1:]
   descriptionText = ''.join(descriptionText)
   descriptionText = descriptionText.strip(' ')
   if   descriptionText.startswith('"""') and descriptionText.endswith('"""'):
      descriptionText = descriptionText[3:-3]
   elif descriptionText.startswith('"') and descriptionText.endswith('"'):
      descriptionText = descriptionText[1:-1]
   elif descriptionText.startswith("'") and descriptionText.endswith("'"):
      descriptionText = descriptionText[1:-1]

   return descriptionText


def getGetSimToolNameRevisionFromEnvironment():
   simToolName     = None
   simToolRevision = None
   try:
      submitApplicationRevision = os.environ['SUBMIT_APPLICATION_REVISION']
   except:
      pass
   else:
      varParts = submitApplicationRevision.split('_')
      simToolRevision = varParts[-1]
      simToolName     = '_'.join(varParts[0:-1])

   return simToolName,simToolRevision


def _getSimToolNotebookMetaData(nbPath):
   simToolNotebookMetaData = {}
   simToolNotebookMetaData['name']     = None
   simToolNotebookMetaData['revision'] = None
   simToolNotebookMetaData['state']    = None

   try:
      nb = nbformat.read(nbPath,nbformat.NO_CONVERT)
   except:
      pass
   else:
      try:
         metadata = nb['metadata']['simTool_info']
      except (AttributeError,KeyError) as err:
         pass
      else:
         try:
            name = metadata['name']
         except:
            pass
         else:
            simToolNotebookMetaData['name'] = name

         try:
            revision = metadata['revision']
         except:
            pass
         else:
            simToolNotebookMetaData['revision'] = "r%d" % (revision)

         try:
            state = metadata['state']
         except:
            pass
         else:
            simToolNotebookMetaData['state'] = state

   return simToolNotebookMetaData


def findSimToolNotebook(simToolName,simToolRevision=None):
   """Lookup simtool by name and revision.

   Returns:
       A dictionary containing -
           notebookPath    - the full path name of the simtool notebook,
           simToolName     - the simtool shortname
           simToolRevision - the simtool revision (if installed or published)
           published       - boolean which is True if the notebook is published
   """
   simToolLocation = {}
   simToolLocation['notebookPath']    = None
   simToolLocation['simToolName']     = None
   simToolLocation['simToolRevision'] = None
   simToolLocation['published']       = None

   if   simToolRevision and not simToolName.endswith('.ipynb'):
      simToolNotebook = os.path.basename(simToolName) + '.ipynb'
      notebookPath = os.path.join(os.sep,'apps',simToolName,simToolRevision,'simtool',simToolNotebook)
      if os.path.exists(notebookPath):
         # look for installed or published revision in /apps/name/revision/simtool/
         simToolLocation['notebookPath']    = os.path.realpath(notebookPath)
         simToolLocation['simToolName']     = os.path.basename(simToolName)
         simToolLocation['simToolRevision'] = os.path.basename(os.path.dirname(os.path.dirname(simToolLocation['notebookPath'])))
         # verify pubication status - sample published notebook reference to simtool
         simToolNotebookMetaData = _getSimToolNotebookMetaData(simToolLocation['notebookPath'])
         if simToolNotebookMetaData['name'] == simToolLocation['simToolName'] and \
            simToolNotebookMetaData['revision'] == simToolLocation['simToolRevision'] and \
            simToolNotebookMetaData['state'] == 'published':
            simToolLocation['published'] = True
         else:
            simToolLocation['published'] = False
#           print(simToolNotebookMetaData['name'],simToolLocation['simToolName'])
#           print(simToolNotebookMetaData['revision'],simToolLocation['simToolRevision'])
#           print(simToolNotebookMetaData['state'])
      else:
         notebookPath = os.path.join(simToolName,simToolRevision,'simtool',simToolNotebook)
         if os.path.exists(notebookPath):
            # look for notebook in name/revision/simtool/
            simToolLocation['notebookPath']    = os.path.realpath(notebookPath)
            simToolLocation['simToolName']     = os.path.basename(simToolName)
            simToolLocation['simToolRevision'] = simToolRevision
            simToolLocation['published']       = False
   elif not simToolName.endswith('.ipynb'):
      # revision not specified
      # look for latest published revision in /apps
      simToolNotebook = os.path.basename(simToolName) + '.ipynb'
      notebookPathPattern = os.path.join(os.sep,'apps',simToolName,'*','simtool',simToolNotebook)
      newestRevision = 0
      for notebookPath in glob.glob(notebookPathPattern):
         revision = notebookPath.split(os.sep)[3]
         if revision.startswith('r'):
            simToolNotebookMetaData = _getSimToolNotebookMetaData(notebookPath)
            if simToolNotebookMetaData['state'] == 'published':
               revisionNumber = int(revision[1:])
               if revisionNumber > newestRevision:
                  newestRevision = revisionNumber
                  simToolLocation['notebookPath']    = os.path.realpath(notebookPath)
                  simToolLocation['simToolName']     = os.path.basename(simToolName)
                  simToolLocation['simToolRevision'] = os.path.basename(os.path.dirname(os.path.dirname(simToolLocation['notebookPath'])))
                  simToolLocation['published']       = True

      if simToolLocation['published'] is None:
         notebookPath = os.path.join(simToolName,simToolNotebook)
         if os.path.exists(notebookPath):
            # look for notebook in name
            simToolLocation['notebookPath']    = os.path.realpath(notebookPath)
            simToolLocation['simToolName']     = os.path.basename(simToolName)
            simToolLocation['simToolRevision'] = None
            simToolLocation['published']       = False
         else:
            notebookPath = os.path.join(simToolName,'simtool',simToolNotebook)
            if os.path.exists(notebookPath):
               # look for notebook in name
               simToolLocation['notebookPath']    = os.path.realpath(notebookPath)
               simToolLocation['simToolName']     = os.path.basename(simToolName)
               simToolLocation['simToolRevision'] = None
               simToolLocation['published']       = False
               notebookPath = simToolLocation['notebookPath'].split(os.sep)
               notebookPath.pop(0)
               if len(notebookPath) == 5:
                  revision = notebookPath.pop(2)
                  if os.sep.join(notebookPath) == \
                     os.path.join('apps',simToolLocation['simToolName'],'simtool',simToolNotebook):
                     simToolLocation['simToolRevision'] = revision
                     # verify pubication status - sample published notebook reference to simtool
                     simToolNotebookMetaData = _getSimToolNotebookMetaData(simToolLocation['notebookPath'])
                     if simToolNotebookMetaData['name'] == simToolLocation['simToolName'] and \
                        simToolNotebookMetaData['revision'] == simToolLocation['simToolRevision'] and \
                        simToolNotebookMetaData['state'] == 'published':
                        simToolLocation['published'] = True
   elif os.path.isfile(simToolName):
      # *.ipynb - must be a local (non-published) notebook
      simToolLocation['notebookPath']    = os.path.realpath(simToolName)
      simToolLocation['simToolName']     = os.path.splitext(os.path.basename(simToolName))[0]
      simToolLocation['simToolRevision'] = None
      simToolLocation['published']       = False
   else:
      if simToolRevision:
         raise FileNotFoundError('Revision "%s" of simtool named "%s" not found' % (simToolRevision,simToolName))
      else:
         raise FileNotFoundError('No simtool named "%s, "' % (simToolName))

   return simToolLocation


def findInstalledSimToolNotebooks(querySimToolName=None,
                                  returnString=True):
   """Find all the revisions of simToolName.

   Returns:
      Ordered lists of installed and published revisions
   """
   installedSimToolRevisions = {}

   if querySimToolName:
      simToolNames = [querySimToolName]
   else:
      appsPath = os.path.join(os.sep,'apps')
      appsDirs = os.listdir(appsPath)
      simToolNames = []
      for appsDir in appsDirs:
         simToolPath = os.path.join(os.sep,'apps',appsDir)
         if os.path.isdir(simToolPath):
            simToolNames.append(appsDir)
   simToolNames.sort()

   reFiles = re.compile("^r[0-9]+$")
   for simToolName in simToolNames:
      simToolPath = os.path.join(os.sep,'apps',simToolName)
      try:
         dirFiles = os.listdir(simToolPath)
      except:
         pass
      else:
         matchingFiles = filter(reFiles.search,dirFiles)
         simToolRevisions = []
         for matchingFile in matchingFiles:
            try:
               revisionIndex = int(matchingFile[1:])
            except:
               pass
            else:
               simToolRevisions.append(revisionIndex)
         simToolRevisions.sort()
         simToolRevisions = [ 'r%d' % (revision) for revision in simToolRevisions ]

         for simToolRevision in simToolRevisions:
            nbPath = os.path.join(simToolPath,simToolRevision,'simtool',"%s.ipynb" % (simToolName))
            if os.path.exists(nbPath):
               simToolNotebookMetaData = _getSimToolNotebookMetaData(nbPath)
               if   simToolNotebookMetaData['state'] == 'installed':
                  description = _getSimToolDescription(nbPath)
                  if not simToolName in installedSimToolRevisions:
                     installedSimToolRevisions[simToolName] = {}
                  if not 'installed' in installedSimToolRevisions[simToolName]:
                     installedSimToolRevisions[simToolName]['installed'] = {}
                  installedSimToolRevisions[simToolName]['installed'][simToolRevision] = description
               elif simToolNotebookMetaData['state'] == 'published':
                  description = _getSimToolDescription(nbPath)
                  if not simToolName in installedSimToolRevisions:
                     installedSimToolRevisions[simToolName] = {}
                  if not 'published' in installedSimToolRevisions[simToolName]:
                     installedSimToolRevisions[simToolName]['published'] = {}
                  installedSimToolRevisions[simToolName]['published'][simToolRevision] = description

   if returnString:
      installedSimToolRevisions = yaml.dump(installedSimToolRevisions,indent=3)
      installedSimToolRevisions = installedSimToolRevisions.replace("\n\n", "\n  ").strip()

   return installedSimToolRevisions


def searchForSimTool(simToolName,simToolRevision=None):
   foundIt = True
   if simToolRevision is None:
      notebookPath = os.path.join('simtool',"%s.ipynb" % (simToolName))
      if not os.path.islink(notebookPath):
         notebookPath = os.path.join('..','simtool',"%s.ipynb" % (simToolName))
         if not os.path.islink(notebookPath):
            foundIt = False

      if foundIt:
#        verify link to installed (/apps) version
         if os.path.isfile(notebookPath):
            notebookPath = os.path.realpath(os.path.abspath(notebookPath))
            installedNotebookPattern = os.path.join(os.sep,'apps',simToolName,'(r[0-9]+)','simtool',"%s.ipynb" % (simToolName))
            reInstalledNotebookPattern = re.compile("^%s$" % (installedNotebookPattern))
            match = reInstalledNotebookPattern.match(notebookPath)
            if match:
               simToolLocation = {}
               simToolLocation['notebookPath']    = notebookPath
               simToolLocation['simToolName']     = simToolName
               simToolLocation['simToolRevision'] = match.group(1)
               simToolNotebookMetaData = _getSimToolNotebookMetaData(simToolLocation['notebookPath'])
               if simToolNotebookMetaData['name'] == simToolLocation['simToolName'] and \
                  simToolNotebookMetaData['revision'] == simToolLocation['simToolRevision'] and \
                  simToolNotebookMetaData['state'] == 'published':
                  simToolLocation['published'] = True
               else:
                  simToolLocation['published'] = False
            else:
               foundIt = False
         else:
#           broken link
            foundIt = False

      if not foundIt:
# Not an installed SimTool
         foundIt = True

         notebookPath = os.path.join('simtool',"%s.ipynb" % (simToolName))
         if not os.path.isfile(notebookPath):
            notebookPath = os.path.join('..','simtool',"%s.ipynb" % (simToolName))
            if not os.path.isfile(notebookPath):
               foundIt = False

         if foundIt:
            notebookPath = os.path.realpath(os.path.abspath(notebookPath))
            simToolLocation = {}
            simToolLocation['notebookPath']    = notebookPath
            simToolLocation['simToolName']     = simToolName
            simToolLocation['simToolRevision'] = None
            simToolLocation['published']       = False

      if not foundIt:
         foundIt = True
         try:
            simToolLocation = findSimToolNotebook(simToolName,'current')
         except:
            foundIt = False
         else:
            notebookPath = simToolLocation['notebookPath']
            if notebookPath is None:
               foundIt = False
            else:
               simToolLocation['simToolRevision'] = os.path.basename(os.path.dirname(os.path.dirname(notebookPath)))

      if not foundIt:
         foundIt = True
         try:
            simToolLocation = findSimToolNotebook(simToolName,'dev')
         except:
            foundIt = False
         else:
            notebookPath = simToolLocation['notebookPath']
            if notebookPath is None:
               foundIt = False
            else:
               simToolLocation['simToolRevision'] = os.path.basename(os.path.dirname(os.path.dirname(notebookPath)))
   else:
      try:
         simToolLocation = findSimToolNotebook(simToolName,simToolRevision)
      except:
         foundIt = False
      else:
         if simToolLocation['notebookPath'] is None:
            foundIt = False

   if not foundIt:
      simToolLocation = {}
      simToolLocation['notebookPath']    = None
      simToolLocation['simToolName']     = None
      simToolLocation['simToolRevision'] = None
      simToolLocation['published']       = None

   return simToolLocation


def _find_simTool(simToolName,simToolRevision=None):
    """Lookup simtool by name and revision.

    Returns:
        A tuple containing the full path name of the simtool notebook,
        the tool name, the tool revision (if published) and a boolean which is True if the notebook
        is published
    """
    if   simToolRevision and not simToolName.endswith('.ipynb'):
        simToolNotebook = simToolName + '.ipynb'
        prefix = 'apps'
        if   os.path.exists(os.path.join(prefix,simToolName,simToolRevision,simToolNotebook)):
            return (os.path.join(prefix,simToolName,simToolRevision,simToolNotebook),simToolName,simToolRevision,True)
        elif os.path.exists(os.path.join(simToolName,simToolRevision,simToolNotebook)):
            tool_name = os.path.splitext(os.path.basename(simToolName))[0]
            return (os.path.join(os.path.realpath(simToolName),simToolRevision,simToolNotebook),tool_name,simToolRevision,False)
    elif not simToolName.endswith('.ipynb'):
        simToolNotebook = simToolName + '.ipynb'
        if os.path.exists(os.path.join(simToolName,simToolRevision,simToolNotebook)):
            tool_name = os.path.splitext(os.path.basename(simToolName))[0]
            return (os.path.join(os.path.realpath(simToolName),simToolRevision,simToolNotebook),tool_name,simToolRevision,False)
    elif os.path.isfile(simToolName):
        # must be a local (non-published) notebook
        tool_name = os.path.splitext(os.path.basename(simToolName))[0]
        return (os.path.realpath(simToolName), tool_name, None,False)
    else:
        if simToolRevision:
            raise FileNotFoundError('Revision "%s" of simtool named "%s" not found' % (simToolRevision,simToolName))
        else:
            raise FileNotFoundError('No simtool named "%s, "' % (simToolName))


def getNotebookInputs(nb):
   incell = None
   for cell in nb.cells:
      if cell['source'].startswith('%%yaml INPUTS'):
         incell = cell['source']
         break
   if incell is None:
      return None
   # remove first line (cell magic)
   incell = incell.split('\n', 1)[1]
   input_dict = yaml.load(incell, Loader=yaml.FullLoader)

   return parse(input_dict)


def getSimToolInputs(simToolLocation):
   nbPath = simToolLocation['notebookPath']
   nb = load_notebook_node(nbPath)

   return getNotebookInputs(nb)


def _get_inputs_dict(inputs,
                     inputFileRunPrefix=None):
   if type(inputs) == dict:
      return inputs
   inputsDict = {}
   for i in inputs:
      value = inputs[i].serialValue

      checkForFile = False
      try:
         if isinstance(value,basestring):
            checkForFile = True
      except NameError:
         if isinstance(value,str):
            checkForFile = True

      if checkForFile:
         if value.startswith('file://'):
            path = value[7:]
            fileName = os.path.basename(path)
            if inputFileRunPrefix:
               value = 'file://' + os.path.join(inputFileRunPrefix,fileName)
            else:
               value = 'file://' + fileName
      inputsDict[i] = value

   return inputsDict


def _get_inputs_cache_dict(inputs):
   if type(inputs) == dict:
      return inputs
   inputsCacheDict = {}
   for i in inputs:
      value = inputs[i].serialValue

      checkForFile = False
      try:
         if isinstance(value,basestring):
            checkForFile = True
      except NameError:
         if isinstance(value,str):
            checkForFile = True

      if checkForFile:
         if value.startswith('file://'):
            path = value[7:]
            with open(path,'rb') as fp:
               value = fp.read()
      inputsCacheDict[i] = value

   return inputsCacheDict


def _get_inputFiles(inputs):
   if type(inputs) == dict:
      return None

   inputFiles = []
   for i in inputs:
      try:
         if inputs[i].file:
            inputFiles.append(inputs[i].file)
      except:
         pass
   return inputFiles


def getNotebookOutputs(nb):
   incell = None
   for cell in nb.cells:
      if cell['source'].startswith('%%yaml OUTPUTS'):
         incell = cell['source']
         break
   if incell is None:
      return None
   # remove first line (cell magic)
   incell = incell.split('\n', 1)[1]
   out_dict = yaml.load(incell, Loader=yaml.FullLoader)

   return parse(out_dict)


def getSimToolOutputs(simToolLocation):
   nbPath = simToolLocation['notebookPath']
   nb = load_notebook_node(nbPath)

   return getNotebookOutputs(nb)


