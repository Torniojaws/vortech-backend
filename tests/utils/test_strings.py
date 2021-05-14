import unittest

from apps.utils.strings import int_or_none, linux_linebreaks


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

    def test_int_or_none_with_valid_values(self):
        """Should return the value back as an int type value."""
        self.assertEqual(True, isinstance(int_or_none(2), int))
        self.assertEqual(3, int_or_none(3))
        self.assertEqual(4, int_or_none("4"))
        self.assertEqual(0, int_or_none("0"))

    def test_int_or_none_with_invalid_possible_values(self):
        """Should return None when value is possible but not an int."""
        self.assertEqual(None, int_or_none("a2"))
        self.assertEqual(None, int_or_none(""))
        self.assertEqual(None, int_or_none("aaabbb"))
        self.assertEqual(None, int_or_none("😀"))

    def test_int_or_none_with_invalid_nonsense_values(self):
        """Should return None for 'impossible' values."""
        self.assertEqual(None, int_or_none(['lists', 'cannot', 'be', 'used', 'in', 'urlparams']))
        self.assertEqual(None, int_or_none({"dict": "is also not possible in urlparams"}))
        self.assertEqual(None, int_or_none(None))
