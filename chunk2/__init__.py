
__ALL__ = [ 'Chunk', 'parse_chunk', 'parse_iff_file' ]

__VERSION__ = '0.1.0'

import struct
import cStringIO
import string

class Chunk(object):
    """A replacement Chunk class that allows both reading and writing IFF chunks.

    An IFF chunk, as defined in the
    `EA IFF 85 <http://wiki.amigaos.net/wiki/EA_IFF_85_Standard_for_Interchange_Format_Files>`_
    standard, consists of a 4-byte ID field, a 4-byte length field,
    and the data content of the chunk, and optionally followed by a
    single padding ``null`` byte if required to make the total number
    of bytes even.

    +----------+-------------+
    | Chunk ID |   4 bytes   |
    +----------+-------------+
    |  Length  |   4 bytes   |
    +----------+-------------+
    |   Data   |   n bytes   |
    +----------+-------------+
    | Padding  | 0 or 1 byte |
    +----------+-------------+

    *   The Chunk ID is a 4-character string that identifies the type
        of chunk.
    *   The Length is a 4-byte integer (generally in big-endian format)
        indicating how long the data field is.

    The Chunk class allows for either *reading* a chunk from a file-like
    object or *creating* a chunk and writing it into a file-like object,
    but not both.

    For reading, the Chunk class reads a single chunk from the file-like
    object, and is in turn a read-only file-like object for reading the
    contents of the chunk.

    Chunk tries to determine if the underlying file-like object is seekable
    by via the ``tell`` operation; if that does not raise an exception,
    then the file-like object presented by Chunk is itself seekable.

    When the Chunk is closed, the underlying file-like object is positioned
    to read immediately following the Chunk (and after the padding byte,
    if any).

    For writing, the Chunk class presents a *write-only* file-like object
    for creating the contents of the chunk, as well as the ``setname``
    method for assigning the Chunk ID.

    For writable chunks whose underlying file-like object is not seekable,
    an in-memory file object is created to hold the chunk's data; only
    when the chunk is closed is the in-memory file object is flushed to
    the underlying file-like object.

    IFF files can consist of multiple top-level chunks; "container"
    chunk types (``FORM``, ``CAT ``, and ``LIST``) contain other chunks.
    The Chunk class is designed to be instantiated multiple times, one
    after the other, for either reading or writing multiple chunks from
    or to a file, or from or to the content of a "container" chunk.

    The ``parse_chunk`` and ``parse_iff_file`` helper methods assist in
    reading IFF files by automating the parsing of container chunks.
    ``parse_iff_file`` returns a list of chunk tuples consisting of the
    chunk name and chunk content; for container chunks, the chunk
    content is itself a list of chunk tuples.

    --------

    To Do
    =====

    *   Rewrite from scratch to remove original Python code, if possible
    *   Modify to work with both Python 2 and Python 3, if possible

    --------

    License
    =======

    Original code base copied from Python 2.7 library, then modified
    to support write functionality.

    Original ``chunk.py`` is Copyright (c) 2001, 2002, 2003, 2004,
    2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015,
    2016, 2017 Python Software Foundation; All Rights Reserved; licensed
    under the Python Software Foundation License Version 2
    <https://docs.python.org/2.7/license.html>

    Derived portions are Copyright (c) 2017 Johnson Earls; All Rights
    Reserved; licensed as follows:

    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted, provided that the above
    copyright notice and this permission notice appear in all copies.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
    """

    def __init__(self, file, align=True, bigendian=True, inclheader=False, mode='r', name=None, form=None):
        """Create a Chunk class for reading or writing.
        ``file`` is the underlying file-like object.
        The file-like object is considered seekable if ``file.tell()`` does not raise an exception.
        If ``align`` is False, then no padding byte is read or written after an odd-length chunk.
        If ``bigendian`` is False, then sizes are written in little-endian format.
        If ``inclheader`` is True, then the size field includes the 8 bytes of the header.
        If ``mode`` is `r`, the chunk is opened for reading; if ``mode`` is `w`, the chunk is opened for writing.  No other modes or characters are permitted.
        If ``form`` is not None, then the chunk name (ID) is set to ``FORM`` and the first four characters of ``form`` are written to the first four bytes of the chunk.
        If ``name`` is not None (but ``form`` is), then the chunk name (ID) is set to the first four characters of ``name``.
        """

        import struct
        self.closed = False
        self.align = align
        self.inclheader = inclheader
        if bigendian:
            self.strflag = '>'
        else:
            self.strflag = '<'
        self.file = file
        self.mode = mode
        if mode not in ('w', 'r'):
            raise ValueError, "mode must be 'r' or 'w'"

        if mode == 'r':
            self.chunkname = file.read(4)
            if len(self.chunkname) == 0:
                raise EOFError
            if len(self.chunkname) < 4:
                raise IOError, 'Truncated chunk'
            try:
                self.chunksize = struct.unpack(self.strflag + 'L', file.read(4))[0]
            except struct.error:
                raise IOError, 'Truncated chunk'
            if self.inclheader:
                self.chunksize = self.chunksize - 8
            try:
                self.chunk_offset = self.file.tell()
            except (AttributeError, IOError):
                self.seekable = False
            else:
                self.seekable = True
            self.chunk_index = 0

        else:
            try:
                self.chunk_offset = self.file.tell()
            except (AttributeError, IOError):
                self.contentfile = cStringIO.StringIO()
            else:
                self.contentfile = self.file
            # the content of writable chunks are always seekable
            self.seekable = True
            self.chunk_index = 0

            self.contentfile.write('    \0\0\0\0')
            self.chunk_offset = self.contentfile.tell()

            self.chunksize = 0
            self.chunkname = '    '
            if name is not None:
                self.setname(name)
            if form is not None:
                if not Chunk.name_is_valid(form):
                    raise ValueError, "Invalid FORM name"
                self.setname('FORM')
                self.write((form + '    ')[0:4])

    def getname(self):
        """Return the name (ID) of the current chunk."""
        return self.chunkname

    def setname(self, name):
        """Set the name (ID) of the chunk."""
        if self.mode == 'r':
            raise IOError, 'Write operation on read-only chunk'
        if not Chunk.name_is_valid(name):
            raise ValueError, "Invalid chunk name"
        name = (name + '    ')[0:4]
        self.chunkname = name
        self.contentfile.seek(self.chunk_offset - 8, 0)
        self.contentfile.write(name)
        self.contentfile.seek(self.chunk_offset + self.chunk_index, 0)
        return self

    @staticmethod
    def name_is_valid(name):
        """Validates a chunk name.
        
        Returns ``false`` if the name is empty, longer than 4 characters, or contains a non-printable character.
        """
        if len(name) < 1 or len(name) > 4:
            return False
        for c in name:
            if c not in string.printable:
                return False
        return True

    def getsize(self):
        """Return the size of the current chunk."""
        return self.chunksize

    def __setsize(self, size):
        """Private method to write the content size into the chunk header."""
        if self.mode == 'r':
            raise IOError, 'Write operation on read-only chunk'
        if size < 0:
            raise ValueError, "Invalid chunk size"
        self.chunksize = size
        self.contentfile.seek(self.chunk_offset - 4, 0)
        if self.inclheader:
            self.contentfile.write(struct.pack(self.strflag + 'L', size + 8))
        else:
            self.contentfile.write(struct.pack(self.strflag + 'L', size))
        self.contentfile.seek(self.chunk_offset + self.chunk_index, 0)
        return self

    def close(self):
        """Close the chunk.

        _Always_ call this method when you are done with the chunk.
        For a chunk opened for reading, this positions the underlying
        file-like object to the beginning of the next chunk (if any).
        For a chunk opened for writing, this ensures the contents of
        the chunk are flushed to the underlying file-like object,
        including a padding byte, if required.
        """
        if not self.closed:
            try:
                if self.mode == 'r':
                    self.skip()
                else:
                    self.contentfile.seek(self.chunk_offset + self.chunksize, 0)
                    if self.align and self.chunksize % 2 == 1:
                        self.contentfile.write('\0')
                    if self.contentfile != self.file:
                        self.file.write(self.contentfile.getvalue())
                        self.contentfile.close()
                    self.file.flush()
            finally:
                self.closed = True

    def flush(self):
        """No-op operation.
        
        Provided to prevent ``AttributeError`` exceptions when trying
        to flush the file-like object.
        """
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        pass

    def isatty(self):
        """Always returns ``False``."""
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        return False

    def seek(self, pos, whence=0):
        """Seek to specified position into the chunk.
        Default position is 0 (start of chunk).
        If the file is not seekable, this will result in an error.
        """

        if self.closed:
            raise ValueError, "I/O operation on closed file"
        if not self.seekable:
            raise IOError, "cannot seek"
        if whence == 1:
            pos = pos + self.chunk_index
        elif whence == 2:
            pos = pos + self.chunksize
        if pos < 0 or pos > self.chunksize:
            raise RuntimeError
        if mode == 'w':
            self.contentfile.seek(self.chunk_offset + pos, 0)
        else:
            self.file.seek(self.chunk_offset + pos, 0)
        self.chunk_index = pos

    def tell(self):
        """Return the current read or write position within the chunk."""
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        if not self.seekable:
            raise IOError, "cannot seek"
        return self.chunk_index

    def read(self, size=-1):
        """Read at most size bytes from the chunk.
        If size is omitted or negative, read until the end
        of the chunk.
        """

        if self.mode == 'w':
            raise IOError, "Read operation on write-only chunk"
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        if self.chunk_index >= self.chunksize:
            return ''
        if size < 0 or size > self.chunksize - self.chunk_index:
            size = self.chunksize - self.chunk_index
        data = self.file.read(size)
        self.chunk_index = self.chunk_index + len(data)
        if self.chunk_index == self.chunksize and \
           self.align and \
           (self.chunksize & 1):
            dummy = self.file.read(1)
            self.chunk_index = self.chunk_index + len(dummy)
        return data

    def skip(self):
        """Skip the rest of the chunk.
        If you are not interested in the contents of the chunk,
        this method should be called so that the file points to
        the start of the next chunk.
        """

        if self.mode == 'w':
            raise IOError, 'Read operation on write-only chunk'
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        if self.seekable:
            try:
                n = self.chunksize - self.chunk_index
                # maybe fix alignment
                if self.align and (self.chunksize & 1):
                    n = n + 1
                self.file.seek(n, 1)
                self.chunk_index = self.chunk_index + n
                return
            except IOError:
                pass
        while self.chunk_index < self.chunksize:
            n = min(8192, self.chunksize - self.chunk_index)
            dummy = self.read(n)
            if not dummy:
                raise EOFError

    def write(self, data):
        """Write ``data`` to the chunk."""
        if self.mode == 'r':
            raise IOError, 'Write operation on read-only chunk'
        if len(data) > 0:
            if len(data) + self.chunk_index > self.chunksize:
                self.__setsize(self.chunk_index + len(data))
            self.contentfile.write(data)
            self.contentfile.flush()
            self.chunk_index += len(data)
        return self

def parse_chunk(ifffile):
    """Parse a single chunk from a file object.

    This reads a chunk and returns a tuple of (name, content).  If the
    chunk is a container chunk (``FORM``, ``CAT ``, ``LIST``, or
    ``PROP``), then ``content`` will be a list of tuples of the chunks
    contained within.
    """
    ck = Chunk(ifffile)
    if ck.getname() in ('FORM', 'CAT ', 'LIST', 'PROP'):
        return (ck.getname() + ck.read(4), parse_iff_file(ck))
    return (ck.getname(), ck.read())

def parse_iff_file(ifffile):
    """Parse a file object and return a list of all chunks contained within."""
    contents = []
    while True:
        try:
            ck = parse_chunk(ifffile)
            contents.append(ck)
        except EOFError,e:
            break
    return contents

