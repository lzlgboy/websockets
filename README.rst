.. image:: logo/horizontal.svg
   :width: 480px
   :alt: websockets

|rtd| |pypi-v| |pypi-pyversions| |pypi-l| |pypi-wheel| |circleci| |codecov|

.. |rtd| image:: https://readthedocs.org/projects/websockets/badge/?version=latest
   :target: https://websockets.readthedocs.io/

.. |pypi-v| image:: https://img.shields.io/pypi/v/websockets.svg
    :target: https://pypi.python.org/pypi/websockets

.. |pypi-pyversions| image:: https://img.shields.io/pypi/pyversions/websockets.svg
    :target: https://pypi.python.org/pypi/websockets

.. |pypi-l| image:: https://img.shields.io/pypi/l/websockets.svg
    :target: https://pypi.python.org/pypi/websockets

.. |pypi-wheel| image:: https://img.shields.io/pypi/wheel/websockets.svg
    :target: https://pypi.python.org/pypi/websockets

.. |circleci| image:: https://img.shields.io/circleci/project/github/aaugustin/websockets.svg
   :target: https://circleci.com/gh/aaugustin/websockets

.. |codecov| image:: https://codecov.io/gh/aaugustin/websockets/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aaugustin/websockets

What is ``websockets``?
-----------------------

``websockets`` is a library for building WebSocket servers_ and clients_ in
Python with a focus on correctness and simplicity.

.. _servers: https://github.com/aaugustin/websockets/blob/master/example/server.py
.. _clients: https://github.com/aaugustin/websockets/blob/master/example/client.py

Built on top of ``asyncio``, Python's standard asynchronous I/O framework, it
provides an elegant coroutine-based API.

`Documentation is available on Read the Docs. <https://websockets.readthedocs.io/>`_

Here's how a client sends and receives messages:

.. copy-pasted because GitHub doesn't support the include directive

.. code:: python

    #!/usr/bin/env python

    import asyncio
    import websockets

    async def hello(uri):
        async with websockets.connect(uri) as websocket:
            await websocket.send("Hello world!")
            await websocket.recv()

    asyncio.get_event_loop().run_until_complete(
        hello('ws://localhost:8765'))

And here's an echo server:

.. code:: python

    #!/usr/bin/env python

    import asyncio
    import websockets

    async def echo(websocket, path):
        async for message in websocket:
            await websocket.send(message)

    asyncio.get_event_loop().run_until_complete(
        websockets.serve(echo, 'localhost', 8765))
    asyncio.get_event_loop().run_forever()

Does that look good?

`Get started with the tutorial! <https://websockets.readthedocs.io/en/stable/intro.html>`_

.. raw:: html

    <hr>
    <img align="left" height="150" width="150" src="https://raw.githubusercontent.com/aaugustin/websockets/master/logo/tidelift.png">
    <h3 align="center"><i>Professionally supported websockets is now available</i></h3>
    <p align="center"><i>Tidelift gives software development teams a single source for purchasing and maintaining their software, with professional grade assurances from the experts who know it best, while seamlessly integrating with existing tools.</i></p>
    <p align="center"><b><i><a href="https://tidelift.com/subscription/pkg/pypi-websockets?utm_source=pypi-websockets&utm_medium=referral&utm_campaign=readme">Get supported websockets with the Tidelift Subscription</a></i></b></p>
    <hr>
    <p>(If you contribute to ``websockets`` and would like to become an official support provider, <a href="https://fractalideas.com/">let me know</a>.)</p>

Why should I use ``websockets``?
--------------------------------

The development of ``websockets`` is shaped by four principles:

1. **Simplicity**: all you need to understand is ``msg = await ws.recv()`` and
   ``await ws.send(msg)``; ``websockets`` takes care of managing connections
   so you can focus on your application.

2. **Robustness**: ``websockets`` is built for production; for example it was
   the only library to `handle backpressure correctly`_ before the issue
   became widely known in the Python community.

3. **Quality**: ``websockets`` is heavily tested. Continuous integration fails
   under 100% branch coverage. Also it passes the industry-standard `Autobahn
   Testsuite`_.

4. **Performance**: memory use is configurable. An extension written in C
   accelerates expensive operations. It's pre-compiled for Linux, macOS and
   Windows and packaged in the wheel format for each system and Python version.

Documentation is a first class concern in the project. Head over to `Read the
Docs`_ and see for yourself.

.. _Read the Docs: https://websockets.readthedocs.io/
.. _handle backpressure correctly: https://vorpus.org/blog/some-thoughts-on-asynchronous-api-design-in-a-post-asyncawait-world/#websocket-servers
.. _Autobahn Testsuite: https://github.com/aaugustin/websockets/blob/master/compliance/README.rst

