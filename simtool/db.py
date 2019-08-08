import os
import scrapbook as sb
from IPython.display import display as idisplay

from .utils import parse, get_outputs, Params
from .datastore import FileDataStore
from .encode import JsonEncoder

class DB(object):

    def __init__(self, outputs, dir=None):
        if type(outputs) is str:
            self.nb = sb.read_notebook(outputs)
            self.out = get_outputs(self.nb)
        else:
            self.out = parse(outputs)
        self.dir = dir
        if self.dir is None:
            self.dir = os.getcwd()

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
        if name not in self.out and force is False:
            raise ValueError('\"%s\" not in output schema!' % name)

        # FIXME: If output value is oversized, write it to a file
        # and glue a reference.

        if file:
            if value:
                raise ValueError('Cannot set both "value" and "file" in save()')
            if not os.path.isfile(file):
                raise FileNotFoundError(f'File "{file}" not found.')
            if file.startswith("/") or file.startswith(".."):
                raise FileNotFoundError('File must be in the local directory.')
            data = self._make_ref(file)
        else:
            data = DB.encoder.encode(value)
        sb.glue(name, data)

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
        data = self.nb.scraps[name].data
        return self._read(name, data, display, raw)

    def _read(self, name, data, display, raw):
        path = self._get_ref(data)
        if path:
            if raw:
                return data
            if name in self.out:
                read_type = Params.types[self.out[name].type]
            else:
                read_type = None
            path = os.path.join(self.dir, path)
            val = DB.datastore.read(path, read_type)
        else:
            val = DB.encoder.decode(data)

        if display:
            idisplay(val)
        return val

DB.encoder = JsonEncoder()  # encoder to use for serialzation
DB.datastore = FileDataStore  # configure to use shared filesystem as datastore
