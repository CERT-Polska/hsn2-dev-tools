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

class WebclientIntegrationTest(com.TestCaseVerbose):
	'''
	general info: https://drotest4.nask.net.pl:3000/issues/6418
	details: https://drotest4.nask.net.pl:3000/issues/5375
	'''
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Configuration.setServices(["object-feeder","feeder-list", "webclient", "js-sta", "shell-scdbg", "swf-cve", "reporter"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Starter.initStart("hsn2-webclient")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/webclient.hwl")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testWebclient(self):
		jobId = com.Console.submitJob("webclient feed.uri=/tmp/tests/resources/json/webclient-benign.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertSet(ret[1], "creation_time")
		self.assertSet(ret[1], "top_ancestor")
		self.assertSet(ret[1], "html")
		self.assertSet(ret[1], "depth")
		self.assertSet(ret[1], "http_code")
		self.assertSet(ret[1], "http_request")
		self.assertSet(ret[1], "active")
		self.assertSet(ret[1], "type")
		self.assertSet(ret[1], "url_original")

		self.assertEqual(ret[1].url_original, "http://www.google.com/", name1="url_original")

	def runTest(self):
		import signal
		try:
			self.setUp()
			self.testWebclient()
			#signal.pause()
		except KeyboardInterrupt:
			pass
		finally:
			self.doCleanups()

if __name__ == "__main__":
	a = WebclientIntegrationTest()
	a.runTest()
