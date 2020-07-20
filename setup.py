#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="pytest-boardfarm",
    version="0.2.0",
    author="Various",
    maintainer="Various",
    license="MIT",
    url="https://github.com/lgirdk/pytest-boardfarm",
    description="Integratate boardfarm as a pytest plugin",
    long_description=read("README.rst"),
    py_package=["pytest_boardfarm"],
    python_requires=">=3.6",
    install_requires=["pytest>=5.4.3"],
    setup_requires=["setuptools_scm"],
    classifiers=[
        "Development Status :: 1 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["pytest_boardfarm = pytest_boardfarm.plugin",],},
)
