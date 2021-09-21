#!/usr/bin/env python

import aioari
from aiohttp import web_exceptions
import httpretty
import json
import pytest
from urllib.request import urlopen

from .utils import AriTestCase


GET = httpretty.GET
PUT = httpretty.PUT
POST = httpretty.POST
DELETE = httpretty.DELETE


# noinspection PyDocstring
@pytest.mark.usefixtures("httpretty")
class TestClient(AriTestCase):
    def setUp(self, event_loop):
        """Setup httpretty; create ARI client.
        """
        super().setUp(event_loop)
        self.uut = event_loop.run_until_complete(aioari.connect('http://ari.py/', 'test', 'test'))

    def tearDown(self, event_loop):
        
        event_loop.run_until_complete(self.uut.close())
        super().tearDown(event_loop)

    @pytest.mark.asyncio
    async def test_docs(self):
        fp = urlopen("http://ari.py/ari/api-docs/resources.json")
        try:
            actual = json.load(fp)
            assert self.BASE_URL == actual['basePath']
        finally:
            fp.close()

    @pytest.mark.asyncio
    async def test_empty_listing(self):
        self.serve(GET, 'channels', body='[]')
        actual = await self.uut.channels.list()
        assert actual == []

    @pytest.mark.asyncio
    async def test_one_listing(self):
        self.serve(GET, 'channels', body='[{"id": "test-channel"}]')
        self.serve(DELETE, 'channels', 'test-channel')

        actual = await self.uut.channels.list()
        assert len(actual) == 1
        await actual[0].hangup()

    @pytest.mark.asyncio
    async def test_play(self):
        self.serve(GET, 'channels', 'test-channel',
                   body='{"id": "test-channel"}')
        self.serve(POST, 'channels', 'test-channel', 'play',
                   body='{"id": "test-playback"}')
        self.serve(DELETE, 'playbacks', 'test-playback')

        channel = await self.uut.channels.get(channelId='test-channel')
        playback = await channel.play(media='sound:test-sound')
        await playback.stop()

    @pytest.mark.asyncio
    async def test_bad_resource(self):
        try:
            await self.uut.i_am_not_a_resource.list()
            self.fail("How did it find that resource?")
        except AttributeError:
            pass

    @pytest.mark.asyncio
    async def test_bad_repo_method(self):
        try:
            await self.uut.channels.i_am_not_a_method()
            self.fail("How did it find that method?")
        except AttributeError:
            pass

    @pytest.mark.asyncio
    async def test_bad_object_method(self):
        self.serve(GET, 'channels', 'test-channel',
                   body='{"id": "test-channel"}')

        try:
            channel = await self.uut.channels.get(channelId='test-channel')
            await channel.i_am_not_a_method()
            self.fail("How did it find that method?")
        except AttributeError:
            pass

    @pytest.mark.asyncio
    async def test_bad_param(self):
        try:
            await self.uut.channels.list(i_am_not_a_param='asdf')
            self.fail("How did it find that param?")
        except TypeError:
            pass

    @pytest.mark.asyncio
    async def test_bad_response(self):
        self.serve(GET, 'channels', body='{"message": "This is just a test"}',
                   status=500)
        try:
            await self.uut.channels.list()
            self.fail("Should have thrown an exception")
        except web_exceptions.HTTPError as e:
            assert e.response.status_code == 500
            assert (await e.response.json()) == {"message": "This is just a test"}

    @pytest.mark.asyncio
    async def test_endpoints(self):
        self.serve(GET, 'endpoints',
                   body='[{"technology": "TEST", "resource": "1234"}]')
        self.serve(GET, 'endpoints', 'TEST', '1234',
                   body='{"technology": "TEST", "resource": "1234"}')

        endpoints = await self.uut.endpoints.list()
        assert len(endpoints) == 1
        endpoint = await endpoints[0].get()
        assert endpoint.json['technology'] == "TEST"
        assert endpoint.json['resource'] == "1234"

    @pytest.mark.asyncio
    async def test_live_recording(self):
        self.serve(GET, 'recordings', 'live', 'test-recording',
                   body='{"name": "test-recording"}')
        self.serve(DELETE, 'recordings', 'live', 'test-recording', status=204)

        recording = await self.uut.recordings.getLive(recordingName='test-recording')
        await recording.cancel()

    @pytest.mark.asyncio
    async def test_stored_recording(self):
        self.serve(GET, 'recordings', 'stored', 'test-recording',
                   body='{"name": "test-recording"}')
        self.serve(DELETE, 'recordings', 'stored', 'test-recording',
                   status=204)

        recording = await self.uut.recordings.getStored(
            recordingName='test-recording')
        await recording.deleteStored()

    @pytest.mark.asyncio
    async def test_mailboxes(self):
        self.serve(PUT, 'mailboxes', '1000',
                   body='{"name": "1000", "old_messages": "1", "new_messages": "3"}')

        mailbox = await self.uut.mailboxes.update(
            mailboxName='1000',
            oldMessages='1',
            newMessages='3')
        assert mailbox['name'] == "1000"
        assert mailbox['old_messages'] == "1"
        assert mailbox['new_messages'] == "3"

    @pytest.mark.asyncio
    async def test_device_state(self):
        self.serve(PUT, 'deviceStates', 'foobar',
                   body='{"name": "foobar", "state": "BUSY"}')
        device_state = await self.uut.deviceStates.update(
            deviceName='foobar',
            deviceState='BUSY')
        assert device_state['name'] == "foobar"
        assert device_state['state'] == "BUSY"


if __name__ == '__main__':
    pytest.main()
