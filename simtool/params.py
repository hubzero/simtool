import os
import numpy as np
from mendeleev import element
import PIL.Image
from pint import UnitRegistry
from .encode import JsonEncoder


ureg = UnitRegistry()
ureg.autoconvert_offset_to_baseunit = True
Q_ = ureg.Quantity


# A dictionary-like object that can also
# be accessed by attributes.  Note that you
# cannot access attributes by key, only keys
# can be accessed by attributes.
class Params:
    encoder = JsonEncoder()

    def __init__(self, **kw):
        self.__members = []
        for k in kw:
            self[k] = kw[k]

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
        if not key in self.__members:
            self.__members.append(key)

    def has_key(self, key):
        return hasattr(self, key)

    def keys(self):
        return self.__members

    def iterkeys(self):
        return self.__members

    def __iter__(self):
        return iter(self.__members)

    def __repr__(self):
        res = []
        for i in self.__members:
            res.append('%s:' % i)
            res.append(self[i].__repr__())
        return '\n'.join(res)

    @staticmethod
    def _make_ref(filename):
        return 'file://' + filename

    @staticmethod
    def read_from_file(path):
        with open(path) as fp:
            return Params.encoder.decode(fp.read())

    @staticmethod
    def read_from_data(data):
        value = None
        if data:
            value = Params.encoder.decode(data)
        return value


