# @package      hubzero-simtool
# @file         params.py
# @copyright    Copyright (c) 2019-2021 The Regents of the University of California.
# @license      http://opensource.org/licenses/MIT MIT
# @trademark    HUBzero is a registered trademark of The Regents of the University of California.
#
import os
import sys
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

    KEYWORDPRINTORDER = ['type', 'description', 'units', 'max', 'min', 'options', 'property', 'value']

    def __init__(self, **kwargs):
        self.__members = []

        if hasattr(self, 'property'):
            self['property'] = kwargs.get('property','symbol')

        for k in kwargs:
            if k in ['type','description']:
                self[k] = kwargs[k]

        if hasattr(self, 'units'):
            units = kwargs.get('units')
            if units:
                try:
                    self['units'] = ureg.parse_units(units)
                except:
                    raise ValueError('Unrecognized units: %s' % (units))
        if hasattr(self, 'min'):
            self['min'] = self._getNumericValueFromQuantity(kwargs.get('min'),checkMinMax=False)
        if hasattr(self, 'max'):
            self['max'] = self._getNumericValueFromQuantity(kwargs.get('max'),checkMinMax=False)

        if hasattr(self, 'options'):
            self['options'] = kwargs.get('options')

        for k in kwargs:
            if k in ['value']:
                self[k] = kwargs[k]

        for k in kwargs:
            if k not in ['type','value','description','units','min','max','options','property']:
                print('Parameter type %s does not have %s attribute.' % (self['type'],k),file=sys.stderr)

        for k in kwargs:
            if k in ['units','min','max','options','property']:
                if not hasattr(self, k):
                    print('Parameter type %s does not have %s attribute.' % (self['type'],k),file=sys.stderr)

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

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self.__members:
            attributeDictionary[attribute] = self[attribute].getAttributeDictionary()
        return attributeDictionary

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
        with open(path,'r') as fp:
            return Params.encoder.decode(fp.read())

    @staticmethod
    def read_from_data(data):
        value = None
        if data:
            value = Params.encoder.decode(data)
        return value

    def content(self,
                returnAs=None):
        value = None

        if   returnAs == 'value':
            if hasattr(self, '_value'):
                value = self._value
        elif returnAs == 'file':
            if hasattr(self, '_file'):
                if self._file:
                    value = self._file
        else:
            if   hasattr(self, '_file'):
                if   self._file:
                    if hasattr(self, '_value'):
                        value = self.read_from_file(self._file)
                    else:
                        value = self._file
                elif hasattr(self, '_value'):
                    value = self._value
            elif hasattr(self, '_value'):
                value = self._value

        return value

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

    def _getNumericValueFromQuantity(self,
                                     quantity,
                                     checkMinMax=True):
        numericValue = None
        if quantity is not None:
            if   hasattr(self, 'units') and self.units and type(quantity) == str:
                numericValue = ureg.parse_expression(quantity)
                if hasattr(numericValue, 'units'):
                    numericValue = self.convert(numericValue)
                else:
                    try:
                        numericValue = float(numericValue)
                    except:
                        raise ValueError("%s is not a number" % (str(quantity)))
            elif type(quantity) == str:
                try:
                    numericValue = float(quantity)
                except:
                    raise ValueError("%s is not a number" % (str(quantity)))
            elif type(quantity) == int:
                numericValue = quantity
            elif type(quantity) == float:
                numericValue = quantity
            elif type(quantity) == np.float64:
                numericValue = float(quantity)
            else:
                raise ValueError("%s is not a number (%s)" % (str(quantity),type(quantity)))

            if checkMinMax and numericValue is not None:
                if self.min is not None and numericValue < self.min:
                    raise ValueError("Minimum value is %g" % (self.min))
                if self.max is not None and numericValue > self.max:
                    raise ValueError("Maximum value is %g" % (self.max))

        return numericValue

    def _getNumericValueForAllQuanities(self,
                                        quantities,
                                        checkMinMax=True):
        for quantity in quantities:
            if isinstance(quantity,list):
                yield list(self._getNumericValueForAllQuanities(quantity,checkMinMax=checkMinMax))
            else:
                yield self._getNumericValueFromQuantity(quantity,checkMinMax=checkMinMax)


