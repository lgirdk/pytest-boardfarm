# Copyright (c) 2020
#
# All rights reserved.
#
# This file is distributed under the Clear BSD license.
# The full text can be found in LICENSE in the root directory.

from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

__pypi_url__ = "https://github.com/lgirdk/pytest-boardfarm"
