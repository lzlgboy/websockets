"""
:mod:`websockets.uri` parses WebSocket URIs.

See `section 3 of RFC 6455`_.

.. _section 3 of RFC 6455: http://tools.ietf.org/html/rfc6455#section-3

"""

import urllib.parse
from typing import NamedTuple, Optional, Tuple

from .exceptions import InvalidURI
import collections

__all__ = [
    'parse_uri', 'WebSocketURI',
    'parse_proxy_uri', 'ProxyURI',
]


# Consider converting to a dataclass when dropping support for Python < 3.7.


class WebSocketURI(NamedTuple):
    """
    WebSocket URI.

    :param bool secure: secure flag
    :param str host: lower-case host
    :param int port: port, always set even if it's the default
    :param str resource_name: path and optional query
    :param str user_info: ``(username, password)`` tuple when the URI contains
      `User Information`_, else ``None``.

    .. _User Information: https://tools.ietf.org/html/rfc3986#section-3.2.1
    """

    secure: bool
    host: str
    port: int
    resource_name: str
    user_info: Optional[Tuple[str, str]]


# Work around https://bugs.python.org/issue19931

WebSocketURI.secure.__doc__ = ""
WebSocketURI.host.__doc__ = ""
WebSocketURI.port.__doc__ = ""
WebSocketURI.resource_name.__doc__ = ""
WebSocketURI.user_info.__doc__ = ""


ProxyURI = collections.namedtuple(
    'ProxyURI', ['secure', 'host', 'port', 'user_info'])
ProxyURI.__doc__ = """Proxy URI.
* ``secure`` tells whether to connect to the proxy with TLS
* ``host`` is the lower-case host
* ``port`` if the integer port, it's always provided even if it's the default
* ``user_info`` is an ``(username, password)`` tuple when the URI contains
  `User Information`_, else ``None``.
.. _User Information: https://tools.ietf.org/html/rfc3986#section-3.2.1
"""

def parse_uri(uri: str) -> WebSocketURI:
    """
    Parse and validate a WebSocket URI.

    :raises ValueError: if ``uri`` isn't a valid WebSocket URI.

    """
    parsed = urllib.parse.urlparse(uri)
    try:
        assert parsed.scheme in ["ws", "wss"]
        assert parsed.hostname is not None
        # Params aren't allowed ws or wss URLs. urlparse doesn't extract them.
        assert parsed.params == ""
        assert parsed.fragment == ""
        assert parsed.hostname is not None
    except AssertionError as exc:
        raise InvalidURI(uri) from exc

    secure = parsed.scheme == "wss"
    host = parsed.hostname
    port = parsed.port or (443 if secure else 80)
    resource_name = parsed.path or "/"
    if parsed.query:
        resource_name += "?" + parsed.query
    user_info = None
    if parsed.username or parsed.password:
        user_info = (parsed.username, parsed.password)
    return WebSocketURI(secure, host, port, resource_name, user_info)


def parse_proxy_uri(uri):
    """
    This function parses and validates a HTTP proxy URI.
    If the URI is valid, it returns a :class:`ProxyURI`.
    Otherwise it raises an :exc:`~websockets.exceptions.InvalidURI` exception.
    """
    uri = urllib.parse.urlparse(uri)
    try:
        assert uri.scheme in ['http', 'https']
        assert uri.hostname is not None
        assert uri.path == ''
        assert uri.params == ''
        assert uri.query == ''
        assert uri.fragment == ''
    except AssertionError as exc:
        raise InvalidURI("{} isn't a valid URI".format(uri)) from exc

    secure = uri.scheme == 'https'
    host = uri.hostname
    port = uri.port or (443 if secure else 80)
    user_info = None
    if uri.username or uri.password:
        user_info = (uri.username, uri.password)
    return ProxyURI(secure, host, port, user_info)