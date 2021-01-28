import os
import json
from joblib import Memory
import uuid
from subprocess import call
import shutil
import warnings
import requests

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


   def read_cache(self, outdir):
      # reads cache and copies contents to outdir
      if os.path.exists(self.rdir):
#        print("CACHED. Fetching results from %s" % (self.cacheLocationRoot))
         call('/bin/cp -sRf %s/. %s' % (self.rdir, outdir), shell=True)
         return True
      return False


   def write_cache(self,
                   sourcedir,
                   prerunFiles,
                   savedOutputFiles):
      # copy notebook to data store
      os.makedirs(self.rdir)

      for prerunFile in prerunFiles:
         call('/bin/cp -prL %s/%s %s' % (sourcedir,prerunFile,self.rdir), shell=True)
      for savedOutputFile in savedOutputFiles:
         call('/bin/cp -prL %s/%s %s' % (sourcedir,savedOutputFile,self.rdir), shell=True)

      call('/usr/bin/find %s -type d -exec chmod o+rx {} \;' % (self.rdir), shell=True)
      call('/usr/bin/find %s -type f -exec chmod o+r {} \;' % (self.rdir), shell=True)


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
#  SQUIDDB_WS = 'http://instanton2.dev.nanohub.org:5000/api/v1'

   def __init__(self,simtoolName,simtoolRevision,inputs,cacheLocationRoot):

      self.cacheLocationRoot = cacheLocationRoot.rstrip('/') + '/'

      try:
         # Request the signature for the set of inputs
         squidid = requests.get(
             self.cacheLocationRoot + "squidid",
             headers = {'Content-Type': 'application/json'},
             data = json.dumps({
                 'simtoolName':simtoolName,
                 'simtoolRevision':simtoolRevision,
                 'inputs':inputs,
             })
         )
         sid = squidid.json()
         # The signature id (squidid) is saved on the rdir variable instead of the path to the directory
         self.rdir = sid['id']
      except Exception as e:
         # If there is any error obtaining the squidid the mode is changed to global. should it be "local"?
         self.rdir = None


   def read_cache(self, outdir):
      # reads cache and copies contents to outdir
      try:
         squidid = self.rdir
         # request the list of files given the squidid
         cachefile = requests.get(
             self.cacheLocationRoot + "squidlist",
             headers = {'Content-Type': 'application/json'},
             data = json.dumps({
                 'squidid':squidid,
             })
         )
         results = cachefile.json()
         if len(results) == 0:
            return False;
         if not os.path.isdir(outdir):
            os.mkdir(outdir)
         # for each file on the response, download the blob
         for result in results:
            outputname = result['name']
            outputdir = outdir
            # WARNING: filenames with '_._' mean they are included on a directory, only 1 level is supported
            if "_._" in outputname:
               outputfile = outputname.split("_._")
               outputname = outputfile[1]
               outputdir = outdir + "/" + outputfile[0]
               if not os.path.isdir(outputdir):
                  os.mkdir(outputdir)
            # request the file and save on the proper user file directory
            r = requests.get(
                self.cacheLocationRoot + "files/" + result['id'],
                headers = {"Cache-Control": "no-cache"},
                params = {"download": "true"}
            )
            open(os.path.join(outputdir,outputname), 'wb').write(r.content)
         return True
      except Exception as e:
         return False
 
 
   def write_cache(self,
                   sourcedir,
                   prerunFiles,
                   savedOutputFiles):
      # copy notebook to data store
      try:
         squidid = self.rdir
         files = []
         dirs = []
         # loop prerunFiles, save file blobs on the list or the folder to be processed later
         for prerunFile in prerunFiles:
            path = sourcedir+"/"+prerunFile
            if os.path.isfile(path):
               files.append(('file',open(path,'rb')))
            else:
               dirs.append(prerunFile)
         # loop savedOutputFiles, save file blobs on the list or the folder to be processed later
         for savedOutputFile in savedOutputFiles:
            path = sourcedir+"/"+savedOutputFile
            if os.path.isfile(path):
               files.append(('file',open(path,'rb')))
            else:
               dirs.append(savedOutputFile)
 
         # loop all folders found and change the filename to include '_._' only one recursion level supported
         for file in dirs:
            for f in os.listdir(sourcedir+"/"+file):
               path = sourcedir+"/"+file+"/"+f
               if os.path.isfile(path):
                  files.append(('file',(file + "_._" + f, open(path,'rb'))))
 
         # Store the files on the server
         res = requests.put(
             self.cacheLocationRoot + "squidlist",
             data = {'squidid':squidid},
             files = files
         )
      except Exception as e:
         raise e;
 
 
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
 
 
