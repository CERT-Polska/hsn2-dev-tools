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
import time
import unittest

class NuggetServiceIntegrationTest(com.TestCaseVerbose):
	'''
	Set of tests for the Python Nugget Service.
	Most of these tests can also be directly treated as tests for the more general Python Service Template.
	'''
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName = self.__class__.__name__, testName = self._testMethodName, loglevel = logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initStop("rabbitmq-server")
		com.Starter.initStop("hsn2-framework")
		com.Starter.initStop("hsn2-object-store")
		com.Starter.initStop("hsn2-data-store")
		com.Starter.initStop("hsn2-object-feeder")
		com.Starter.initStop("hsn2-rb-swfscanner")
		com.Configuration.setServices(["object-feeder", "rb-swfscanner", "rb-pdffox", "rb-clamavnugget",
				"rb-officecat", "rb-archiveinflate", "rb-virustotal", "reporter", "webclient", "feeder-list", "mime-recognizer"])

	def testStartOkay(self):
		'''
		Test startup of nugget service when everything is running.
		Expected:
		- service starts up and runs.
		- service runs for 5 seconds
		- service stops
		- no error messages were logged
		'''
		com.Starter.initRabbitMQ()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-rb-swfscanner", autoStop = False)
		logging.info("Waiting 5 seconds"); time.sleep(5)
		com.Starter.initStop("hsn2-rb-swfscanner")
		ret = ''.join(com.Configuration.getConf("/var/log/hsn2/rb-swfscanner.log"))
		self.assertIn("Connection opened", ret)
		self.assertIn("Service rb-swfscanner stopped", ret)

	def testStartNoBinary(self):
		'''
		Test startup of nugget service when specified binary file is missing.
		Expected:
		- service doesn't startup (return value 255)
		'''
		ret = com.Console.call("/opt/hsn2/python/nugget-commons/nuggetService.py --nugget=/tmp/nonexistent", stderr = True)
		self.assertEqual(ret[0], 255)
		self.assertIn("isn't executable or does not exist", ret[2])
		self.assertIn("Service not starting", ret[2])

	def testStartNoRabbit(self):
		'''
		Test startup of nugget service when RabbitMQ isn't running.
		Expected:
		- service starts up (return value 0)
		- service shuts down after children cannot connect to RabbitMQ
		'''
		ret = com.Console.call("/opt/hsn2/python/nugget-commons/nuggetService.py --nugget=/opt/hsn2/rb-swfscanner/rb-swfscanner", stderr = True)
		self.assertIn("Can't connect to RabbitMQ", ret[2])
		self.assertIn("All children exited", ret[2])

	def testStartNoQueue(self):
		'''
		Test startup of nugget service when RabbitMQ is running, but the service queue doesn't exist.
		Expected:
		- service starts up (return value 0)
		- service shuts down after children cannot connect to their queue.
		'''
		com.Starter.initRabbitMQ()
		ret = com.Console.call("/opt/hsn2/python/nugget-commons/nuggetService.py --nugget=/opt/hsn2/rb-swfscanner/rb-swfscanner", stderr = True)
		self.assertIn("ERROR (404, \"NOT_FOUND - no queue", ret[2])
		self.assertIn("All children exited", ret[2])

	def testFailRabbit(self):
		'''
		Test for nugget service when RabbitMQ shuts down while the service is running.
		Expected:
		- service starts up (return value 0)
		- service shuts down after children recannot connect to their queue.
		'''
		com.Starter.initRabbitMQ(autoStop = False)
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-rb-swfscanner", autoStop = False)
		com.Starter.initStop("rabbitmq-server", None)
		self.assertFalse(com.Starter.isRunning("rabbitmq-server"), "RabbitMQ was found to still be running.")
		i = 0
		while i < 10 and com.Starter.isRunning("hsn2-rb-swfscanner"):
			i = i + 1
			time.sleep(1)
		self.assertFalse(com.Starter.isRunning("hsn2-rb-swfscanner"))
		ret = ''.join(com.Configuration.getConf("/var/log/hsn2/rb-swfscanner.log"))
		#logging.info(ret)
		self.assertIn("ERROR BlockingConnection", ret)
		self.assertIn("ERROR All children exited", ret)
		self.assertIn("INFO Service rb-swfscanner stopped", ret)

	def testShutdownWhileProcessing(self):
		'''
		Test for nugget service when the service shuts down while processing a task.
		Expected:
		- service starts up (return value 0)
		- service processors send TaskError with DEFUNCT.
		- service stops
		'''
		com.Starter.initRabbitMQ()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")

		# Four tasks per each TaskProcessor - should take long enough to break in processing.
		com.Configuration.setWorkflow("/tmp/tests/workflows/nuggets/rb-swfscanner1.hwl")
		for i in range(40):
			com.Console.submitJob("rb-swfscanner1 feed.uri=/tmp/tests/resources/json/rb-swfscanner-benign.json")

		com.Starter.initStart("hsn2-rb-swfscanner", autoStop = False)
		#time.sleep(1)
		com.Starter.initStop("hsn2-rb-swfscanner")
		ret = ''.join(com.Configuration.getConf("/var/log/hsn2/rb-swfscanner.log"))
		#logging.info(ret)
		self.assertIn("Connection opened", ret)
		self.assertIn("Service rb-swfscanner stopped", ret)
		self.assertIn("WARNING DEFUNCT Processor termination", ret)
		self.assertNotIn("ERROR", ret)

	def testFailDataStore(self):
		'''
		Test for nugget service when the data store shuts down while the service is running.
		Expected:
		- service starts up (return value 0)
		- service processors send TaskError with DATA_STORE when they cannot access their object's content.
		'''
		com.Starter.initRabbitMQ()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store", autoStop = False)
		com.Starter.initStart("hsn2-object-feeder")
		com.Configuration.setWorkflow("/tmp/tests/workflows/nuggets/rb-swfscanner1.hwl")
		com.Console.submitJob("rb-swfscanner1 feed.uri=/tmp/tests/resources/json/rb-swfscanner-benign.json")
		time.sleep(1)
		com.Starter.initStop("hsn2-data-store")
		time.sleep(1)
		com.Starter.initStart("hsn2-rb-swfscanner")
		time.sleep(3)
		ret = ''.join(com.Configuration.getConf("/var/log/hsn2/rb-swfscanner.log"))
		#logging.info(ret)
		self.assertIn("Connection opened", ret)
		self.assertIn("WARNING DATA_STORE [Errno 111] Connection refused", ret)
		self.assertNotIn("ERROR", ret)

	def testFailObjectStore(self):
		'''
		Test for nugget service when the object store shuts down while the service is running.
		Expected:
		- service starts up (return value 0)
		- service processors send TaskError with OBJ_STORE when they cannot access their object.
		'''
		com.Starter.initRabbitMQ()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store", autoStop = False)
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Configuration.setWorkflow("/tmp/tests/workflows/nuggets/rb-swfscanner1.hwl")
		com.Console.submitJob("rb-swfscanner1 feed.uri=/tmp/tests/resources/json/rb-swfscanner-benign.json")
		time.sleep(1)
		com.Starter.initStop("hsn2-object-store")
		time.sleep(1)
		com.Starter.initStart("hsn2-rb-swfscanner")
		logging.info("Waiting for object connector timeouts."); time.sleep(18)
		ret = ''.join(com.Configuration.getConf("/var/log/hsn2/rb-swfscanner.log"))
		#logging.info(ret)
		self.assertIn("Connection opened", ret)
		self.assertIn("WARNING OBJ_STORE Object store not responding", ret)
		self.assertNotIn("ERROR", ret)

	def runTest(self):
		pass

if __name__ == "__main__":
	import signal
	a = NuggetServiceIntegrationTest()
	try:
		a.setUp()
		a.testFailObjectStore()
		#signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
