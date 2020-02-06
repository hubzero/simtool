import os
from joblib import Memory
import uuid
from subprocess import call
import shutil
import warnings

class FileDataStore:
    """
    A data store implemented on a shared file system.
    """
    USER_FILEDIR    = os.path.expanduser('~/data/.simtool_cache')
    USER_FILETABDIR = os.path.expanduser('~/data/.simtool_cache_table')
    GLOBAL_FILEDIR    = '/data/tools/simtools/Archive/cache'
    GLOBAL_FILETABDIR = '/data/tools/simtools/Archive/cache_table'

    def __init__(self,simtoolName,simtoolRevision,inputs,cacheName):

        self.cacheName = cacheName
        if self.cacheName == 'global':
            self.cachedir    = os.path.join(FileDataStore.GLOBAL_FILEDIR,simtoolName,simtoolRevision)
            self.cachetabdir = os.path.join(FileDataStore.GLOBAL_FILETABDIR,simtoolName,simtoolRevision)
        else:
            self.cachedir    = os.path.join(FileDataStore.USER_FILEDIR,simtoolName,simtoolRevision)
            self.cachetabdir = os.path.join(FileDataStore.USER_FILETABDIR,simtoolName,simtoolRevision)

#       print(simtoolName,simtoolRevision)
#       print(self.cacheName)
#       print(FileDataStore.USER_FILEDIR)
#       print(FileDataStore.USER_FILETABDIR)
#       print(FileDataStore.GLOBAL_FILEDIR)
#       print(FileDataStore.GLOBAL_FILETABDIR)

#       print("cachedir    = %s" % (self.cachedir))
#       print("cachetabdir = %s" % (self.cachetabdir))
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
            if self.cacheName == 'global':
                print("CACHED. Fetching results from Data Store.")
            else:
                print("CACHED. Fetching results from user cache. (%s)" % self.USER_FILEDIR)
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

