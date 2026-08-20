import unittest
from exercise17_string_utils import reverse_string, capitalize_string, is_capitalized

class TestStringUtils(unittest.TestCase):
    def test_reverse_string(self):
        self.assertEqual(reverse_string('watch'), 'hctaw')
    
    def test_capitalize(self):
        self.assertEqual(capitalize_string('watch'), 'Watch')

    def test_is_capitalized(self):
        self.assertEqual(is_capitalized('Watch'), True)

if __name__ == '__main__':
    unittest.main()