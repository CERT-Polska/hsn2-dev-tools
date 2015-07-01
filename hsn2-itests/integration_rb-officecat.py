#!/usr/bin/python -tt

# Copyright (c) NASK, NCSC
# 
# This file is part of HoneySpider Network 2.0.
# 
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on 04-05-2012

@author: wojciechm
'''

import commons as com
import logging

class OfficeCatIntegrationTest(com.TestCaseVerbose):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Starter.initCouchDB()
		com.Configuration.setServices(["object-feeder","rb-officecat","reporter"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Starter.initStart("hsn2-rb-officecat")
		com.Starter.waitCouchDB()
		com.Configuration.deleteCouchDB(database="hsn")
		com.Starter.initStart("hsn2-reporter")
		com.Configuration.setWorkflow("/tmp/tests/workflows/nuggets/rb-officecat1.hwl")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testBenign(self):
		'''
		Test how the nugget reacts to a benign file.
		Expected behaviour:
		- set rb_officecat_return_value to 0
		- set rb_officecat_classification to "benign"
		'''
		jobId = com.Console.submitJob("rb-officecat1 feed.uri=/tmp/tests/resources/json/rb-officecat-benign.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_officecat_classification"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_officecat_return_value"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_officecat_return_value, 0)
		self.assertEqual(ret[1].rb_officecat_classification, "benign")
		self.assertFalse(ret[1].isSet("rb_officecat_verdict_message"), "Unexpected attribute was set.")
		self.assertFalse(ret[1].isSet("rb_officecat_verdict_priority"), "Unexpected attribute was set.")
		self.assertFalse(ret[1].isSet("rb_officecat_cve"), "Unexpected attribute was set.")
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-officecat", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEqual(objDict.get("classification"), "benign")
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertIsNotNone(objDict, "Details in object don't have the value attribute.")
		self.assertTrue(len(objDict) == 1)
		self.assertIn({u'value': u'0', u'name': u'return value', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")

	def testMalicious(self):
		'''
		Test how the nugget reacts to a malicious file.
		Expected behaviour:
		- set rb_officecat_return_value to 0
		- set rb_officecat_classification to "malicious"
		- set rb_officecat_verdict_message to "THE FOLLOWING HAS BEEN FOUND BY OFFICECAT: CVE-2008-4841"
		- set rb_officecat_verdict_priority to 1
		- set rb_officecat_cve to "CVE-2008-4841"
		'''
		jobId = com.Console.submitJob("rb-officecat1 feed.uri=/tmp/tests/resources/json/rb-officecat-malicious.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_officecat_classification"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_officecat_return_value"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_officecat_return_value, 0)
		self.assertEqual(ret[1].rb_officecat_classification, "malicious")
		self.assertTrue(ret[1].isSet("rb_officecat_verdict_message"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_officecat_verdict_priority"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_officecat_cve"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_officecat_verdict_message, "THE FOLLOWING HAS BEEN FOUND BY OFFICECAT: CVE-2008-4841")
		self.assertEqual(ret[1].rb_officecat_verdict_priority, 1)
		self.assertEqual(ret[1].rb_officecat_cve, "CVE-2008-4841")
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-officecat", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEqual(objDict.get("classification"), "malicious")
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertIsNotNone(objDict, "Details in object don't have the value attribute.")
		self.assertTrue(len(objDict) == 4)
		self.assertIn({u'value': u'0', u'name': u'return value', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")
		self.assertIn({u'value': u'THE FOLLOWING HAS BEEN FOUND BY OFFICECAT: CVE-2008-4841', u'name': u'message', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")
		self.assertIn({u'value': u'1', u'name': u'priority', u'structure': u'text'}, objDict,
					"Didn't find structure priority in the details attribute.")
		self.assertIn({u'value': u'CVE-2008-4841', u'name': u'cve', u'structure': u'text'}, objDict,
					"Didn't find structure cve in the details attribute.")

	def testUnsupportedFile(self):
		'''
		Test results of processing a file that the nugget doesn't handle.
		The nugget provides no explicit information about the file being not supported. Output is similar to that of a benign file.
		Expected behaviour:
		- set rb_officecat_return_value to 0
		- set rb_officecat_classification to "benign"
		'''
		jobId = com.Console.submitJob("rb-officecat1 feed.uri=/tmp/tests/resources/json/rb-officecat-unsupportedfile.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_officecat_classification"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_officecat_return_value"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_officecat_return_value, 0)
		self.assertEqual(ret[1].rb_officecat_classification, "benign")
		self.assertFalse(ret[1].isSet("rb_officecat_verdict_message"), "Unexpected attribute was set.")
		self.assertFalse(ret[1].isSet("rb_officecat_verdict_priority"), "Unexpected attribute was set.")
		self.assertFalse(ret[1].isSet("rb_officecat_cve"), "Unexpected attribute was set.")
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-officecat", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEqual(objDict.get("classification"), "benign")
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertIsNotNone(objDict, "Details in object don't have the value attribute.")
		self.assertTrue(len(objDict) == 1)
		self.assertIn({u'value': u'0', u'name': u'return value', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")

	def runTest(self):
		pass

if __name__ == "__main__":
	import signal
	a = OfficeCatIntegrationTest()
	try:
		a.setUp()
		a.testBenign()
		signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
	try:
		a.setUp()
		a.testMalicious()
		signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
	try:
		a.setUp()
		a.testUnsupportedFile()
		signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
