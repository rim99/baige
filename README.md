## Baige 

Baige is a asynchronous WSGI server based on Cheroot, a WSGI server inside the famous web framework CherryPy. The asynchronous architecture is implemented on built-in `selectors`. So only Python3.4+ are supported.

The original idea was inspired by the Bjoern, another fast and low-memery-usage web server framework which is only avilable under CPython2.x, 

Baige exposes its event loop instance, so the web applications can make use of that by regitering their backend queries on the event loop instance, to try to enchance effiency.

Currently, Baige is still **working in progress**.
