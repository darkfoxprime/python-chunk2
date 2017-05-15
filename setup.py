"""The setuptools module for ASTFormatter.
"""

from setuptools import setup

from codecs import open
from os import path

import chunk2

long_description = getattr(chunk2.Chunk, '__doc__', "").lstrip().rstrip('\n').split('\n')
description = long_description.pop(0)
indent = min((len(x) - len(x.lstrip())) for x in long_description if len(x.lstrip()) > 0)
long_description = reduce(lambda a,b:a+('\n' if len(a)>0 else '')+b, [x[indent:].rstrip() for x in long_description], '')
open('README.rst', 'w').write(long_description + '\n')

setup(
    name = 'chunk2' ,
    version = chunk2.__VERSION__ ,
    description = description ,
    long_description = long_description ,
    url = 'https://github.com/darkfoxprime/python-chunk2' ,
    # bugtrack_url = 'https://github.com/darkfoxprime/python-astformatter/issues' ,
    author = 'Johnson Earls' ,
    author_email = 'darkfoxprime@gmail.com' ,
    license = 'ISC' ,
    classifiers = [
        'Development Status :: 4 - Beta' ,
        'Intended Audience :: Developers' ,
        'Topic :: Software Development :: Libraries :: Python Modules' ,
        'License :: OSI Approved :: ISC License (ISCL)' ,
        'Programming Language :: Python :: 2.6' ,
        'Programming Language :: Python :: 2.7' ,
    ] ,
    keywords = 'IFF, chunk, read, write' ,
    packages = [ 'chunk2' ] ,
    install_requires = [] ,
    package_data = {} ,
    data_files = [] ,
    entry_points = {} ,
)
