import unittest
import sys, os
sys.path.append("..")
os.environ['DUBNOTES_DEBUG'] = "true"
import database
from helper import *

class TestDatabase(unittest.TestCase):
    def setUp(self):
        pass
 