Proxy support
-------------

This fork merges the proxy support work done in https://github.com/aaugustin/websockets/pull/422 , adapted
for Python 3.7.  It also adds support for a proxy_headers argument that can be used to deal with proxy authentication
requirements.

Proxy authentication via NTLM and SSPI
--------------------------------------

NTLM is a challenge-response authentication protocol

SSPI is a way to get the response using a Window's user's current login (without needing to know their password)

To deal with a proxy requiring NTLM authentication, only when NTLM authentication is needed,
you can catch the 407 "Proxy Authentication Required" exception and then do the NTLM authentication, using SSPI,
to get the value to use for proxy_headers

.. code:: python

    try:
        self.socket = await websockets.connect(url, proxy_headers=self.proxy_headers)
    except ValueError as e:
        if "407" in str(e):
            self.proxy_headers = await get_proxy_auth_header_sspi(self.sfp.get_session(), os.environ['HTTPS_PROXY'] if url.startswith("wss") else os.environ['HTTP_PROXY'])

            # headers are returned in a name-value dictionary but websockets use list of tuples so convert..
            self.proxy_headers = list(self.proxy_headers.items())

            self.socket = await websockets.connect(url, proxy_headers=self.proxy_headers)
        else:
            raise

The aio_proxy_sspi_auth function is provided below.  It's a work in progress and doesn't belong inside the websockets
package, because it's something that should be used  when making requests via aiohttp too (see below).
Also, you can see that this is something that just works for a specific use case (NTLM SSPI, not Kerberos,
not username/password) so I don't feel it's generic enough to suggest adding to aiohttp at this stage.  Use
at own risk :)

.. code:: python

    import base64
    import hashlib
    import logging
    import socket
    import struct


    import pywintypes
    import sspi
    import sspicon
    import win32security

    try:
        from urllib.parse import urlparse
    except ImportError:
        from urlparse import urlparse

    _logger = logging.getLogger(__name__)

    async def get_proxy_auth_header_sspi(session, proxy_url, peercert = None, delegate=False, host=None):
        """Performs a GET request against the proxy server to start and complete an NTLM authentication process

        Invoke this after getting a 407 error.  Returns the proxy_headers to use going forwards (in dict format)

        Overview of the protocol/exchange: https://docs.microsoft.com/en-us/openspecs/office_protocols/ms-grvhenc/b9e676e7-e787-4020-9840-7cfe7c76044a

        Inspired by: https://github.com/brandond/requests-negotiate-sspi/blob/master/requests_negotiate_sspi/requests_negotiate_sspi.py
        (But this is async, and it's for proxy auth not normal www auth)
        """
        scheme = 'NTLM'

        host = None
        if host is None:
            targeturl = urlparse(proxy_url)
            host= targeturl.hostname
            try:
                host= socket.getaddrinfo(host, None, 0, 0, 0, socket.AI_CANONNAME)[0][3]
            except socket.gaierror as e:
                _logger.info('Skipping canonicalization of name %s due to error: %s', host, e)

        targetspn = '{}/{}'.format("HTTP", host)

        # Set up SSPI connection structure
        pkg_info = win32security.QuerySecurityPackageInfo(scheme)
        clientauth = sspi.ClientAuth(scheme, targetspn=targetspn)#, auth_info=self._auth_info)
        sec_buffer = win32security.PySecBufferDescType()

        # Calling sspi.ClientAuth with scflags set requires you to specify all the flags, including defaults.
        # We just want to add ISC_REQ_DELEGATE.
        #if delegate:
        #    clientauth.scflags |= sspicon.ISC_REQ_DELEGATE

        # Channel Binding Hash (aka Extended Protection for Authentication)
        # If this is a SSL connection, we need to hash the peer certificate, prepend the RFC5929 channel binding type,
        # and stuff it into a SEC_CHANNEL_BINDINGS structure.
        # This should be sent along in the initial handshake or Kerberos auth will fail.
        if peercert is not None:
            md = hashlib.sha256()
            md.update(peercert)
            appdata = 'tls-server-end-point:'.encode('ASCII')+md.digest()
            cbtbuf = win32security.PySecBufferType(pkg_info['MaxToken'], sspicon.SECBUFFER_CHANNEL_BINDINGS)
            cbtbuf.Buffer = struct.pack('LLLLLLLL{}s'.format(len(appdata)), 0, 0, 0, 0, 0, 0, len(appdata), 32, appdata)
            sec_buffer.append(cbtbuf)

        # Send initial challenge auth header
        try:
            error, auth = clientauth.authorize(sec_buffer)
            headers = {'Proxy-Authorization': f'{scheme} {base64.b64encode(auth[0].Buffer).decode("ASCII")}'}
            response2 = await session.get(proxy_url, headers=headers)

            _logger.debug('Got response: ' + str(response2))
            #Sending Initial Context Token - error={} authenticated={}'.format(error, clientauth.authenticated))
        except pywintypes.error as e:
            _logger.debug('Error calling {}: {}'.format(e[1], e[2]), exc_info=e)
            raise

        # expect to get 407 error and proxy-authenticate header
        if response2.status != 407:
            raise Exception(f'Expected 407, got {res.status} status code')

        # Extract challenge message from server
        challenge = [val[len(scheme)+1:] for val in response2.headers.get('proxy-Authenticate', '').split(', ') if scheme in val]
        if len(challenge) != 1:
            raise Exception('Did not get exactly one {} challenge from server.'.format(scheme))

        # Add challenge to security buffer
        tokenbuf = win32security.PySecBufferType(pkg_info['MaxToken'], sspicon.SECBUFFER_TOKEN)
        tokenbuf.Buffer = base64.b64decode(challenge[0])
        sec_buffer.append(tokenbuf)
        _logger.debug('Got Challenge Token (NTLM)')

        # Perform next authorization step
        try:
            error, auth = clientauth.authorize(sec_buffer)
            headers = {'proxy-Authorization': '{} {}'.format(scheme, base64.b64encode(auth[0].Buffer).decode('ASCII'))}
            _logger.debug(str(headers))
        except pywintypes.error as e:
            _logger.debug('Error calling {}: {}'.format(e[1], e[2]), exc_info=e)
            raise

        return headers

