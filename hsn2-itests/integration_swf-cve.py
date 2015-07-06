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

class SwfCveIntegrationTest(com.TestCaseVerbose):
	'''
	general info: https://drotest4.nask.net.pl:3000/issues/6420
	details: https://drotest4.nask.net.pl:3000/issues/5374
	'''
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Configuration.setServices(["object-feeder","feeder-list", "webclient", "js-sta", "shell-scdbg", "swf-cve", "reporter"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store-mongodb")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Starter.initStart("hsn2-swf-cve")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/swf-cve-1.hwl")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testSwfCveBenign(self):
		jobId = com.Console.submitJob("swf-cve-1 feed.uri=/tmp/tests/resources/json/swf-cve-benign.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertSet(ret[1], "swf_cve_time_begin")
		self.assertSet(ret[1], "swf_cve_time_end")
		self.assertSet(ret[1], "swf_cve_detected")
		self.assertNotSet(ret[1], "swf_cve_list")
		self.assertEqual(ret[1].swf_cve_detected, 0, "Expected 0 CVE detected, got %s." % ret[1].swf_cve_detected)

	def testSwfCveMalicious(self):
		jobId = com.Console.submitJob("swf-cve-1 feed.uri=/tmp/tests/resources/json/swf-cve-malicious.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertSet(ret[1], "swf_cve_time_begin")
		self.assertSet(ret[1], "swf_cve_time_end")
		self.assertSet(ret[1], "swf_cve_detected")
		self.assertSet(ret[1], "swf_cve_list")
		self.assertEqual(ret[1].swf_cve_detected, 1, "Expected 1 CVE detected, got %s." % ret[1].swf_cve_detected)

		handle = com.getUrlHandle('http://localhost:8080/data/%s/%s' % (jobId, ret[1].swf_cve_list.getKey()), method='GET')
		html = ''.join(handle.readlines())
		self.assertIn('CVE_2007_0071', html, "Expected CVE_2007_0071 detected, but in data-store there was only:\n%s" % (html))

	def runTest(self):
		pass

if __name__ == "__main__":
	import signal
	a = SwfCveIntegrationTest()
	try:
		a.setUp()
		a.testSwfCveBenign()
		#signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
	try:
		a.setUp()
		a.testSwfCveMalicious()
		#signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
