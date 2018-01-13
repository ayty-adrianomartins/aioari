#
# Copyright (c) 2013, Digium, Inc.
# Copyright (c) 2016, fokin.denis@gmail.com
#

"""ARI client library
"""

import ari.asyncclient
import swaggerpy.http_client

AsyncClient = asyncclient.AsyncClient


def connect(base_url, username, password, loop=None):
    """Helper method for easily connecting to ARI.

    :param base_url: Base URL for Asterisk HTTP server (http://localhost:8088/)
    :param username: ARI username
    :param password: ARI password.
    :return:
    """
    http_client = swaggerpy.http_client.AsynchronousHttpClient(username, password, loop)
    return AsyncClient(base_url, http_client)
