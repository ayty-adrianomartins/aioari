#!/usr/bin/env python

"""WebSocket testing.
"""

import pytest

pytest.skip()

import aioari
import aiohttp
import asyncio
import httpretty

from .utils import AriTestCase
from aioswagger11.http_client import AsynchronousHttpClient

BASE_URL = "http://ari.py/ari"

GET = httpretty.GET
PUT = httpretty.PUT
POST = httpretty.POST
DELETE = httpretty.DELETE


# noinspection PyDocstring
@pytest.mark.usefixtures("httpretty")
class TestWebSocket(AriTestCase):
    def setUp(self, event_loop):
        super(TestWebSocket, self).setUp(event_loop)
        self.uut = event_loop.run_until_complete(connect(BASE_URL, [], loop=event_loop))
        self.actual = []

    def tearDown(self, event_loop):
        event_loop.run_until_complete(self.uut.close())
        super().tearDown(event_loop)

    def record_event(self, event):
        self.actual.append(event)

    @pytest.mark.asyncio
    async def test_empty(self, event_loop):
        self.uut.on_event('ev', self.record_event)
        await self.uut.run('test')
        assert self.actual == []

    @pytest.mark.asyncio
    async def test_series(self, event_loop):
        messages = [
            '{"type": "ev", "data": 1}',
            '{"type": "ev", "data": 2}',
            '{"type": "not_ev", "data": 3}',
            '{"type": "not_ev", "data": 5}',
            '{"type": "ev", "data": 9}'
        ]
        self.uut.on_event("ev", self.record_event)
        await self.uut.run('test', _test_msgs=messages)

        expected = [
            {"type": "ev", "data": 1},
            {"type": "ev", "data": 2},
            {"type": "ev", "data": 9}
        ]
        assert self.actual == expected

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_loop):
        messages = [
            '{"type": "ev", "data": 1}',
            '{"type": "ev", "data": 2}'
        ]
        self.once_ran = 0

        def only_once(event):
            self.once_ran += 1
            assert event['data'] == 1
            self.once.close()

        def both_events(event):
            self.record_event(event)

        self.once = self.uut.on_event("ev", only_once)
        self.both = self.uut.on_event("ev", both_events)
        await self.uut.run('test', _test_msgs=messages)

        expected = [
            {"type": "ev", "data": 1},
            {"type": "ev", "data": 2}
        ]
        assert self.actual == expected
        assert self.once_ran == 1

    @pytest.mark.asyncio
    async def test_on_channel(self, event_loop):
        self.serve(DELETE, 'channels', 'test-channel')
        messages = [
            '{ "type": "StasisStart", "channel": { "id": "test-channel" } }'
        ]

        async def cb(channel, event):
            self.record_event(event)
            await channel.hangup()

        self.uut.on_channel_event('StasisStart', cb)
        await self.uut.run('test', _test_msgs=messages)

        expected = [
            {"type": "StasisStart", "channel": {"id": "test-channel"}}
        ]
        assert self.actual == expected

    @pytest.mark.asyncio
    async def test_on_channel_unsubscribe(self, event_loop):
        messages = [
            '{ "type": "StasisStart", "channel": { "id": "test-channel1" } }',
            '{ "type": "StasisStart", "channel": { "id": "test-channel2" } }'
        ]

        def only_once(channel, event):
            self.record_event(event)
            self.once.close()

        self.once = self.uut.on_channel_event('StasisStart', only_once)
        await self.uut.run('test', _test_msgs=messages)

        expected = [
            {"type": "StasisStart", "channel": {"id": "test-channel1"}}
        ]
        assert self.actual == expected

    @pytest.mark.asyncio
    async def test_channel_on_event(self, event_loop):
        self.serve(GET, 'channels', 'test-channel',
                   body='{"id": "test-channel"}')
        self.serve(DELETE, 'channels', 'test-channel')
        messages = [
            '{"type": "ChannelStateChange", "channel": {"id": "ignore-me"}}',
            '{"type": "ChannelStateChange", "channel": {"id": "test-channel"}}'
        ]

        channel = await self.uut.channels.get(channelId='test-channel')

        async def cb(channel, event):
            self.record_event(event)
            await channel.hangup()

        channel.on_event('ChannelStateChange', cb)
        await self.uut.run('test', _test_msgs=messages)

        expected = [
            {"type": "ChannelStateChange", "channel": {"id": "test-channel"}}
        ]
        assert self.actual == expected

    @pytest.mark.asyncio
    async def test_arbitrary_callback_arguments(self, event_loop):
        self.serve(GET, 'channels', 'test-channel',
                   body='{"id": "test-channel"}')
        self.serve(DELETE, 'channels', 'test-channel')
        messages = [
            '{"type": "ChannelDtmfReceived", "channel": {"id": "test-channel"}}'
        ]
        obj = {'key': 'val'}

        channel = await self.uut.channels.get(channelId='test-channel')

        async def cb(channel, event, arg):
            if arg == 'done':
                await channel.hangup()
            else:
                self.record_event(arg)

        def cb2(channel, event, arg1, arg2=None, arg3=None):
            self.record_event(arg1)
            self.record_event(arg2)
            self.record_event(arg3)

        channel.on_event('ChannelDtmfReceived', cb, 1)
        channel.on_event('ChannelDtmfReceived', cb, arg=2)
        channel.on_event('ChannelDtmfReceived', cb, obj)
        channel.on_event('ChannelDtmfReceived', cb2, 2.0, arg3=[1, 2, 3])
        channel.on_event('ChannelDtmfReceived', cb, 'done')
        await self.uut.run('test', _test_msgs=messages)

        expected = [1, 2, obj, 2.0, None, [1, 2, 3]]
        assert self.actual == expected

    @pytest.mark.asyncio
    async def test_bad_event_type(self, event_loop):
        try:
            self.uut.on_object_event(
                'BadEventType', self.noop, self.noop, 'Channel')
            self.fail("Event does not exist")
        except ValueError:
            pass

    @pytest.mark.asyncio
    async def test_bad_object_type(self, event_loop):
        try:
            self.uut.on_object_event('StasisStart', self.noop, self.noop, 'Bridge')
            self.fail("Event has no bridge")
        except ValueError:
            pass

    # noinspection PyUnusedLocal
    def noop(self, *args, **kwargs):
        self.fail("Noop unexpectedly called")

