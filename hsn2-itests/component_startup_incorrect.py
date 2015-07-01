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
Created on 2012-05-17

@author: pawelch
'''

import commons as com
import unittest
import logging
import time

class ComponentStartupIncorrectIntegrationTest(unittest.TestCase):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName = self.__class__.__name__, testName = self._testMethodName, loglevel = logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initStop("rabbitmq-server")

	def _testHelper(self, service, checkFailed = True):
		failed = False
		try:
			com.Starter.initStart("hsn2-%s" % service)
		except com.InitException:
			failed = True
		time.sleep(2)
		ret = ''.join(com.Configuration.getConf("/var/log/hsn2/%s.log" % service))
		logging.info(ret)
		if checkFailed:
			self.assertTrue(failed, "Expected %s failed to start, it appears it started." % service)
		return ret

	def testStartingFrameworkIncorrect(self):
		ret = self._testHelper("framework")
		self.assertIn("pl.nask.hsn2.framework.core.Main - Framework cannot attach to the bus. Is Rabbit MQ working?", ret, "Expected connection refused.")

	def testStartingObjectStoreIncorrect(self):
		ret = self._testHelper("object-store")
		self.assertNotIn("ObjectStoreConnector - Object store started.", ret, "Expected object store not started.")

	@unittest.skip("Test disabled until conditions when data store should fail are defined.")
	def testStartingDataStoreIncorrect(self):
		#ret = self._testHelper("data-store")
		# TODO: simulate situation when data-store should fail and add appropriate asserts
		pass

	def testStartingFileFeederIncorrect(self):
		ret = self._testHelper("file-feeder")
		self.assertNotIn("pl.nask.hsn2.TaskProcessor - Waiting for TaskRequest", ret, "Expected file-feeder not started.")

	@unittest.skip("Test disabled until conditions when swf-cve should fail are defined.")
	def testStartingSwfCveIncorrect(self):
		#ret = self._testHelper("swf-cve")
		# TODO: simulate situation when swf-cve should fail and add appropriate asserts
		pass

	def testStartingShellScdbgIncorrect(self):
		ret = self._testHelper("shell-scdbg")
		self.assertNotIn("pl.nask.hsn2.TaskProcessor - Waiting for TaskRequest", ret, "Expected shell-scdbg not started.")

	def testStartingReporterIncorrect(self):
		com.Starter.initCouchDB()
		ret = self._testHelper("reporter", False)
		self.assertIn("pl.nask.hsn2.service.ReporterService - Error in connection with ObjectStore", ret, "Expected error when connecting with object store.")

	def testStartingReporterIncorrectNoCouchDB(self):
		ret = self._testHelper("reporter")
		self.assertNotIn("org.lightcouch.CouchDbClientBase - >> HEAD /hsn/ HTTP/1.1", ret, "Expected reporter not connected to CouchDB.")
		self.assertIn("pl.nask.hsn2.service.ReporterService - Cannot connect do CouchDB server:", ret, "Expected connection to CouchDB refused.")

	# TODO: re-enable when vm and test scenarios are ready
	@unittest.skip("Test disabled until resources required for Capture HPC are available.")
	def testStartingCaptureHPCIncorrect(self):
		#ret = self._testHelper("capture-hpc")
		# TODO: add any required asserts
		pass
