"""

"""
import types
import unittest
import sys

if not hasattr(unittest.TestCase, "assertIsNotNone"):
    def assertIsNotNone(self, value, message=""):
        self.assertNotEqual(value, None, message)

    unittest.TestCase.assertIsNotNone = types.MethodType(assertIsNotNone, None, unittest.TestCase)


def skip_if_3(fn):
        return unittest.skipIf(sys.version_info > (3,0,0), "tests skipped for py3k")(fn)
