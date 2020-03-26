import unittest

import pytest


# Add decorators to just the base class
@pytest.mark.usefixtures("standard")
class MyBaseTestClass(unittest.TestCase):
    pass


class RouterPingWanDev(MyBaseTestClass):
    '''Router can ping device through WAN interface.'''
    def runTest(self):
        pass
