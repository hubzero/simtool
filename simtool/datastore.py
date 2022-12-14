# @package      hubzero-simtool
# @file         datastore.py
# @copyright    Copyright (c) 2019-2021 The Regents of the University of California.
# @license      http://opensource.org/licenses/MIT MIT
# @trademark    HUBzero is a registered trademark of The Regents of the University of California.
#
import os
import stat
import json
from joblib import Memory
import uuid
import shutil
import warnings
import requests
import traceback

class FileDataStore:
   """
   A data store implemented on a shared file system.
   """
   USERCACHELOCATIONROOT = os.path.expanduser('~/data')

   def __init__(self,simtoolName,simtoolRevision,inputs,cacheLocationRoot=None):

      if cacheLocationRoot:
         self.cacheLocationRoot = cacheLocationRoot
      else:
         self.cacheLocationRoot = FileDataStore.USERCACHELOCATIONROOT

      self.cachedir    = os.path.join(self.cacheLocationRoot,'.simtool_cache',simtoolName,simtoolRevision)
      self.cachetabdir = os.path.join(self.cacheLocationRoot,'.simtool_cache_table',simtoolName,simtoolRevision)

#     print(simtoolName,simtoolRevision)
#     print(self.cacheLocationRoot)
#     print("cachedir    = %s" % (self.cachedir))
#     print("cachetabdir = %s" % (self.cachetabdir))
      if not os.path.isdir(self.cachedir):
         os.makedirs(self.cachedir)

      memory = Memory(cachedir=self.cachetabdir, verbose=0)

      @memory.cache
      def make_rname(*args):
         # uuid should be unique, but check just in case
         while True:
            fname = str(uuid.uuid4()).replace('-', '')
            if not os.path.isdir(os.path.join(self.cachedir, fname)):
               break
         return fname

#
# suppress this message:
#
# UserWarning: Persisting input arguments took 0.84s to run.
# If this happens often in your code, it can cause performance problems
# (results will be correct in all cases).
# The reason for this is probably some large input arguments for a wrapped
# function (e.g. large strings).
# THIS IS A JOBLIB ISSUE. If you can, kindly provide the joblib's team with an
# example so that they can fix the problem.
#
      with warnings.catch_warnings():
         warnings.simplefilter('ignore')
         self.rdir = os.path.join(self.cachedir, make_rname(inputs))


   def getSimToolSquidId(self):
      squidId = None
      if self.rdir:
         squidId = os.path.basename(self.rdir)

      return squidId


   @staticmethod
   def __copySimToolTreeAsLinks(sdir,ddir):
      simToolFiles = os.listdir(sdir)
      for simToolFile in simToolFiles:
         simToolPath = os.path.join(sdir,simToolFile)
         if os.path.isdir(simToolPath):
            shutil.copytree(simToolPath,os.path.join(ddir,simToolFile),copy_function=os.symlink)
         else:
            os.symlink(simToolPath,os.path.join(ddir,simToolFile))


   @staticmethod
   def __copySimToolTree(spath,ddir):
      if os.path.isdir(spath):
         sdir = os.path.realpath(os.path.abspath(spath))
         simToolFiles = os.listdir(sdir)
         destinationDir = os.path.join(ddir,os.path.basename(sdir))
         if not os.path.isdir(destinationDir):
            os.mkdir(destinationDir)
      else:
         sdir = os.path.dirname(os.path.realpath(os.path.abspath(spath)))
         simToolFiles = [os.path.basename(spath)]
         destinationDir = ddir

      for simToolFile in simToolFiles:
         simToolPath = os.path.join(sdir,simToolFile)
         if os.path.isdir(simToolPath):
            shutil.copytree(simToolPath,os.path.join(destinationDir,simToolFile))
         else:
            shutil.copy2(simToolPath,os.path.join(destinationDir,simToolFile))


   def read_cache(self,outdir):
      # reads cache and copies contents to outdir
      if os.path.exists(self.rdir):
