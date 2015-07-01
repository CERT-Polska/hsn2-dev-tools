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
import re

class JobsIncorrectIntegrationTest(unittest.TestCase):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Configuration.resetJobCounter()
		com.Starter.initRabbitMQ()
		com.Starter.initStart("hsn2-framework")

		time.sleep(2)
		com.Configuration.setWorkflowsFolder("/tmp/tests/workflows/incorrect")

	def testJobRejected(self):
		ret = com.Console.call("hc j s XXX")
		logging.info(ret[1])
		self.assertIn("The job has been rejected. The reason is 'Error running workflow XXX'.", ret[1], "The job should be rejected.")

	def testJobAcceptedAborted(self):
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-file-feeder")

		ret = com.Console.call("hc j s incorrect")
		logging.info(ret[1])
		self.assertIn("The job has been accepted.", ret[1], "The job should be accepted.")
		jobId = re.search(r'\(Id=(\d+)\)', ret[1])
		self.assertNotEqual(jobId, None, "Couldn't get job ID.")
		jobId = jobId.group(1)
		logging.info("The job ID is %s" % jobId)

		time.sleep(2)
		ret = com.Console.call("hc j l")
		logging.info(ret[1])
		self.assertRegexpMatches(ret[1], r'id:\s+%s\s+status:\s+ABORTED' % jobId, "The job should be aborted.")

	def testJobWithParamsAcceptedAborted(self):
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-file-feeder")

		ret = com.Console.call("hc j s incorrect --param service1.key=value -p service2.key2=value2")
		logging.info(ret[1])
		self.assertIn("The job has been accepted.", ret[1], "The job should be accepted.")
		jobId = re.search(r'\(Id=(\d+)\)', ret[1])
		self.assertNotEqual(jobId, None, "Couldn't get job ID.")
		jobId = jobId.group(1)
		logging.info("The job ID is %s" % jobId)

		time.sleep(2)
		ret = com.Console.call("hc j l")
		logging.info(ret[1])
		self.assertRegexpMatches(ret[1], r'id:\s+%s\s+status:\s+ABORTED' % jobId, "The job should be aborted.")
