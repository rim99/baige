"""
Compatibility code for using Cheroot with various versions of Python.
Cheroot is compatible with Python versions 2.6+. This module provides a
useful abstraction over the differences between Python versions, sometimes by
preferring a newer idiom, sometimes an older one, and sometimes a custom one.
In particular, Python 2 uses str and '' for byte strings, while Python 3
uses str and '' for unicode strings. Refer to each of these the 'native
string' type for each version. Because of this major difference, this module
provides
two functions: 'ntob', which translates native strings (of type 'str') into
byte strings regardless of Python version, and 'ntou', which translates native
strings to unicode strings. This also provides a 'BytesIO' name for dealing
specifically with bytes, and a 'StringIO' name for dealing with native strings.
It also provides a 'base64_decode' function with native strings as input and
output.
"""

import binascii
import os
import re
import sys
import threading


def ntob(n, encoding='ISO-8859-1'):
    """Return the given native string as a byte string in the given
    encoding.
    """
    assert_native(n)
    # In Python 3, the native string type is unicode
    return n.encode(encoding)

def ntou(n, encoding='ISO-8859-1'):
    """Return the given native string as a unicode string with the given
    encoding.
    """
    assert_native(n)
    # In Python 3, the native string type is unicode
    return n

def tonative(n, encoding='ISO-8859-1'):
    """Return the given string as a native string in the given encoding."""
    # In Python 3, the native string type is unicode
    if isinstance(n, bytes):
        return n.decode(encoding)
    return n

def bton(b, encoding='ISO-8859-1'):
    return b.decode(encoding)

def assert_native(n):
    if not isinstance(n, str):
        raise TypeError('n must be a native str (got %s)' % type(n).__name__)

from base64 import decodebytes as _base64_decodebytes

def base64_decode(n, encoding='ISO-8859-1'):
    """Return the native string base64-decoded (as a native string)."""
    if isinstance(n, str):
        b = n.encode(encoding)
    else:
        b = n
    b = _base64_decodebytes(b)
    return b.decode(encoding)


try:
    sorted = sorted
except NameError:
    def sorted(i):
        i = i[:]
        i.sort()
        return i

try:
    reversed = reversed
except NameError:
    def reversed(x):
        i = len(x)
        while i > 0:
            i -= 1
            yield x[i]

from urllib.parse import urljoin, urlencode
from urllib.parse import quote, quote_plus
from urllib.request import unquote, urlopen
from urllib.request import parse_http_list, parse_keqv_list

iteritems = lambda d: d.items()
copyitems = lambda d: list(d.items())

iterkeys = lambda d: d.keys()
copykeys = lambda d: list(d.keys())

itervalues = lambda d: d.values()
copyvalues = lambda d: list(d.values())

import builtins

from http.cookies import SimpleCookie, CookieError  # noqa
from http.client import BadStatusLine, HTTPConnection, IncompleteRead  # noqa
from http.client import NotConnected  # noqa
from http.server import BaseHTTPRequestHandler  # noqa

try:
    from http.client import HTTPSConnection
except ImportError:
    # Some platforms which don't have SSL don't expose HTTPSConnection
    HTTPSConnection = None

xrange = range


from urllib.parse import unquote as parse_unquote
def unquote_qs(atom, encoding, errors='strict'):
    return parse_unquote(
        atom.replace('+', ' '),
        encoding=encoding,
        errors=errors)


try:
    import json
    json_decode = json.JSONDecoder().decode
    _json_encode = json.JSONEncoder().iterencode
except ImportError:
    def json_decode(s):
        raise ValueError('No JSON library is available')

    def _json_encode(s):
        raise ValueError('No JSON library is available')
finally:
    def json_encode(value):
        for chunk in _json_encode(value):
            yield chunk.encode('utf8')


text_or_bytes = str, bytes

import pickle  # noqa


def random20():
    return binascii.hexlify(os.urandom(20)).decode('ascii')


from _thread import get_ident as get_thread_ident

Timer = threading.Timer
Event = threading.Event

from subprocess import _args_from_interpreter_flags

from html import escape

# html module needed the argument quote=False because in cgi the default
# is False. With quote=True the results differ.

def escape_html(s, escape_quote=False):
    """Replace special characters "&", "<" and ">" to HTML-safe sequences.
    When escape_quote=True, escape (') and (") chars.
    """
    return escape(s, quote=escape_quote)
