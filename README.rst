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