#        print("CACHED. Fetching results from %s" % (self.cacheLocationRoot))
         self.__copySimToolTreeAsLinks(self.rdir,outdir)
         return True
      return False


   def write_cache(self,
                   sourcedir,
                   prerunFiles,
                   savedOutputFiles):
      # copy notebook to data store
      os.makedirs(self.rdir)

#     print("write_cache(sourcedir): %s" % (sourcedir))
#     print("write_cache(cachedir): %s" % (self.rdir))
      for prerunFile in prerunFiles:
         self.__copySimToolTree(os.path.join(sourcedir,prerunFile),self.rdir)
      for savedOutputFile in savedOutputFiles:
         savedDirectory,savedFile = os.path.split(savedOutputFile)
         if savedDirectory:
            cacheDirectory = os.path.join(self.rdir,savedDirectory)
            if not os.path.isdir(cacheDirectory):
               os.mkdir(cacheDirectory)
            self.__copySimToolTree(os.path.join(sourcedir,savedOutputFile),cacheDirectory)
         else:
            self.__copySimToolTree(os.path.join(sourcedir,savedOutputFile),self.rdir)

      for rootDir,dirNames,fileNames in os.walk(self.rdir):
         for fileName in fileNames:
            filePath = os.path.join(rootDir,fileName)
            os.chmod(filePath,os.stat(filePath).st_mode | stat.S_IROTH)
         for dirName in dirNames:
            dirPath = os.path.join(rootDir,dirName)
            os.chmod(dirPath,os.stat(dirPath).st_mode | stat.S_IROTH | stat.S_IXOTH)


   @staticmethod
   def readFile(path, out_type=None):
      """Reads the contents of an artifact file.

      Args:
          path: Path to the artifact
          out_type: The data type
      Returns:
          The contents of the artifact encoded as specified by the
          output type.  So for an Array, this will return a Numpy array,
          for an Image, an IPython Image, etc.
      """
      if out_type is None:
         with open(path, 'rb') as fp:
            res = fp.read()
         return res
      return out_type.read_from_file(path)


   @staticmethod
   def readData(data, out_type=None):
      """Reads the contents of an artifact data.

      Args:
          data: Artifact data
          out_type: The data type
      Returns:
          The contents of the artifact encoded as specified by the
          output type.  So for an Array, this will return a Numpy array,
          for an Image, an IPython Image, etc.
      """
      if out_type is None:
         return data
      return out_type.read_from_data(data)


