import json
import fuse
import logging
import stat
import time
import re
import pprint

import os, errno

from functools import wraps
from stat import S_IFDIR, S_IFREG
from types import FunctionType

from pocket_fuse.item import Item

fuse.fuse_python_api = (0, 2)

logging.basicConfig()
log = logging.getLogger("pocket_fuse")
log.setLevel(logging.INFO)

example_item_raw = {'domain_metadata': {'greyscale_logo': 'https://logo.clearbit.com/newrepublic.com?size=800&greyscale=true',
                     'logo': 'https://logo.clearbit.com/newrepublic.com?size=800',
                     'name': 'The New Republic'},
 'excerpt': 'Co-written by a molecular biology postdoc and a British viscount, '
            'the new pop science book Viral is positioned as the reasonable '
            'person’s guide to the Covid-19 “lab leak” theory. The authors '
            'bristle at the suggestion that they are trafficking in conspiracy '
            'theories.',
 'favorite': '0',
 'given_title': 'This Terrible Book Shows Why the Covid-19 Lab Leak Theory '
                'Won’t Die | The N',
 'given_url': 'https://newrepublic.com/article/164688/viral-lab-leak-theory-covid-19',
 'has_image': '1',
 'has_video': '0',
 'is_article': '1',
 'is_index': '0',
 'item_id': '3501610234',
 'lang': 'en',
 'listen_duration_estimate': 976,
 'resolved_id': '3501610234',
 'resolved_title': 'This Terrible Book Shows Why the Covid-19 Lab Leak Theory '
                   'Won’t Die',
 'resolved_url': 'https://newrepublic.com/article/164688/viral-lab-leak-theory-covid-19',
 'sort_id': 0,
 'status': '0',
 'time_added': '1640662340',
 'time_favorited': '0',
 'time_read': '0',
 'time_to_read': 11,
 'time_updated': '1640662340',
 'top_image_url': 'https://images.newrepublic.com/76e34ca405477b1b9c4006cda8fa83dd6743a562.jpeg?w=1109&h=577&crop=faces&fit=crop&fm=jpg',
 'word_count': '2522'}
example_item = Item(example_item_raw)

example_item2_raw = {'domain_metadata': {'greyscale_logo': 'https://logo.clearbit.com/newrepublic.com?size=800&greyscale=true',
                     'logo': 'https://logo.clearbit.com/newrepublic.com?size=800',
                     'name': 'The New Republic'},
 'excerpt': 'Co-written by a molecular biology postdoc and a British viscount, '
            'the new pop science book Viral is positioned as the reasonable '
            'person’s guide to the Covid-19 “lab leak” theory. The authors '
            'bristle at the suggestion that they are trafficking in conspiracy '
            'theories.',
 'favorite': '0',
 'given_title': 'This Terrible Book Shows Why the Covid-19 Lab Leak Theory '
                'Won’t Die | The N',
 'given_url': 'https://newrepublic.com/article/164688/viral-lab-leak-theory-covid-19',
 'has_image': '1',
 'has_video': '0',
 'is_article': '1',
 'is_index': '0',
 'item_id': '12345678',
 'lang': 'en',
 'listen_duration_estimate': 976,
 'resolved_id': '12345678',
 'resolved_title': 'This Terrible Book Shows Why the Covid-19 Lab Leak Theory '
                   'Won’t Die',
 'resolved_url': 'https://newrepublic.com/article/164688/viral-lab-leak-theory-covid-19',
 'sort_id': 0,
 'status': '0',
 'time_added': '1640662340',
 'time_favorited': '0',
 'time_read': '0',
 'time_to_read': 11,
 'time_updated': '1640662340',
 'top_image_url': 'https://images.newrepublic.com/76e34ca405477b1b9c4006cda8fa83dd6743a562.jpeg?w=1109&h=577&crop=faces&fit=crop&fm=jpg',
 'word_count': '2522'}
example_item2 = Item(example_item2_raw)

example_item3_raw = {'domain_metadata': {'greyscale_logo': 'https://logo.clearbit.com/newrepublic.com?size=800&greyscale=true',
                     'logo': 'https://logo.clearbit.com/newrepublic.com?size=800',
                     'name': 'The New Republic'},
 'excerpt': 'Co-written by a molecular biology postdoc and a British viscount, '
            'the new pop science book Viral is positioned as the reasonable '
            'person’s guide to the Covid-19 “lab leak” theory. The authors '
            'bristle at the suggestion that they are trafficking in conspiracy '
            'theories.',
 'favorite': '0',
 'given_title': 'This Terrible Book Shows Why the Covid-19 Lab Leak Theory '
                'Won’t Die | The N',
 'given_url': 'https://newrepublic.com/article/164688/viral-lab-leak-theory-covid-19',
 'has_image': '1',
 'has_video': '0',
 'is_article': '1',
 'is_index': '0',
 'item_id': '87654321',
 'lang': 'en',
 'listen_duration_estimate': 976,
 'resolved_id': '87654321',
 'resolved_title': 'Some Completely Different Title Is/Here',
 'resolved_url': 'https://example.com',
 'sort_id': 0,
 'status': '0',
 'time_added': '1640662340',
 'time_favorited': '0',
 'time_read': '0',
 'time_to_read': 11,
 'time_updated': '1640662340',
 'top_image_url': 'https://images.newrepublic.com/76e34ca405477b1b9c4006cda8fa83dd6743a562.jpeg?w=1109&h=577&crop=faces&fit=crop&fm=jpg',
 'word_count': '2522'}
