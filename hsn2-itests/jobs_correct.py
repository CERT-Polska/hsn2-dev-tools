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
Created on 2012-05-18

@author: pawelch
'''

import commons as com
import unittest
import logging

class JobsCorrectIntegrationTest(unittest.TestCase):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Configuration.resetJobCounter()
		com.Starter.initRabbitMQ()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store-mongodb")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-file-feeder")
		com.Starter.initStart("hsn2-webclient")
		com.Starter.initStart("hsn2-js-sta")
		com.Starter.initStart("hsn2-swf-cve")
		com.Configuration.setWorkflowsFolder("/tmp/tests/workflows/correct")
		com.Configuration.setConf("/file.txt", "http://www.nask.pl/")
		com.Configuration.setConf("/tmp/tests/file.txt", "http://www.nask.pl/")

	def _testHelper(self, jobParams=""):
		ret = com.Console.call("hc j s correct %s" % jobParams)
		logging.info(ret[1])
		self.assertIn("The job has been accepted.", ret[1], "The job should be accepted.")

		jobId = com.Console.jobIdRegexp.search(ret[1]).group(1)
		self.assertNotEqual(jobId, None, "Couldn't get job ID.")
		logging.info("The job ID is %s" % jobId)

		ret = com.Console.call("hc j d %s" % jobId)
		logging.info(ret[1])
		self.assertNotIn("couldn't execute activity", ret[1], "Expected no failed activities.")

		completed = com.Console.waitForCompletion(jobId=jobId, maxTime=300, period=5, verbose=True)
		ret = com.Console.call("hc j d %s" % jobId)
		logging.info(ret[1])
		self.assertTrue(completed, "Job failed to finish successfully.")

	def testJobAccepted(self):
		self._testHelper()

	def testJobWithParamsAccepted(self):
		self._testHelper(jobParams=" --param service1.key=value -p feeder1.uri=/tmp/tests/file.txt")
