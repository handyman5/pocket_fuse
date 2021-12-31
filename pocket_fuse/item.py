import json
import fuse
import stat

from collections import UserDict

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0



class Item(UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def direntry(self):
        """Renders this Item into a series of files"""
        # what files do i want?
        # item_id, title (resolved_title), url (resolved_url), excerpt
        yield fuse.Direntry('item_id')
        yield fuse.Direntry('title')
        yield fuse.Direntry('url')
        yield fuse.Direntry('excerpt')

    def getattr(self, path):
        """Returns the stat info for the given path"""
        st = MyStat()
        last = list(filter(None, path.split('/')))[-1]

        if last in ['item_id', 'title', 'url', 'excerpt']:
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = 0
        else:
            return -errno.ENOENT
        return st
