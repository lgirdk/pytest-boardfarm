import pytest
from boardfarm.bft import logger
from boardfarm.exceptions import CodeError, ContingencyCheckError, SkipTest
from boardfarm.tests import bft_base_test


class myBftBaseTest(bft_base_test.BftBaseTest):
    """None of the tests in this module should make the overall pytest fail."""

    @staticmethod
    def ok(*args, **kwargs):
        pass

    def __init__(self, *args, **kwargs):
        self.result_grade = ""
        self._hw = type("hw", (object,), {"consoles": []})()
        self.td_step = type("tstclass", (object,), {"td_final_result": None})()
        self.config = type("tstclass1", (object,), {"devices": [], "retry": 0})()
        board = type(
            "tstclass2",
            (object,),
            {"hw": self._hw, "consoles": [], "touch": myBftBaseTest.ok},
        )()
        self.dev = type("tstclass3", (object,), {"board": None})()
        self.dev.board = board
        self.logged = {}

    def recover(self):
        pass


class AlwaysPasses(myBftBaseTest):
    def test_main(self):
        logger.info("This always passes")


@pytest.mark.xfail(strict=True, reason="Intentional CodeError", raises=CodeError)
class AlwaysFails(myBftBaseTest):
    def test_main(self):
        logger.info("This test always fails, but pytest overall does NOT!")
        """We have to use CodeError instead the more appropriate TestError as
        the latter is intercepted by pytest (due to the Test prefix) which
        generates a warning."""
        raise CodeError()


class ThisIsSkippedFromBFT(myBftBaseTest):
    def test_main(self):
        logger.info("This is skipped from bft_base_test pytest overall must NOT fail!")
        logger.info("It raises a SkipTest but with 'SKIP' in self.result_grade")
        raise SkipTest()


@pytest.mark.skip(reason="This is skipped  with a marker")
class ThisWouldFailButIsSkipped(myBftBaseTest):
    def test_main(self):
        assert 0, "Should never get to this point!!!!!"


@pytest.mark.xfail(
    strict=True, raises=SkipTest, reason="Intentional Contingency check error"
)
class ThisIsSkippedFromPytest(myBftBaseTest):
    def test_main(self):
        logger.info("This is a Contigency Check failure")
        logger.info("it raises a SkipTest but with 'CC FAIL' in self.result_grade")
        raise ContingencyCheckError("Forced failure for intergration test")
