from unittest.mock import MagicMock

from pytest_boardfarm.plugin import pytest_unconfigure


class _PathStub:
    def __init__(self, name, content=None):
        self.name = name
        self.parent = ""
        self.content = content
        self.written_content = None

    def exists(true):
        return True

    def read_text(self):
        return self.content

    def rename(self, path):
        self.renamed_path = path

    def write_text(self, content):
        self.written_content = content


def test_pytest_unconfigure_remove_control_chars(mocker):
    xml_content = r"sample text"
    mocked_path = _PathStub("xmlpath", xml_content)
    config = MagicMock(autospec=True)
    config.option.xmlpath = "xmlpath"
    mocker.patch("pytest_boardfarm.plugin.Path", return_value=mocked_path)
    pytest_unconfigure(config)
    assert "" not in mocked_path.written_content
    assert "sample text" == mocked_path.written_content


def test_pytest_unconfigure_remove_escape_sequence(mocker):
    xml_content = "\x1b[00m\x1b[01;31mfile.zip\x1b[00m\r\n\x1b[01;31m"
    mocked_path = _PathStub("xmlpath", xml_content)
    config = MagicMock(autospec=True)
    config.option.xmlpath = "xmlpath"
    mocker.patch("pytest_boardfarm.plugin.Path", return_value=mocked_path)
    pytest_unconfigure(config)
    expected_content = "file.zip\r\n"
    assert expected_content == mocked_path.written_content
