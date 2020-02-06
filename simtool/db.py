import os
import copy
import scrapbook as sb
from IPython.display import display as idisplay

from .utils import parse, getNotebookOutputs, Params
from .datastore import FileDataStore
from .encode import JsonEncoder

class DB(object):

    def __init__(self, outputs, dir=None):
        if type(outputs) is str:
            self.nb = sb.read_notebook(outputs)
            self.out = getNotebookOutputs(self.nb)
        else:
            self.out = parse(outputs)
            self.outputsToBeSaved = copy.deepcopy(self.out.keys())
            self.setSimToolSaveErrorOccurred(0)
            self.setSimToolAllOutputsSaved(0)

        self.dir = dir
        if self.dir is None:
            self.dir = os.getcwd()


    def getSimToolSaveErrorOccurred(self):
        simToolSaveErrorOccurred = DB.encoder.decode(self.read('simToolSaveErrorOccurred',display=False,raw=False))
        return simToolSaveErrorOccurred


    def setSimToolSaveErrorOccurred(self, value):
        data = DB.encoder.encode(value)
        sb.glue('simToolSaveErrorOccurred', data)


    def getSimToolAllOutputsSaved(self):
        simToolAllOutputsSaved = DB.encoder.decode(self.read('simToolAllOutputsSaved',display=False,raw=False))
        return simToolAllOutputsSaved


    def setSimToolAllOutputsSaved(self, value):
        data = DB.encoder.encode(value)
        sb.glue('simToolAllOutputsSaved', data)


    @staticmethod
    def _make_ref(filename):
        return 'file://' + filename


    @staticmethod
    def _get_ref(val):
        if type(val) is not str:
            return None
        if val.startswith('file://'):
            return val[7:]
        return None


    def save(self, name, value=None, display=False, file=None, force=False):
        """Save output to the results database.

        Outputs are saved as key-value entries in the notebook metadata.  Large output
        will typically be in files, so the value saved in the notebook will be a filename.

        Args:
            name: Name of the output.
            value: Value. Not required if the output is in a file.
            display: Should the value be displayed as output for the cell?
            file: Name of the file with the value.
            force: Ignore output schema and write value anyway.
        """
        if   name not in self.out and force is False:
            raise ValueError('\"%s\" not in output schema!' % name)
        elif name in self.out:
# do data validation
            simToolObject = copy.deepcopy(self.out[name])
            try:
                if file != None:
                    simToolObject.file = file
                else:
                    simToolObject.value = value
            except ValueError as e:
                data = DB.encoder.encode(None)
                sb.glue(name, data)
                self.setSimToolSaveErrorOccurred(1)
                raise ValueError("""save output "%s" failed: %s""" % (name,e.args[0]))
            finally:
                del simToolObject

        # FIXME: If output value is oversized, write it to a file
        # and glue a reference.

        data = None
        if file == None:
            path = self._get_ref(value)
            if path:
                if not os.path.isfile(path):
                    data = DB.encoder.encode(None)
                    sb.glue(name, data)
                    self.setSimToolSaveErrorOccurred(1)
                    raise FileNotFoundError(f'File "{path}" not found.')
                if path.startswith("/") or path.startswith(".."):
                    data = DB.encoder.encode(None)
                    sb.glue(name, data)
                    self.setSimToolSaveErrorOccurred(1)
                    raise FileNotFoundError('File must be in the local directory.')
                data = self._make_ref(path)

        if not data:
            if file:
                if value:
                    data = DB.encoder.encode(None)
                    sb.glue(name, data)
                    self.setSimToolSaveErrorOccurred(1)
                    raise ValueError('Cannot set both "value" and "file" in save()')
                if not os.path.isfile(file):
                    data = DB.encoder.encode(None)
                    sb.glue(name, data)
                    self.setSimToolSaveErrorOccurred(1)
                    raise FileNotFoundError(f'File "{file}" not found.')
                if file.startswith("/") or file.startswith(".."):
                    data = DB.encoder.encode(None)
                    sb.glue(name, data)
                    self.setSimToolSaveErrorOccurred(1)
                    raise FileNotFoundError('File must be in the local directory.')
                data = self._make_ref(file)
            else:
                data = DB.encoder.encode(value)

        sb.glue(name, data)

        if name in self.outputsToBeSaved:
            self.outputsToBeSaved.remove(name)
            if len(self.outputsToBeSaved) == 0:
                self.setSimToolAllOutputsSaved(1)

        if display:
            self._read(name, data, True, False)


    def read(self, name, display=False, raw=False):
        """Read output from the results database.

        Results are saved internally in the notebook.  The internal result
        could be a reference to a local file.

        Args:
            name: Name of the output.
            display: Should the value be displayed as output for the cell?
            raw: If a reference, just return that.
        Returns:
            The saved value.
        """
        value = None
        try:
            data = self.nb.scraps[name].data
        except KeyError:
            print("%s is not available in results" % (name))
        else:
            value = self._read(name, data, display, raw)

        return value


    def _read(self, name, data, display, raw):
        if name in self.out:
            read_type = Params.types[self.out[name].type]
        else:
            read_type = None
        path = self._get_ref(data)
        if path:
            path = os.path.join(self.dir,path)
            if raw:
                return self._make_ref(path)
            val = DB.datastore.readFile(path,read_type)
        else:
            val = DB.datastore.readData(data,read_type)

        if display:
            idisplay(val)
        return val


    def getSavedOutputs(self):
        savedOutputs = self.nb.scraps.keys()
        return savedOutputs


    def getSavedOutputFiles(self):
        savedOutputFiles = []
        savedOutputs = self.nb.scraps.keys()
        for scrap in savedOutputs:
            data = self.nb.scraps[scrap].data
            if data:
                if type(data) is str:
                    if data.startswith('file://'):
                        savedOutputFiles.append(data[7:])
        return savedOutputFiles


DB.encoder   = JsonEncoder()  # encoder to use for serialzation
DB.datastore = FileDataStore  # configure to use shared filesystem as datastore
