#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
# Copyright (c) 2018, Matthias Urlichs
#

import os

from setuptools import setup

setup(
    name="aioari",
    version="0.10.0",
    license="BSD 3-Clause License",
    description="Asynchronous library for accessing the Asterisk REST Interface",
    long_description=open(os.path.join(os.path.dirname(__file__),
                                       "README.rst")).read(),
    author="Matthias Urlichs",
    author_email="matthias@urlichs.de",
    url="https://github.com/M-o-a-T/aioari",
    packages=["aioari"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Telephony",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    tests_require=["coverage", "httpretty", "pytest"],
    install_requires=["aioswagger11"],
)
