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
Created on 2012-05-22

@author: pawelch
'''

import commons as com
import logging
import couchdb

class ServiceReportersIntegrationTest(com.TestCaseVerbose):
	'''
	general info: https://drotest4.nask.net.pl:3000/issues/6420
	details: https://drotest4.nask.net.pl:3000/issues/5375
	'''
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Configuration.setServices(["object-feeder","feeder-list", "webclient", "js-sta", "shell-scdbg", "swf-cve", "reporter"])
		com.Configuration.resetJobCounter()
		com.Starter.initCouchDB()
		# TODO: remove this workaround after com.Starter.initCouchDB(wait=True) is fixed
		import time
		time.sleep(5)
		couchdb.Server().delete('hsn')
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store-mongodb")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)
		com.Starter.initStart("hsn2-reporter")

	def testReportingJsSta(self):
		com.Starter.initStart("hsn2-js-sta")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/service-reporters-js-sta.hwl")
		jobId = com.Console.submitJob("reporter-js-sta feed.uri=/tmp/tests/resources/json/js-sta-malicious.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		couch = couchdb.Server()["hsn"]
		self.assertTrue(str(jobId) + ":2:js-sta" in couch, "Expected 1:2:js-sta saved in couch. It seems it was missing.")

	def testReportingSwfCve(self):
		com.Starter.initStart("hsn2-swf-cve")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/service-reporters-swf-cve.hwl")
		jobId = com.Console.submitJob("reporter-swf-cve feed.uri=/tmp/tests/resources/json/swf-cve-malicious.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		couch = couchdb.Server()["hsn"]
		self.assertTrue(str(jobId) + ":2:swf-cve" in couch, "Expected 1:2:swf-cve saved in couch. It seems it was missing.")

	def testReportingShellScdbg(self):
		com.Starter.initStart("hsn2-shell-scdbg")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/service-reporters-shell-scdbg.hwl")
		jobId = com.Console.submitJob("reporter-shell-scdbg feed.uri=/tmp/tests/resources/json/shell-scdbg-malicious.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 20, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")

		couch = couchdb.Server()["hsn"]
		self.assertTrue(str(jobId) + ":2:shell-scdbg" in couch, "Expected 1:2:shell-scdbg saved in couch. It seems it was missing.")

	def testReportingWebclient(self):
		com.Starter.initStart("hsn2-webclient")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/service-reporters-webclient.hwl")
		jobId = com.Console.submitJob("reporter-webclient feed.uri=/tmp/tests/resources/json/webclient-benign.json")
		finished = com.Console.waitForCompletion(jobId, 15, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		couch = couchdb.Server()["hsn"]
		self.assertTrue(str(jobId) + ":2:webclient" in couch, "Expected 1:2:webclient saved in couch. It seems it was missing.")
