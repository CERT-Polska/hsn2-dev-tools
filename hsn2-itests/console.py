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

class ConsoleIntegrationTest(unittest.TestCase):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Configuration.resetJobCounter()
		com.Configuration.setServices(["object-feeder","webclient","reporter"])
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store-mongodb")
		com.Configuration.setWorkflow("/tmp/tests/workflows/minimal/stub.hwl")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testPing(self):
		ret = com.Console.call("hc p")
		logging.info(ret[1])
		self.assertIn("The framework is alive", ret[1], "Framework failed to report alive before timeout.")

	def testJobSubmit(self):
		result = com.Console.submitJob("stub")
		self.assertIsNotNone(result, "Didn't receive job accepted notification.")
		return result

	def testJobList(self):
		jobId = self.testJobSubmit()
		ret = com.Console.call("hc j l")
		logging.info(ret[1])
		self.assertRegexpMatches(ret[1], r"id:\s+%s\s+status:" % jobId, "Haven't found job in the job list. Got '%s'" % ret[1])

	def testJobDetails(self):
		jobId = self.testJobSubmit()
		ret = com.Console.call("hc j d %s" % jobId)
		logging.info(ret[1])
		self.assertRegexpMatches(ret[1], r"Details\s+about\s+the\s+job:", "Didn't receive job details. Got '%s'" % ret[1])

	def testWorkflowList(self):
		ret = com.Console.call("hc w l")
		logging.info(ret[1])
		self.assertRegexpMatches(ret[1], "Found \d+ workflow\(s\):", "Framework should report at least 1 workflow.");
		self.assertIn("stub", ret[1], "Expected workflow not found. Got '%s'" % ret[1])

	@unittest.skip("Not implemented in Console")
	def testWorkflowGet(self):
		pass

	def testWorkflowUpload(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/minimal/stub.hwl", "testWorkflowUpload")
		ret = com.Console.call("hc w l")
		self.assertIn("testWorkflowUpload", ret[1], "Expected workflow not found. Got '%s'" % ret[1])

	@unittest.skip("Not implemented in Console")
	def testWorkflowDisable(self):
		pass

	@unittest.skip("Not implemented in Console")
	def testWorkflowEnable(self):
		pass

	@unittest.skip("Not implemented in Console")
	def testWorkflowHistory(self):
		pass

	@unittest.skip("Not implemented in Console")
	def testWorkflowStatus(self):
		pass

	@unittest.skip("Not implemented in Console")
	def testConfigSet(self):
		pass

	def testConfigGet(self):
		ret = com.Console.call("hc c g")
		logging.info(ret[1])
		self.assertIn("workflow.repository	/etc/hsn2/workflows/", ret[1], "Expected workflow repository set to /etc/hsn2/workflows/.")
		self.assertIn("AMQP.services	object-feeder webclient reporter", ret[1], "Expected AMQP.services set to: object-feeder webclient reporter.")
