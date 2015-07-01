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

class ComponentStartupCorrectIntegrationTest(unittest.TestCase):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName = self.__class__.__name__, testName = self._testMethodName, loglevel = logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()

	def _testHelper(self, service):
		com.Starter.initStart("hsn2-framework")
		time.sleep(2)
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		time.sleep(2)
		com.Starter.initStart("hsn2-%s" % service)
		time.sleep(2)
		ret = ''.join(com.Configuration.getConf("/var/log/hsn2/%s.log" % service))
		logging.info(ret)
		return ret

	def testStartingFrameworkCorrect(self):
		com.Starter.initStart("hsn2-framework")
		ret = ''.join(com.Configuration.getConf("/var/log/hsn2/framework.log"))
		logging.info(ret)
		self.assertIn("pl.nask.hsn2.framework.bus.RbtFrameworkBus - Starting consumer endpoints for the bus...", ret, "Expected bus thread started.")

	def testStartingObjectStoreCorrect(self):
		ret = self._testHelper("object-store")
		self.assertIn("ObjectStoreConnector - Object store started.", ret, "Expected object store started.")

	def testStartingDataStoreCorrect(self):
		ret = self._testHelper("data-store")
		self.assertIn("pl.nask.hsn2.DataStoreServer - Server is listening on port", ret, "Expected data store started.")

	def testStartingFileFeederCorrect(self):
		ret = self._testHelper("file-feeder")
		self.assertIn("pl.nask.hsn2.TaskProcessor - Waiting for TaskRequest", ret, "Expected file-feeder started.")

	def testStartingSwfCveCorrect(self):
		ret = self._testHelper("swf-cve")
		self.assertIn("pl.nask.hsn2.GenericServiceInfo - Jar location: /opt/hsn2/swf-cve", ret, "Expected swf-cve started.")

	def testStartingShellScdbgCorrect(self):
		ret = self._testHelper("shell-scdbg")
		self.assertIn("pl.nask.hsn2.TaskProcessor - Waiting for TaskRequest", ret, "Expected shell-scdbg started.")

	def testStartingReporterCorrect(self):
		com.Starter.initCouchDB()
		ret = self._testHelper("reporter")
		self.assertIn("org.lightcouch.CouchDbClientBase - >> HEAD /hsn/ HTTP/1.1", ret, "Expected reporter started and connected with CouchDB.")

	# TODO: re-enable when vm and test scenarios are ready
	@unittest.skip("Test disabled until resources required for Capture HPC are available.")
	def testStartingCaptureHPCCorrect(self):
		ret = self._testHelper("capture-hpc")
		self.assertIn("CommandLineParams - Command line option: con. Value from command line: 127.0.0.1, default value=localhost", ret, "Expected localhost passed as command line option.")
		# TODO: add any required asserts
