#!/usr/bin/env python

"""Brief example of using the channel API.

This app will answer any channel sent to Stasis(hello), and play "Hello,
world" to the channel. For any DTMF events received, the number is played back
to the channel. Press # to hang up, and * for a special message.
"""

#
# Copyright (c) 2013, Digium, Inc.
#

import ari
import asyncio
import logging

async def on_dtmf(channel, event):
    """Callback for DTMF events.

    When DTMF is received, play the digit back to the channel. # hangs up,
    * plays a special message.

    :param channel: Channel DTMF was received from.
    :param event: Event.
    """
    digit = event['digit']
    print(digit)
    if digit == '#':
        await channel.play(media='sound:goodbye')
        await channel.continueInDialplan()
    elif digit == '*':
        await channel.play(media='sound:asterisk-friend')
    else:
        await channel.play(media='sound:digits/%s' % digit)


async def on_start(channel, event):
    """Callback for StasisStart events.

    On new channels, register the on_dtmf callback, answer the channel and
    play "Hello, world"

    :param channel: Channel DTMF was received from.
    :param event: Event.
    """
    print(channel['channel'], event)
    channel['channel'].on_event('ChannelDtmfReceived', on_dtmf)
    await channel['channel'].answer()
    await channel['channel'].play(media='sound:hello-world')

async def on_end(channel, event):
        """Callback for StasisEnd events.

        On new channels, register the on_dtmf callback, answer the channel and
        play "Hello, world"

        :param channel: Channel DTMF was received from.
        :param event: Event.
        """
        print(channel, event)

sessions = {}

logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()
client = ari.connect('http://192.168.254.60:8088/', 'remari', '@rip@$$', loop=loop)
loop.run_until_complete(client.init())
client.on_channel_event('StasisStart', on_start)
client.on_channel_event('StasisEnd', on_end)
# Run the WebSocket
loop.run_until_complete(client.run(apps="hello"))
