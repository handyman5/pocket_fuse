

import fuse
import logging
import time

from functools import wraps
from stat import S_IFDIR, S_IFREG
from types import FunctionType

fuse.fuse_python_api = (0, 2)

logging.basicConfig()
log = logging.getLogger('pocket_fuse')
log.setLevel(logging.INFO)


class MetaClass(type):
    @classmethod
    def log_method(cls, obj):
        @wraps(obj)
        def wrapper(*args, **kwargs):
            #print(f"entering wrapper for {cls}, {obj} with {args}, {kwargs}")
            ret = obj(*args, **kwargs)
            log.info(f"Called method `{obj.__name__}` of {cls} with {args}, {kwargs} returning {ret}")
            return ret
        return wrapper

    def __new__(cls, classname, bases, classDict):
        # print(f"cls: {cls}")
        # print(f"classname: {classname}")
        # print(f"bases: {bases}")
        # print(f"classDict: {classDict}")
        replacement_dict = classDict.copy()
        for attribute_name, attribute in bases[0].__dict__.items():
        #for attribute_name, attribute in classDict.items():
            if isinstance(attribute, FunctionType) and not attribute_name.startswith("__") and not attribute_name == 'main':
                #print(f"setting up attribute {attribute_name}")
                attribute = cls.log_method(attribute)
            classDict[attribute_name] = attribute

        #return type.__new__(cls, classname, bases, replacement_dict)
        return type.__new__(cls, classname, bases, classDict)





#class BasePocketFS(fuse.Fuse, metaclass=MetaClass):
class BasePocketFS(fuse.Fuse):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def main(self):
        fuse.Fuse.main(self)
        #type(self).__mro__[1].main(self)

    def getinfo(self, path):
        return None

    def readdir(self, path, offset):
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')


    def getattr(self, path):
        st = fuse.Stat()
        st.st_atime = int(time.time())
        st.st_mtime = int(time.time())
        st.st_ctime = int(time.time())
        st.st_mode = S_IFDIR | 0o755
        st.st_nlink = 2
        return st


#class WrappedPocketFS(PocketFS, metaclass=MetaClass):
#    pass
class PocketFS(BasePocketFS, metaclass=MetaClass):
    pass