class Boolean(Params):
    def __init__(self, **kwargs):
        # always set these first
        self._value = None
        super(Boolean, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        if type(newval) is not None:
            if type(newval) != bool:
                raise ValueError("%s is not type bool" % (str(newval)))
        self._value = newval

    @property
    def serialValue(self):
        return self._value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % (self.value)
        return res


class Integer(Params):
    def __init__(self, **kwargs):
        # always set these first
        self.min = kwargs.get('min')
        self.max = kwargs.get('max')
        self._value = None
        super(Integer, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        if type(newval) is not None:
            if type(newval) == str:
                try:
                    newval = int(newval)
                except:
                    raise ValueError("%s is not an integer" % (newval))
            if self.min is not None and newval < self.min:
                raise ValueError("Minimum value is %d" % (self.min))
            if self.max is not None and newval > self.max:
                raise ValueError("Maximum value is %d" % (self.max))
        self._value = newval

    @property
    def serialValue(self):
        return self._value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % self.value
        return res


class Text(Params):
    def __init__(self, **kwargs):
        self._value = None
        self._file  = None
        super(Text, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = None
        if type(newval) is not None:
            try:
                if isinstance(newval,basestring):
                    self._value = newval
                else:
                    raise ValueError("%s is not a string" % (str(newval)))
            except NameError:
                if isinstance(newval,str):
                    self._value = newval
                else:
                    raise ValueError("%s is not a string" % (str(newval)))

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, newval):
        self._file = None
        if newval:
            try:
                if os.path.exists(newval):
                    if os.path.isfile(newval):
                        self._file = newval
            except:
                pass

    @property
    def serialValue(self):
        if self._file:
            return self._make_ref(self._file)
        else:
            return self._value

    @staticmethod
    def read_from_file(path):
        with open(path) as fp:
            return fp.read()

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % self.value
        return res


class Choice(Params):
    def __init__(self, **kwargs):
        self._value   = None
        self.options = kwargs.get('options')
        super(Choice, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = None
        if self.options is not None:
            try:
                if isinstance(newval,basestring):
                    if newval in self.options:
                        self._value = newval
                    else:
                        raise ValueError("%s is not a valid option" % (str(newval)))
                else:
                    raise ValueError("%s is not a string" % (str(newval)))
            except NameError:
                if isinstance(newval,str):
                    if newval in self.options:
                        self._value = newval
                    else:
                        raise ValueError("%s is not a valid option" % (str(newval)))
                else:
                    raise ValueError("%s is not a string" % (str(newval)))

    @property
    def serialValue(self):
        return self._value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % self.value
        return res


class List(Params):
    def __init__(self, **kwargs):
        self._value = None
        self._file  = None
        super(List, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = None
        if type(newval) is not None:
            if   isinstance(newval,list):
                self._value = newval
            elif isinstance(newval,tuple):
                self._value = newval
            else:
                raise ValueError("%s is not a list" % (str(newval)))

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, newval):
        self._file = None
        if newval:
            try:
                if os.path.exists(newval):
                    if os.path.isfile(newval):
                        self._file = newval
            except:
                pass

    @property
    def serialValue(self):
        if self._file:
            return self._make_ref(self._file)
        else:
            return self._value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % self.value
        return res


class Dict(Params):
    def __init__(self, **kwargs):
        self._value = None
        self._file  = None
        super(Dict, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = None
        if type(newval) is not None:
            if isinstance(newval,dict):
                self._value = newval
            else:
                raise ValueError("%s is not a dictionary" % (str(newval)))

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, newval):
        self._file = None
        if newval:
            try:
                if os.path.exists(newval):
                    if os.path.isfile(newval):
                        self._file = newval
            except:
                pass

    @property
    def serialValue(self):
        if self._file:
            return self._make_ref(self._file)
        else:
            return self._value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % self.value
        return res


class Array(Params):
    def __init__(self, **kwargs):
        self._value = None
        self._file  = None
        super(Array, self).__init__(**kwargs)
        units = kwargs.get('units')

        if units:
            try:
                self.units = ureg.parse_units(self.units)
            except:
                raise ValueError('Unrecognized units: %s' % self.units)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = None
        if type(newval) is not None:
            if   type(newval) is np.ndarray:
                # papermill expects inputs to be json-encodeable by nbformat.
                # This is OK for typical input arrays, but if we ever need
                # to support really large arrays we will need to write a
                # custom papermill engine.
                newval = newval.tolist()
            elif type(newval) is not list:
                raise ValueError("%s is not an array" % (str(newval)))
            self._value = newval

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, newval):
        self._file = None
        if newval:
            try:
                if os.path.exists(newval):
                    if os.path.isfile(newval):
                        self._file = newval
            except:
                pass

    @property
    def serialValue(self):
        if self._file:
            return self._make_ref(self._file)
        else:
            return self._value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % self.value
        return res


class Number(Params):
    def __init__(self, **kwargs):
        # always set these first
        self.min = kwargs.get('min')
        self.max = kwargs.get('max')
        self.units = kwargs.get('units')
        self._value = None
        super(Number, self).__init__(**kwargs)
        if self.units:
            try:
                self.units = ureg.parse_units(self.units)
            except:
                raise ValueError('Unrecognized units: %s' % self.units)

# TODO pressure needs treatment similar to temperature
# absolute, gauge, and pressure diff
    def convert(self, newval):
        "unit conversion with special temperature conversion"
        units = self.units
        if units == ureg.degC or units == ureg.kelvin or units == ureg.degF or units == ureg.degR:
            if newval.units == ureg.coulomb:
                # we want temp, so 'C' is degC, not coulombs
                newval = newval.magnitude * ureg.degC
            elif newval.units == ureg.farad:
               # we want temp, so 'F' is degF, not farads
                newval = newval.magnitude * ureg.degF
        elif units == ureg.delta_degC or units == ureg.delta_degF:
            # detect when user means delta temps
            if newval.units == ureg.degC or newval.units == ureg.coulomb:
                newval = newval.magnitude * ureg.delta_degC
            elif newval.units == ureg.degF or units == ureg.farad:
                newval = newval.magnitude * ureg.delta_degF
        return newval.to(units).magnitude

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        if type(newval) is not None:
            if   self.units and type(newval) == str:
                newval = ureg.parse_expression(newval)
                if hasattr(newval, 'units'):
                    newval = self.convert(newval)
                else:
                    try:
                        newval = float(newval)
                    except:
                        raise ValueError("%s is not a number" % (str(newval)))
            elif type(newval) == str:
                try:
                    newval = float(newval)
                except:
                    raise ValueError("%s is not a number" % (str(newval)))
            elif type(newval) == int:
                pass
            elif type(newval) == float:
                pass
            elif type(newval) == np.float64:
                newval = float(newval)
            else:
                raise ValueError("%s is not a number (%s)" % (str(newval),type(newval)))

            if newval is not None:
                if self.min is not None and newval < self.min:
                    raise ValueError("Minimum value is %g" % self.min)
                if self.max is not None and newval > self.max:
                    raise ValueError("Maximum value is %g" % self.max)
        self._value = newval

    @property
    def serialValue(self):
        return self._value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % self.value
        return res


class Image(Params):
    def __init__(self, **kwargs):
        # always set these first
        self._value       = None
        self._file        = None
        self._imageFormat = None
        super(Image, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = None
        if type(newval) is not None:
            if newval:
                try:
                    self._imageFormat = newval.format
                except:
                    pass
                else:
                    self._value = np.array(newval).tolist()

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, newval):
        self._file = None
        if newval:
            try:
                if os.path.exists(newval):
                    if os.path.isfile(newval):
                        try:
                            fileImage = self.read_from_file(newval)
                            self._imageFormat = fileImage.format
                        except:
                            raise ValueError("%s is not an image file" % (newval))
                        else:
                            self._file = newval
            except:
                raise ValueError("%s is not an image file" % (newval))

    @property
    def serialValue(self):
        if self._file:
            return self._make_ref(self._file)
        else:
            return self._value

    @property
    def imageFormat(self):
        return self._imageFormat

    @staticmethod
    def read_from_file(path):
        return PIL.Image.open(path)

    @staticmethod
    def read_from_data(data):
        value = None
        if data:
            ordinaryData = Params.encoder.decode(data)
            if ordinaryData:
                npData = np.array(ordinaryData,dtype='uint8')
                value = PIL.Image.fromarray(npData)
        return value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: <image>\n'
        return res


class Element(Params):
    def __init__(self, **kwargs):
        self.property = kwargs.get('property', 'symbol')
        self.options = kwargs.get('options')
        self._value = None
        super(Element, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        if type(newval) is not str:
            self._value = newval
            return
        self._e = element(newval.title())
        try:
            self._value = self._e.__dict__[self.property]
        except KeyError:
            print("Error: unknown property:", self.property)
            print("Valid properties are")
            print(list(sorted(self._e.__dict__.keys())))
            raise ValueError("%s is not an element" % (str(newval)))

    @property
    def serialValue(self):
        return self._value

    def __repr__(self):
        # print all attributes with value last
        res = ''
        for i in self:
            if i != 'value':
                res += '    %s: %s\n' % (i, self[i])
        if self.value is not None:
            res += '    value: %s\n' % self.value
        return res

# register param types
# Dictionary that maps strings to class names.
Params.types = {
    'Boolean': Boolean,
    'Integer': Integer,
    'Text': Text,
    'Choice': Choice,
    'List': List,
    'Dict': Dict,
    'Array': Array,
    'Number': Number,
    'Image': Image,
    'Element': Element
}

