import os

import yaml

class Struct:
    """
    Turns a dictionary into an object that you can reference by name. You can turn it back into a dictionary with todict()
    """
    def __init__(self, **entries):
        for k, v in entries.items():
            if type(v) is dict:
                entries[k] = Struct(**v)
        self.__dict__.update(entries)
    
    def to_dict(self):
        r = self.__dict__.copy()
        for k ,v in r.items():
            if type(v) == Struct:
                r[k] = v.to_dict()
        return r
    def __repr__(self):
        return str(self.to_dict())

def _load():
    root = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(root, "constants.yml")) as file:
        constants_dict = yaml.safe_load(file)
        return Struct(**constants_dict)

"""
The constants are loaded from the constants.yml.
Anything in the yaml file can be read directly by name from this object.
For example:

from src.config import constants
print(constants.example.message)

Will print

"This is an example constant"
"""
constants = _load()
