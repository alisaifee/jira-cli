"""

"""
import types
import unittest

if not hasattr(unittest.TestCase, "assertIsNotNone"):
    def assertIsNotNone(self, value, message=""):
        self.assertNotEqual(value, None, message)

    unittest.TestCase.assertIsNotNone = types.MethodType(assertIsNotNone, None, unittest.TestCase)