example_item3 = Item(example_item3_raw)

example_items = [example_item, example_item2, example_item3]


def populate_tree(items):
    ids = {}
    titles = {}
    urls = {}

    for i in items:
        ids[i['item_id']] = i

        if i['resolved_title'] not in titles:
            titles[i['resolved_title']] = i['item_id']
        else:
            match_count = 0
            for k in titles.keys():
                if k.startswith(i['resolved_title']):
                    match_count += 1
            titles[i['resolved_title'] + f" ({match_count})"] = i['item_id']

        if i['resolved_url'] not in urls:
            urls[i['resolved_url']] = i['item_id']
        else:
            match_count = 0
            for k in urls.keys():
                if k.startswith(i['resolved_url']):
                    match_count += 1
            urls[i['resolved_url'] + f" ({match_count})"] = i['item_id']

    log.info(pprint.pformat(ids))
    log.info(pprint.pformat(titles))
    log.info(pprint.pformat(urls))

    return ids, titles, urls


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



class MetaClass(type):
    @classmethod
    def log_method(cls, obj):
        @wraps(obj)
        def wrapper(*args, **kwargs):
            ret = obj(*args, **kwargs)
            log.debug(
                f"Called method `{obj.__name__}` of {cls} with {args}, {kwargs} returning {ret}"
            )
            return ret

        return wrapper

    def __new__(cls, classname, bases, classDict):
        for attribute_name, attribute in classDict.items():
            if isinstance(attribute, FunctionType):
                classDict[attribute_name] = cls.log_method(attribute)
        return type.__new__(cls, classname, bases, classDict)


class PocketFS(fuse.Fuse, metaclass=MetaClass):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.ids, self.titles, self.urls = populate_tree(example_items)

    def main(self):
        fuse.Fuse.main(self)

    def getinfo(self, path):
        return None

    def readdir(self, path, offset):
        yield fuse.Direntry(".")
        yield fuse.Direntry("..")

        if path == '/':
            yield fuse.Direntry('by-id')
            yield fuse.Direntry('by-title')
            yield fuse.Direntry('by-url')

        elif path.rstrip('/') == '/by-id':
            for i in self.ids:
                yield fuse.Direntry(i)

        elif path.rstrip('/') == '/by-title':
            for i in self.titles:
                yield fuse.Direntry(i)

        elif path.rstrip('/') == '/by-url':
            for i in self.urls:
                yield fuse.Direntry(i)

        else:
            log.info(f"Trying to load path {path}")
            yield from example_item.direntry()


    def getattr(self, path):
        """Returns the stat info for the given path"""
        st = MyStat()
        try:
            last = list(filter(None, path.split('/')))[-1]
        except IndexError:
            # root directory
            last = ""

        # what files do we expect we might see?
        # /
        # /by-{id,title,url}
        # /by-id/123456..
        # /by-title/Some Long Ass Title
        # /by-url/http://example.com
        # /{one of those three}/<something>/<item_id,title,url,excerpt>

        readdir_roots_re = re.compile('^/by-(id|title|url)/?$')
        readdir_ids_re = re.compile('^/by-id/\d+/?$')
        readdir_ids_file_re = re.compile('^/by-id/\d+/[^/]+$')
        readdir_titles_re = re.compile('^/by-title/[^/]+/?$')
        readdir_titles_file_re = re.compile('^/by-title/[^/]+/[^/]+$')
        readdir_urls_re = re.compile('^/by-url/[^/]+/?$')
        readdir_urls_file_re = re.compile('^/by-url/[^/]+/[^/]+$')

        if path == '/':
            log.info(f"matching '/' for path {path}")
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        elif readdir_roots_re.match(path):
            log.info(f"matching readdir_roots_re for path {path}")
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        elif readdir_ids_re.match(path):
            log.info(f"matching readdir_ids_re for path {path}")
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        elif readdir_ids_file_re.match(path):
            log.info(f"matching readdir_ids_file_re for path {path}")
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = 0
        elif readdir_titles_re.match(path):
            log.info(f"matching readdir_titles_re for path {path}")
            st.st_mode = stat.S_IFLNK | 0o777
            st.st_nlink = 1
        elif readdir_titles_file_re.match(path):
            log.info(f"matching readdir_titles_file_re for path {path}")
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = 0
        elif readdir_urls_re.match(path):
            log.info(f"matching readdir_urls_re for path {path}")
            st.st_mode = stat.S_IFLNK | 0o777
            st.st_nlink = 1
        elif readdir_urls_file_re.match(path):
            log.info(f"matching readdir_urls_file_re for path {path}")
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = 0
        else:
            return -errno.ENOENT
        return st


    def readlink(self, path):
        pathtype_re = re.compile('^/by-(id|title|url)/([^/]+)$')
        m = pathtype_re.match(path)
        if m:
            log.info(f"matched pathtype for {path}, is {m.groups()}")
            pathtype = m.groups()[0]
            if pathtype == 'title':
                return '../by-id/' + self.titles[m.groups()[1]]
            if pathtype == 'url':
                return '../by-id/' + self.urls[m.groups()[1]]
        return 'READLINK-DID-NOT-MATCH'


        # st = fuse.Stat()
        # st.st_atime = int(time.time())
        # st.st_mtime = int(time.time())
        # st.st_ctime = int(time.time())
        # st.st_mode = S_IFDIR | 0o755
        # st.st_nlink = 2
        # log.debug(f"getattr for PATH {path}: {st}")
        # log.debug(st.__dict__)
        # return st