Corporate proxies are often automatically configured using a PAC approach, so you can use pypac to get
that and store the result in the environ variables, which are picked up by aiohttp if you set trust_env to true

.. code:: python

        if auto_proxy_config:
            import pypac
            pac = pypac.get_pac()
            if pac:
                resolver = pypac.resolver.ProxyResolver(pac)
                proxies = resolver.get_proxy_for_requests(url)
                os.environ['HTTP_PROXY'] = proxies.get('http') or ''
                os.environ['HTTPS_PROXY'] = proxies.get('https') or ''
                logger.info(f"Proxy Auto Config: HTTP:{os.environ['HTTP_PROXY']} HTTPS:{os.environ['HTTPS_PROXY']}")

Lastly, if you also have to do normal web requests and not just websockets, you need a similar 407 challenge
response handler when doing such requests:

.. code:: python


    def get_session(self):
        if not hasattr(self, 'session'):
            # trust_env means read HTTPS_PROXY from environment
            self.session = ClientSession(trust_env=True)
        return self.session

    #... and then when you need to do a request
        try:
            res = await self.session.post(url, json=body, proxy_headers=self.proxy_headers)
        except ClientHttpProxyError as e:
            if e.status == 407:
                logger.info("Proxy 407 error occurred - starting proxy NTLM auth negotiation")
                self.proxy_headers = await get_proxy_auth_header_sspi(self.session, os.environ['HTTPS_PROXY'] if self.url.startswith("https") else os.environ['HTTP_PROXY'])
                res = await self.session.post(self.url, json=body, proxy_headers=self.proxy_headers)
            else:
                raise


Why shouldn't I use ``websockets``?
-----------------------------------

* If you prefer callbacks over coroutines: ``websockets`` was created to
  provide the best coroutine-based API to manage WebSocket connections in
  Python. Pick another library for a callback-based API.
* If you're looking for a mixed HTTP / WebSocket library: ``websockets`` aims
  at being an excellent implementation of :rfc:`6455`: The WebSocket Protocol
  and :rfc:`7692`: Compression Extensions for WebSocket. Its support for HTTP
  is minimal — just enough for a HTTP health check.
* If you want to use Python 2: ``websockets`` builds upon ``asyncio`` which
  only works on Python 3. ``websockets`` requires Python ≥ 3.6.1.

What else?
----------

Bug reports, patches and suggestions are welcome!

To report a security vulnerability, please use the `Tidelift security
contact`_. Tidelift will coordinate the fix and disclosure.

.. _Tidelift security contact: https://tidelift.com/security

For anything else, please open an issue_ or send a `pull request`_.

.. _issue: https://github.com/aaugustin/websockets/issues/new
.. _pull request: https://github.com/aaugustin/websockets/compare/

Participants must uphold the `Contributor Covenant code of conduct`_.

.. _Contributor Covenant code of conduct: https://github.com/aaugustin/websockets/blob/master/CODE_OF_CONDUCT.md

``websockets`` is released under the `BSD license`_.

.. _BSD license: https://github.com/aaugustin/websockets/blob/master/LICENSE
