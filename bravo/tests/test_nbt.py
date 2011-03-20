from gzip import GzipFile
from StringIO import StringIO
import tempfile
import unittest

from bravo.nbt import NBTFile, MalformedFileError
from bravo.nbt import TAG_Compound

bigtest = """
H4sIAAAAAAAAAO1Uz08aQRR+wgLLloKxxBBjzKu1hKXbzUIRibGIFiyaDRrYqDGGuCvDgi67Znew
8dRLe2x66z/TI39Dz732v6DDL3tpz73wMsn35r1v5ntvJnkCBFRyTywOeMuxTY149ONwYj4Iex3H
pZMYD4JH3e6EAmK1oqrHeHZcV8uoVQ8byNYeapWGhg2tflh7j4PPg0+Db88DEG5bjj6+pThMZP0Q
6tp0piNA3GYuaeG107tz+nYLKdsL4O/oPR44W+8RCFb13l3fC0DgXrf6ZLcEAIxBTHPGCFVM0yAu
faTAyMIQs7reWAtTo+5EjkUDMLEnU4xM8ekUo1OMheHZn+Oz8kSBpXwz3di7x6p1E18oHAjXLtFZ
P68dG2AhWd/68QX+wc78nb0AvPFAyfiFQkBG/p7r6g+TOmiHYLvrMjejKAqOu/XQaWPKTtvp7Obm
Kzu9Jb5kSQk9qruU/Rh+6NIO2m8VTLFoPivhm5yEmbyEBQllWRZFAP8vKK4v8sKypC4dIHdaO7mM
yucp31FByRa1xW2hKq0sxTF/unqSjl6dX/gSBSMb0fa3d6rNlXK8nt9YXUuXrpIXuUTQgMj6Pr+z
3FTLB3Vuo7Z2WZKTqdxRUJlrzDXmGv9XIwhCy+kb1njC7P78evt9eNOE39TypPsIBgAA
""".decode("base64")

class BugfixTest(unittest.TestCase):
    """
    Bugfix regression tests.

    These tend to not fit into nice categories.
    """

    def test_empty_file(self):
        """
        Opening an empty file causes an exception.

        https://github.com/twoolie/NBT/issues/issue/4
        """

        temp = tempfile.NamedTemporaryFile()
        temp.flush()
        self.assertRaises(MalformedFileError, NBTFile, temp.name)

class ReadWriteTest(unittest.TestCase):

    def setUp(self):
        self.f = tempfile.NamedTemporaryFile()
        self.f.write(bigtest)
        self.f.flush()

    def test_trivial(self):
        pass

    def testReadBig(self):
        mynbt = NBTFile(self.f.name)
        self.assertTrue(mynbt.filename != None)
        self.assertEqual(len(mynbt.tags), 11)

    def testWriteBig(self):
        mynbt = NBTFile(self.f.name)
        output = StringIO()
        mynbt.write_file(buffer=output)
        self.assertTrue(GzipFile(self.f.name).read() == output.getvalue())

    def testWriteback(self):
        mynbt = NBTFile(self.f.name)
        mynbt.write_file()

class TreeManipulationTest(unittest.TestCase):

    def setUp(self):
        self.nbtfile = NBTFile()

    def testRootNodeSetup(self):
        self.nbtfile.name = "Hello World"
        self.assertEqual(self.nbtfile.name, "Hello World")

class EmptyStringTest(unittest.TestCase):

    def setUp(self):
        self.golden_value = "\x0A\0\x04Test\x08\0\x0Cempty string\0\0\0"
        self.nbtfile = NBTFile(buffer=StringIO(self.golden_value))

    def testReadEmptyString(self):
        self.assertEqual(self.nbtfile.name, "Test")
        self.assertEqual(self.nbtfile["empty string"].value, "")

    def testWriteEmptyString(self):
        buffer = StringIO()
        self.nbtfile.write_file(buffer=buffer)
        self.assertEqual(buffer.getvalue(), self.golden_value)

class TestTAGCompound(unittest.TestCase):

    def setUp(self):
        self.tag = TAG_Compound()

    def test_trivial(self):
        pass

    def test_contains(self):
        self.tag["test"] = TAG_Compound()
        self.assertTrue("test" in self.tag)

if __name__ == '__main__':
    unittest.main()
