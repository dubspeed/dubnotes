import unittest
from test_dubnotes import *
from test_authenticator import *
from test_database import *
from test_action import *
import fake_dropbox

suites = []
suites.append(unittest.TestLoader().loadTestsFromTestCase(DubnotesOnlineTests))
suites.append(unittest.TestLoader().loadTestsFromTestCase(DubnotesOfflineTests))
suites.append(unittest.TestLoader().loadTestsFromTestCase(DubnotesPostTests))
suites.append(unittest.TestLoader().loadTestsFromTestCase(fake_dropbox.client.ClientTests))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestSessionFactory))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestRedirectedSession))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestAuthenticatedSession))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestDatabase))
suites.append(unittest.TestLoader().loadTestsFromTestCase(TestActions))

suite = unittest.TestSuite(suites)
unittest.TextTestRunner(verbosity=1).run(suite)