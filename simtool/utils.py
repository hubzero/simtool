import os
import sys
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

def _get_extra_files(nbname):
    """ Internal function to search the notebook for a cell tagged
    'FILES' with content 'EXTRA_FILES=xxx' where 'xxx' is a list of files
    or '*'
    """
    ecell = None
    nb = load_notebook_node(nbname)
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

def _find_simtool(name):
    """Lookup simtool name and path.
    
    Returns:
        A tuple containing the full path name of the notebook,
        the tool name, and a boolean which is True if the notebook
        is published
    """
    prefix = "/apps/simtools"
    if not name.endswith('.ipynb') and os.path.exists(os.path.join(prefix, name)):
        return (os.path.join(prefix, name, name + '.ipynb'), name, True)

    # must be a local (non-published) notebook
    if os.path.isfile(name):
        tool_name = os.path.splitext(os.path.basename(name))[0]
        return (name, tool_name, False)

    if name.endswith(".ipynb"):
        raise FileNotFoundError('Could not local file "%s"' % name)
    raise FileNotFoundError('No installed tool named "%s"' % name)

def get_inputs(nbname):
    incell = None
    nbname = _find_simtool(nbname)[0]
    nb = load_notebook_node(nbname)
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

def _get_dict(inputs):
    if type(inputs) == dict:
        return inputs
    d = {}
    for i in inputs:
        d[i] = inputs[i].value
    return d


def get_outputs(nb):
    if type(nb) is str:
        nbname = _find_simtool(nb)[0]
        nb = load_notebook_node(nbname)
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

# def get_outputs_df(nbname):
#     df = pm.read_notebook(nbname).dataframe
#     df = df.loc[df['type'] == 'record'].set_index('name')
#     df.drop(['type', 'filename'], axis=1, inplace=True)
#     return df

# def get_output_files(dirname):
#     return [pm.read_notebook(x) for x in glob('%s/*.ipynb' % dirname)]
