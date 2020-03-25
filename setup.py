#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='boardfarm_pytest',
      version='1.0.0',
      description='Makes boardfarm available as a pytest plugin',
      author='Various',
      url='',
      packages=find_packages(),
      package_data={'': ['*.txt', '*.json', '*.cfg', '*.md', '*.csv']},
      include_package_data=True)