class FakeMsg:
    def __init__(self,data):
        self.data = data
        self.type = aiohttp.WSMsgType.TEXT

class WebSocketStubConnection(object):
    """Stub WebSocket connection.

    :param messages:
    """

    def __init__(self, messages, loop=None):
        self.q = asyncio.Queue(loop=loop)
        for m in messages:
            self.q.put_nowait(m)

    async def receive(self):
        """Fake receive method

        :return: Next message, or None if no more messages.
        """
        if self.q is None:
            return None
        try:
            msg = self.q.get_nowait()
        except asyncio.QueueEmpty:
            msg = None
        if msg is None:
            self.q = None
        if msg is not None:
            msg = FakeMsg(msg)
        return msg

    def push(self, msg):
        self.q.put_nowait(msg)

    async def send_close(self):
        """Fake send_close method
        """
        if self.q is not None:
            self.q.put(None)

    async def close(self):
        """Fake close method
        """
        if self.q is not None:
            self.q.put(None)


class WebSocketStubClient(AsynchronousHttpClient):
    """Stub WebSocket client.

    :param messages: List of messages to return.
    :type  messages: list
    """

    def __init__(self, messages, loop=None):
        super(WebSocketStubClient, self).__init__("fake_user","fake_pass", loop=loop)
        self.messages = messages

    async def ws_connect(self, url, params=None):
        """Fake connect method.

        Returns a WebSocketStubConnection, which itself returns the series of
        messages from WebSocketStubClient in its recv() method.

        :param url: Ignored.
        :param params: Ignored.
        :return: Stub connection.
        """
        return WebSocketStubConnection(self.messages, self.session._loop)


def raise_exceptions(ex):
    """Testing exception handler for ARI client.

    :param ex: Exception caught by the event loop.
    """
    raise


async def connect(base_url, messages, loop=None):
    """Connect, with a WebSocket client test double that merely retuns the
     series of given messages.

    :param base_url: Base URL for REST calls.
    :param messages: Message strings to return from the WebSocket.
    :return: ARI client with stubbed WebSocket.
    """
    http_client = WebSocketStubClient(messages, loop=loop)
    client = aioari.Client(base_url, http_client)
    client.exception_handler = raise_exceptions
    await client.init()
    return client

if __name__ == '__main__':
    pytest.main()

