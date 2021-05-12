import unittest

from apps.utils.strings import linux_linebreaks


class TestStringsUtils(unittest.TestCase):
    def setUp(self):
        pass

    def test_windows_linebreaks(self):
        """\r\n should be converted to \n"""
        test = "Test\r\nString\r\n"
        self.assertEqual("Test\nString\n", linux_linebreaks(test))

    def test_html_linebreaks(self):
        """<br>, <br/> and <br /> should be converted to \n"""
        test = "Test<br>Testing<br/>Testingest<br />"
        self.assertEqual("Test\nTesting\nTestingest\n", linux_linebreaks(test))

    def test_mac_linebreaks(self):
        """\r should be converted to \n"""
        test = "Test\rString\r"
        self.assertEqual("Test\nString\n", linux_linebreaks(test))

    def test_mixed_mac_and_windows_linebreaks(self):
        """\r should be converted to \n, but \r\n should not result in \n\n"""
        test = "Test\rString\r\nHere\rAnd\n\nThere\n"
        self.assertEqual("Test\nString\nHere\nAnd\n\nThere\n", linux_linebreaks(test))

    def test_paragraph_linebreaks(self):
        """Just to be sure paragraph breaks (= 2 x Enter) are correct"""
        test = "Test\rString\r\n\r\nHere\n"
        self.assertEqual("Test\nString\n\nHere\n", linux_linebreaks(test))
