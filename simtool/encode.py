# @package      hubzero-simtool
# @file         encode.py
# @copyright    Copyright (c) 2019-2021 The Regents of the University of California.
# @license      http://opensource.org/licenses/MIT MIT
# @trademark    HUBzero is a registered trademark of The Regents of the University of California.
#
import jsonpickle

# The purpose of this class is to abstract out 
# the serialization/deserialization of data so
# that we may change the method in the future.

# abstract class (template)
# (Python doesn't need this, but added anyway
# for clarity.)
class Encoder:
    def encode(self, val):
        pass

    def decode(self, val):
        pass

class JsonEncoder(Encoder):
    def encode(self, val):
        return jsonpickle.dumps(val)

    def decode(self, val):
        return jsonpickle.loads(val)
        

