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
import unittest
import logging

class VirusTotalIntegrationTest(com.TestCaseVerbose):
	testHelp = None
	apiKey = "0b568f4c9d12704c460866112fc546dff282c42c6136a343d6a698dc701cce3a"

	def setApiKey(self, apiKey):
		com.Console.call(r'''sed -i s/API_KEY=\".*\"\;/API_KEY=\"%s\"\;/ /etc/hsn2/razorback/virustotal.conf''' % apiKey)

	def setUp(self):
		com.Backup.backupFile("/etc/hsn2/razorback/virustotal.conf")
		self.setApiKey(self.apiKey)
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Starter.initCouchDB()
		com.Configuration.setServices(["object-feeder","rb-virustotal","reporter"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Starter.initStart("hsn2-rb-virustotal")
		com.Starter.waitCouchDB()
		com.Configuration.deleteCouchDB(database="hsn")
		com.Starter.initStart("hsn2-reporter")
		com.Configuration.setWorkflow("/tmp/tests/workflows/nuggets/rb-virustotal1.hwl")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testBenign(self):
		'''
		Test how the nugget reacts to a benign file.

		Expected behaviour:
		- set rb_virustotal_return_value to 0
		- set rb_virustotal_classification to "benign"
		'''
		# Left clamavNugget test resources here on purpose. No need to split hairs in this case.
		jobId = com.Console.submitJob("rb-virustotal1 feed.uri=/tmp/tests/resources/json/rb-clamavnugget-benign.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_virustotal_classification"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_virustotal_return_value"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_virustotal_return_value, 0)
		self.assertEqual(ret[1].rb_virustotal_classification, "benign")
		self.assertFalse(ret[1].isSet("rb_virustotal_verdict_message"), "Unexpected attribute was set.")
		self.assertFalse(ret[1].isSet("rb_virustotal_verdict_priority"), "Unexpected attribute was set.")
		self.assertFalse(ret[1].isSet("rb_virustotal_report"), "Unexpected attribute was set.")
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-virustotal", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEqual(objDict.get("classification"), "benign")
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertTrue(len(objDict) == 1)
		self.assertIn({u'value': 0, u'name': u'return value', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")

	def testMalicious(self):
		'''
		Test how the nugget reacts to a malicious file.

		Expected behaviour:
		- set rb_virustotal_return_value to 0
		- set rb_virustotal_classification to "malicious"
		- set rb_virustotal_verdict_message to "VirusTotal reported block bad"
		- set rb_virustotal_verdict_priority to 1
		- set rb_virustotal_report. Not checking exact message as it is long and may be subject to change.
		'''
		# Left clamavNugget test resources here on purpose. No need to split hairs in this case.
		jobId = com.Console.submitJob("rb-virustotal1 feed.uri=/tmp/tests/resources/json/rb-clamavnugget-malicious.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_virustotal_classification"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_virustotal_return_value"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_virustotal_return_value, 0)
		self.assertEqual(ret[1].rb_virustotal_classification, "malicious")
		self.assertTrue(ret[1].isSet("rb_virustotal_verdict_message"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_virustotal_verdict_priority"), "Expected attribute wasn't set.")
		self.assertTrue(ret[1].isSet("rb_virustotal_report"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_virustotal_verdict_message, "VirusTotal reported block bad")
		self.assertEqual(ret[1].rb_virustotal_verdict_priority, 1)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-virustotal", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEqual(objDict.get("classification"), "malicious")
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertIsNotNone(objDict, "Details in object don't have the value attribute.")
		self.assertTrue(len(objDict) == 4)
		self.assertIn({u'value': 0, u'name': u'return value', u'structure': u'text'}, objDict,
					"Wrong return value (different than 0).")
		self.assertIn({u'value': u'VirusTotal reported block bad', u'name': u'message', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")
		self.assertIn({u'value': 1, u'name': u'priority', u'structure': u'text'}, objDict,
					"Didn't find structure priority in the details attribute.")

	def testBadKey(self):
		'''
		Test how the nugget reacts to a bad api key.

		Expected behaviour:
		- set rb_virustotal_return_value to 2
		'''
		# Left clamavNugget test resources here on purpose. No need to split hairs in this case.
		com.Starter.initStop("hsn2-rb-virustotal")
		self.setApiKey("BADKEY")
		com.Starter.initStart("hsn2-rb-virustotal",autoStop=False)
		jobId = com.Console.submitJob("rb-virustotal1 feed.uri=/tmp/tests/resources/json/rb-clamavnugget-benign.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_virustotal_return_value"), "Expected attribute wasn't set.")
		self.assertFalse(ret[1].isSet("rb_virustotal_classification"), "Unexpected attribute was set.")
		self.assertEqual(ret[1].rb_virustotal_return_value, 2)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-virustotal", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEqual(objDict.get("classification"), None)
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertTrue(len(objDict) == 1)
		self.assertIn({u'value': 2, u'name': u'return value', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")

	def runTest(self):
		pass

if __name__ == "__main__":
	import signal
	a = VirusTotalIntegrationTest()
#	try:
#		a.setUp()
#		a.testBenign()
#		signal.pause()
#	except KeyboardInterrupt:
#		pass
#	finally:
#		a.doCleanups()
#	try:
#		a.setUp()
#		a.testMalicious()
#		signal.pause()
#	except KeyboardInterrupt:
#		pass
#	finally:
#		a.doCleanups()
	try:
		a.setUp()
		a.testBadKey()
		signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
