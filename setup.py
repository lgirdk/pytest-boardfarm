#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='pytest_boardfarm',
    version='1.0.0',
    description='Makes boardfarm available as a pytest plugin',
    author='Various',
    url='',
    packages=find_packages(),
    package_data={'': ['*.txt', '*.json', '*.cfg', '*.md', '*.csv']},
    include_package_data=True,
    # the following makes a plugin available to pytest
    entry_points={"pytest11": ["boardfarm = pytest_boardfarm"]},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"])