class Boolean(Params):
    def __init__(self, **kwargs):
        self._value = None
        super(Boolean, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        if newval is not None:
            if type(newval) != bool:
                raise ValueError("%s is not type bool" % (str(newval)))
        self._value = newval

    @property
    def serialValue(self):
        return self._value

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


class Integer(Params):
    def __init__(self, **kwargs):
        self._value = None
        self.min = None
        self.max = None
        super(Integer, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        if newval is not None:
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

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
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
        if newval is not None:
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
        with open(path,'r') as fp:
            return fp.read()

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


class Tag(Params):
    MAXTAGLENGTH = 255
    def __init__(self, **kwargs):
        self._value = None
        super(Tag, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = None
        if newval is not None:
            try:
                if isinstance(newval,basestring):
                    if len(newval) <= self.MAXTAGLENGTH:
                        self._value = newval
                    else:
                        raise ValueError("len(%s) > %d" % (newval,self.MAXTAGLENGTH))
                else:
                    raise ValueError("%s is not a string" % (str(newval)))
            except NameError:
                if isinstance(newval,str):
                    if len(newval) <= self.MAXTAGLENGTH:
                        self._value = newval
                    else:
                        raise ValueError("len(%s) > %d" % (newval,self.MAXTAGLENGTH))
                else:
                    raise ValueError("%s is not a string" % (str(newval)))

    @property
    def serialValue(self):
        return self._value

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


class Choice(Params):
    def __init__(self, **kwargs):
        self._value  = None
        self.options = None
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

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
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
        if newval is not None:
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

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
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
        if newval is not None:
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

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


class Array(Params):
    def __init__(self, **kwargs):
        self._value = None
        self._file  = None
        self.units = None
        self.min = None
        self.max = None
        super(Array, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = None
        if newval is not None:
            if   type(newval) is np.ndarray:
                # papermill expects inputs to be json-encodeable by nbformat.
                # This is OK for typical input arrays, but if we ever need
                # to support really large arrays we will need to write a
                # custom papermill engine.
                if self.min is not None and newval.min() < self.min:
                    raise ValueError("Minimum value is %g" % self.min)
                if self.max is not None and newval.max() > self.max:
                    raise ValueError("Maximum value is %g" % self.max)
                self._value = newval.tolist()
            elif type(newval) is list:
                self._value = list(self._getNumericValueForAllQuanities(newval))
            else:
                raise ValueError("%s is not an array" % (str(newval)))

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

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if   attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            elif attribute == 'units':
                attributeDictionary[attribute] = "%s" % (self[attribute])
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


class Number(Params):
    def __init__(self, **kwargs):
        self._value = None
        self.units = None
        self.min = None
        self.max = None
        super(Number, self).__init__(**kwargs)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newval):
        self._value = self._getNumericValueFromQuantity(newval)

    @property
    def serialValue(self):
        return self._value

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if   attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            elif attribute == 'units':
                attributeDictionary[attribute] = "%s" % (self[attribute])
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


class File(Params):
    def __init__(self, **kwargs):
        self._file = None
        super(File, self).__init__(**kwargs)

    @property
    def value(self):
        return self._file

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
            return None

    @staticmethod
    def read_from_file(path):
        with open(path,'rb') as fp:
            return fp.read()

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


class Image(Params):
    def __init__(self, **kwargs):
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
        if newval is not None:
            if newval:
                try:
                    self._imageFormat = newval.format
                except:
                    if   type(newval) is list:
                        self._value = newval
                    elif type(newval) is np.ndarray:
                        self._value = newval.tolist()
#                   else:
#                       print("Image.value: format failed")
#                       print("type(newval): %s" % (type(newval)))
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

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                value = self.serialValue
                if value.startswith('file://'):
                    attributeDictionary[attribute] = value
                else:
                    attributeDictionary[attribute] = '<image>'
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                if self.value:
                    value = "<image>"
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


class Element(Params):
    def __init__(self, **kwargs):
        self._value = None
        self.property = None
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

    def getAttributeDictionary(self):
        attributeDictionary = {}
        for attribute in self:
            if attribute == 'value':
                attributeDictionary[attribute] = self.serialValue
            else:
                attributeDictionary[attribute] = self[attribute]
        return attributeDictionary

    def __repr__(self):
        res = ""
        for keyWord in self.KEYWORDPRINTORDER:
            if keyWord != 'value':
                if keyWord in self:
                    if not self[keyWord] is None:
                        res += '    %s: %s\n' % (keyWord, self[keyWord])
        if 'value' in self.KEYWORDPRINTORDER:
            value = None
            try:
                fileValue = self.file
            except:
                fileValue = None
            else:
                if fileValue:
                    value = self._make_ref(fileValue)
            if not value:
                value = self.value
            if not value is None:
                res += '    value: %s\n' % (value)
        return res


# register param types
# Dictionary that maps strings to class names.
Params.types = {
    'Boolean': Boolean,
    'Integer': Integer,
    'Text': Text,
    'Tag': Tag,
    'Choice': Choice,
    'List': List,
    'Dict': Dict,
    'Array': Array,
    'Number': Number,
    'File': File,
    'Image': Image,
    'Element': Element
}

