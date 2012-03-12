"""A library of helper functions for the Cheroot test suite."""

import datetime
import logging
log = logging.getLogger(__name__)
import os
thisdir = os.path.abspath(os.path.dirname(__file__))
serverpem = os.path.join(os.getcwd(), thisdir, 'test.pem')

import sys
import time
import threading
import traceback

import cheroot
from cheroot._compat import basestring, format_exc, HTTPSConnection, ntob
from cheroot import server, wsgi
from cheroot.test import webtest

import nose

_testconfig = None

def get_tst_config(overconf = {}):
    global _testconfig
    if _testconfig is None:
        conf = {
            'protocol': "HTTP/1.1",
            'bind_addr': ('127.0.0.1', 54583),
            'server': 'wsgi',
        }
        try:
            import testconfig
            if testconfig.config is not None:
                conf.update(testconfig.config)
        except ImportError:
            pass
        _testconfig = conf
    conf = _testconfig.copy()
    conf.update(overconf)

    return conf


class CherootWebCase(webtest.WebCase):

    available_servers = {'wsgi': wsgi.WSGIServer,
                         'native': server.HTTPServer,
                         }
    default_server = "wsgi"
    httpserver_startup_timeout = 5

    def setup_class(cls):
        """Create and run one HTTP server per class."""
        conf = get_tst_config().copy()
        sclass = conf.pop('server', 'wsgi')
        server_factory = cls.available_servers.get(sclass)
        if server_factory is None:
            raise RuntimeError('Unknown server in config: %s' % sclass)
        cls.httpserver = server_factory(**conf)

        cls.HOST, cls.PORT = cls.httpserver.bind_addr
        if cls.httpserver.ssl_adapter is None:
            ssl = ""
            cls.scheme = 'http'
        else:
            ssl = " (ssl)"
            cls.HTTP_CONN = HTTPSConnection
            cls.scheme = 'https'

        v = sys.version.split()[0]
        log.info("Python version used to run this test script: %s" % v)
        log.info("Cheroot version: %s" % cheroot.__version__)
        log.info("HTTP server version: %s%s" % (cls.httpserver.protocol, ssl))
        log.info("PID: %s" % os.getpid())

        if hasattr(cls, 'setup_server'):
            # Clear the wsgi server so that
            # it can be updated with the new root
            cls.setup_server()
            cls.start()
    setup_class = classmethod(setup_class)

    def teardown_class(cls):
        """Stop the per-class HTTP server."""
        if hasattr(cls, 'setup_server'):
            cls.stop()
    teardown_class = classmethod(teardown_class)

    def start(cls):
        """Load and start the HTTP server."""
        threading.Thread(target=cls.httpserver.safe_start).start()
        for trial in range(cls.httpserver_startup_timeout):
            if cls.httpserver.ready:
                return
            time.sleep(1)
        raise AssertionError(
            "The HTTP server did not start in the allotted time.")
    start = classmethod(start)

    def stop(cls):
        """Stop the per-class HTTP server."""
        cls.httpserver.stop()
        td = getattr(cls, 'teardown', None)
        if td:
            td()
    stop = classmethod(stop)

    def base(self):
        if ((self.httpserver.ssl_adapter is None and self.PORT == 80) or
            (self.httpserver.ssl_adapter is not None and self.PORT == 443)):
            port = ""
        else:
            port = ":%s" % self.PORT
        
        return "%s://%s%s%s" % (self.scheme, self.HOST, port,
                                self.script_name.rstrip("/"))
    
    def exit(self):
        sys.exit()
    
    def getPage(self, url, headers=None, method="GET", body=None, protocol=None):
        """Open the url. Return status, headers, body."""
        return webtest.WebCase.getPage(self, url, headers, method, body, protocol)
    
    def skip(self, msg='skipped '):
        raise nose.SkipTest(msg)
    
    date_tolerance = 2
    
    def assertEqualDates(self, dt1, dt2, seconds=None):
        """Assert abs(dt1 - dt2) is within Y seconds."""
        if seconds is None:
            seconds = self.date_tolerance
        
        if dt1 > dt2:
            diff = dt1 - dt2
        else:
            diff = dt2 - dt1
        if not diff < datetime.timedelta(seconds=seconds):
            raise AssertionError('%r and %r are not within %r seconds.' %
                                 (dt1, dt2, seconds))


class Request(object):

    def __init__(self, environ):
        self.environ = environ

class Response(object):

    def __init__(self):
        self.status = '200 OK'
        self.headers = {'Content-Type': 'text/html'}
        self.body = None

    def output(self):
        if self.body is None:
            return []
        elif isinstance(self.body, (tuple, list)):
            return [ntob(x) for x in self.body]
        elif isinstance(self.body, basestring):
            return [ntob(self.body)]
        else:
            return self.body


class Controller(object):

    def __call__(self, environ, start_response):
        try:
            req, resp = Request(environ), Response()
            try:
                handler = getattr(self, environ["PATH_INFO"].lstrip("/").replace("/", "_"))
            except AttributeError:
                resp.status = '404 Not Found'
            else:
                output = handler(req, resp)
                if output is not None:
                    resp.body = output
                    if isinstance(output, basestring):
                        cl = len(output)
                    elif isinstance(output, (tuple, list)):
                        cl = sum([len(a) for a in output])
                    else:
                        cl = None
                    if cl is not None:
                        resp.headers.setdefault('Content-Length', str(cl))
            h = []
            for k, v in resp.headers.items():
                if isinstance(v, (tuple, list)):
                    for atom in v:
                        h.append((k, atom))
                else:
                    h.append((k, v))
            start_response(resp.status, h)
            return resp.output()
        except:
            status = "500 Server Error"
            response_headers = [("Content-Type", "text/plain")]
            start_response(status, response_headers, sys.exc_info())
            return format_exc()

