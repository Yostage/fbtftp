# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import tempfile
import unittest

from fbtftp.base_server import BaseServer
'''
This script stresses the TFTP server by sending malformed RRQ packets and
checking whether it crashed.

NOTE: this test ONLY checks if the server crashed, no output or return code is
checked.
'''

RRQ = b'\x00\x01'

# if you want to add more packets for the tests, do it here
TEST_PAYLOADS = (
    RRQ + b'some_fi',
    RRQ + b'some_file\x00',
    RRQ + b'some_file\x00bina',
    RRQ + b'some_file\x00binascii\x00',
    RRQ + b'some_file\x00binascii\x00a',
    RRQ + b'some_file\x00binascii\x00a\x00',
    RRQ + b'some_file\x00binascii\x00a\x00b\x00',
)


class MockSocketListener(object):
    def __init__(self, network_queue):
        self._network_queue = network_queue

    def recvfrom(self, blocksize):
        data = self._network_queue.pop(0)
        peer = '::1'  # assuming v6, but this is invariant for this test
        return data, peer

    def close(self):
        pass


class StaticServer(BaseServer):
    def __init__(
        self, address, port, retries, timeout, root, stats_callback,
        network_queue
    ):
        BaseServer.__init__(self, address, port, retries, timeout)
        self._root = root
        # mock the network
        self._listener = MockSocketListener(network_queue)


class TestServerMalformedPacket(unittest.TestCase):
    def setUp(self):
        # this is removed automatically when the test ends
        self.tmpdir = tempfile.TemporaryDirectory()
        self.host = '::'  # assuming v6, but this is invariant for this test
        self.port = 0  # let the kernel choose
        self.timeout = 2

    def testMalformedPackets(self):
        for payload in TEST_PAYLOADS:
            server = StaticServer(
                self.host, self.port, 2, 2, self.tmpdir, None, [payload]
            )
            server.on_new_data()
            server.close()
            del server
