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

class ProcessReportersIntegrationTest(com.TestCaseVerbose):
	'''
	There is no documented specification regarding the url.jsont and file.jsont templates.
	These tests were implemented with the assumption that the current input/output pairs were correct.
	#TODO This is a bad assumption. There was nothing else which could be used as a base for writing the tests.
	'''
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Starter.initCouchDB()
		com.Configuration.setServices(["object-feeder","reporter"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Starter.waitCouchDB()
		com.Configuration.deleteCouchDB(database="hsn")
		com.Starter.initStart("hsn2-reporter")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testUrlOkay(self):
		'''
		Checks if the two set attributes retain their respective values in their reported form.
		The type attribute after reporting always has the valuea "url".
		'''
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/process-reporters-url.hwl")
		jobId = com.Console.submitJob("process-reporters-url feed.uri=/tmp/tests/resources/json/process-reporters-url-okay.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEquals(objDict.get("classification"), "benign")
		self.assertEquals(objDict.get("type"), "url")
		self.assertEquals(objDict.get("url_original"), "http://localhost")

	def testUrlNoClassification(self):
		'''
		Checks if not providing a classification causes it to be set to "unknown".
		The type attribute after reporting always has the valuea "url".
		'''
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/process-reporters-url.hwl")
		jobId = com.Console.submitJob("process-reporters-url feed.uri=/tmp/tests/resources/json/process-reporters-url-no-classification.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEquals(objDict.get("classification"), "unknown")
		self.assertEquals(objDict.get("type"), "url")
		self.assertEquals(objDict.get("url_original"), "http://localhost")

	def testUrlNoType(self):
		'''
		The type attribute after reporting always has the valuea "url". Not providing it shouldn't impact this.
		'''
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/process-reporters-url.hwl")
		jobId = com.Console.submitJob("process-reporters-url feed.uri=/tmp/tests/resources/json/process-reporters-url-no-type.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEquals(objDict.get("classification"), "benign")
		self.assertEquals(objDict.get("type"), "url") # this will remain type as it's hard coded in the template.
		self.assertEquals(objDict.get("url_original"), "http://localhost")

	def testUrlNoUrlOriginal(self):
		'''
		Checks if not providing the url_original attribute causes it to not be set.
		'''
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/process-reporters-url.hwl")
		jobId = com.Console.submitJob("process-reporters-url feed.uri=/tmp/tests/resources/json/process-reporters-url-no-urloriginal.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEquals(objDict.get("classification"), "benign")
		self.assertEquals(objDict.get("type"), "url")
		self.assertEquals(objDict.get("url_original"), None)

	def testFileOkay(self):
		'''
		Checks if the parent attribute is properly passed onto the reported form.
		'''
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/process-reporters-file.hwl")
		jobId = com.Console.submitJob("process-reporters-file feed.uri=/tmp/tests/resources/json/process-reporters-file-okay.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEquals(objDict.get("parent"), 1)

	def testFileNoParent(self):
		'''
		Checks if not providing the parent attribute causes it to not be set.
		'''
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/process-reporters-file.hwl")
		jobId = com.Console.submitJob("process-reporters-file feed.uri=/tmp/tests/resources/json/process-reporters-file-no-parent.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		self.assertEquals(objDict.get("parent"), None)
