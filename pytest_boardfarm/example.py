import unittest

import pytest


# Add decorators to just the base class
@pytest.mark.usefixtures("boardfarm_fixtures")
class MyBaseTestClass(unittest.TestCase):
    pass


class RouterPingWanDev(MyBaseTestClass):
    """Router can ping device through WAN interface."""

    def test_main(self):
        board = self.dev.board
        wan = self.dev.wan
        if not wan:
            msg = "No WAN Device defined, skipping ping WAN test."
            self.skipTest(msg)
        board.sendline(f"\nping -c5 {wan.gw}")
        board.expect("5 (packets )?received", timeout=15)
        board.expect(board.prompt)

    def recover(self):
        self.dev.board.sendcontrol("c")
