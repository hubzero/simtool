import os
from joblib import Memory
import uuid

class FileDataStore:
    """
    A data store implemented on a shared file system.
    """
    USER_FILEDIR = os.path.expanduser('~/data/.simtool_cache')
    USER_FILETABDIR = os.path.expanduser('~/data/.simtool_cache_table')
    GLOBAL_FILEDIR = '/simdata/results/cache'
    GLOBAL_FILETABDIR = '/simdata/results/cache_table'

    def __init__(self, simtool_name, inputs, published):

        if published:
            self.cachedir = os.path.join(FileDataStore.GLOBAL_FILEDIR, simtool_name)
            self.cachetabdir = os.path.join(FileDataStore.GLOBAL_FILETABDIR, simtool_name)
        else:
            self.cachedir = os.path.join(FileDataStore.USER_FILEDIR, simtool_name)
            self.cachetabdir = os.path.join(FileDataStore.USER_FILETABDIR, simtool_name)
        
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

        self.rdir = os.path.join(self.cachedir, make_rname(inputs))

    @staticmethod
    def read(path, out_type=None):
        """Reads the contents of an artifact.

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