class WSDataStore:
   """
   A data store implemented as a web service.
   """
   def __init__(self,simtoolName,simtoolRevision,inputs,cacheLocationRoot):

      self.cacheLocationRoot = cacheLocationRoot.rstrip('/') + '/'

      try:
         # Request the signature for the set of inputs
         squidid = requests.get(self.cacheLocationRoot + "squidid",
                                headers = {'Content-Type': 'application/json'},
                                data = json.dumps({'simtoolName':simtoolName,
                                                   'simtoolRevision':simtoolRevision,
                                                   'inputs':inputs}
                                                 )
                               )
         sid = squidid.json()
         # The signature id (squidid) is saved on the rdir variable instead of the path to the directory
         self.rdir = sid['id']
      except Exception as e:
         print("squidId determination failed")
         print(traceback.format_exc())
         # If there is any error obtaining the squidid the mode is changed to global. should it be "local"?
         self.rdir = None


   def getSimToolSquidId(self):
      return self.rdir


   def read_cache(self, outdir):
      # reads cache and copies contents to outdir
      try:
         squidid = self.rdir
         # request the list of files given the squidid
         cachefile = requests.get(self.cacheLocationRoot + "squidlist",
                                  headers = {'Content-Type': 'application/json'},
                                  data = json.dumps({'squidid':squidid})
                                 )
         results = cachefile.json()
         if len(results) == 0:
            return False;
         if not os.path.isdir(outdir):
            os.mkdir(outdir)
         # for each file on the response, download the blob
         for result in results:
            if "_._" in result['name']:
               outputfile = result['name'].split("_._")
               outputname = outputfile[-1]
               outputdir = os.path.join(outdir,os.sep.join(outputfile[:-1]))
               if not os.path.isdir(outputdir):
                  os.makedirs(outputdir)
            else:
               outputdir = outdir
               outputname = result['name']
            # request the file and save on the proper user file directory
            r = requests.get(self.cacheLocationRoot + "files/" + result['id'],
                             headers = {"Cache-Control": "no-cache"},
                             params = {"download": "true"}
                            )
            with open(os.path.join(outputdir,outputname), 'wb') as fp:
               fp.write(r.content)
         return True
      except Exception as e:
         return False


   def write_cache(self,
                   sourcedir,
                   prerunFiles,
                   savedOutputFiles):
      # copy notebook to data store
      cacheFps = []
      try:
         squidid = self.rdir
         cacheFilePaths = []
         # loop prerunFiles, save full paths
         for prerunFile in prerunFiles:
            cacheFilePath = os.path.realpath(os.path.join(sourcedir,prerunFile))
            if os.path.isdir(cacheFilePath):
               for rootPath,dirs,files in os.walk(cacheFilePath):
                  for cacheFile in files:
                     cacheFilePaths.append(os.path.join(rootPath,cacheFile))
            else:
               cacheFilePaths.append(cacheFilePath)
         # loop savedOutputFiles, save full paths
         for savedOutputFile in savedOutputFiles:
            cacheFilePath = os.path.realpath(os.path.join(sourcedir,savedOutputFile))
            if os.path.isdir(cacheFilePath):
               for rootPath,dirs,files in os.walk(cacheFilePath):
                  for cacheFile in files:
                     cacheFilePaths.append(os.path.join(rootPath,cacheFile))
            else:
               cacheFilePaths.append(cacheFilePath)

         # loop all files found and change the path separtor from / to _._, flattening the path.
         cacheFiles = []
         rootPath = os.path.realpath(sourcedir)
         for cacheFilePath in cacheFilePaths:
            relativePath = os.path.relpath(cacheFilePath,rootPath)
            cacheFp = open(relativePath,'rb')
            cacheFps.append(cacheFp)
            if os.path.dirname(relativePath):
               cacheFiles.append(('file',("_._".join(relativePath.split(os.sep)),cacheFp)))
            else:
               cacheFiles.append(('file',cacheFp))

         # Store the files on the server
#        print("squidid: %s" % (squidid))
#        print("files: %s" % (cacheFiles))
         res = requests.put(self.cacheLocationRoot + "squidlist",
                            data = {'squidid':squidid},
                            files = cacheFiles
                           )
         if res.status_code != 200:
            print("res['status_code']: %s" % (res.status_code))
            print("res['reason']: %s" % (res.reason))
            print("res['text']: %s" % (res.text))
      except Exception as e:
#        print("e: %s" % (e))
         raise e;
      finally:
         for cacheFp in cacheFps:
            cacheFp.close()
         del cacheFps


   @staticmethod
   def readFile(path, out_type=None):
      """Reads the contents of an artifact file.

      Args:
          path: Path to the artifact
          out_type: The data type
      Returns:
          The contents of the artifact encoded as specified by the
          output type.  So for an Array, this will return a Numpy array,
          for an Image, an IPython Image, etc.
      """
      if out_type is None:
         with open(path, 'rb') as fp:
            res = fp.read()
         return res
      return out_type.read_from_file(path)


   @staticmethod
   def readData(data, out_type=None):
      """Reads the contents of an artifact data.

      Args:
          data: Artifact data
          out_type: The data type
      Returns:
          The contents of the artifact encoded as specified by the
          output type.  So for an Array, this will return a Numpy array,
          for an Image, an IPython Image, etc.
      """
      if out_type is None:
         return data
      return out_type.read_from_data(data)


