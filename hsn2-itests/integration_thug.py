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
Created on 01-06-2012

@author: wojciechm
'''

import commons as com
import hsn2_commons.hsn2objectwrapper as ow
import logging

class ThugIntegrationTest(com.TestCaseVerbose):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Starter.initCouchDB()
		com.Configuration.setServices(["thug","reporter","feeder-list"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-file-feeder")
		com.Starter.initStart("hsn2-thug")
		com.Starter.waitCouchDB()
		com.Configuration.deleteCouchDB(database="hsn")
		com.Starter.initStart("hsn2-reporter")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/thug.hwl")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testUrlNASK(self):
		jobId = com.Console.submitJob("thug feed.url=http://www.nask.pl")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].isSet("thug_active"), True)
		self.assertEquals(ret[1].thug_active, True)
		self.assertEqual(ret[1].isSet("thug_behaviors"), True)
		behHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].thug_behaviors.key) , method="GET")
		bList = ow.fromBehaviorList(behHandle)
		self.assertTrue(len(bList) > 0, "Behavior shouldn't be zero.")
		self.assertEqual(ret[1].isSet("js_context_list"), True)
		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].js_context_list.key) , method="GET")
		cList = ow.fromJSContextList(contHandle)
		self.assertTrue(len(cList) > 0, "Contexts should have been reported")
		self.assertEqual(ret[1].isSet("thug_time_start"), True)
		self.assertEqual(ret[1].isSet("thug_time_stop"), True)
		self.assertTrue(ret[1].thug_time_stop - ret[1].thug_time_start > 0, "Thug should have run was some time")

	def testUrlCERT(self):
		jobId = com.Console.submitJob("thug feed.url=http://www.cert.pl")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].isSet("thug_active"), True)
		self.assertEquals(ret[1].thug_active, True)
		self.assertEqual(ret[1].isSet("thug_behaviors"), True)
		behHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].thug_behaviors.key) , method="GET")
		bList = ow.fromBehaviorList(behHandle)
		self.assertTrue(len(bList) > 0, "Behavior shouldn't be zero.")
		self.assertEqual(ret[1].isSet("js_context_list"), True)
		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].js_context_list.key) , method="GET")
		cList = ow.fromJSContextList(contHandle)
		self.assertTrue(len(cList) > 0, "Contexts should have been reported")
		self.assertEqual(ret[1].isSet("thug_time_start"), True)
		self.assertEqual(ret[1].isSet("thug_time_stop"), True)
		self.assertTrue(ret[1].thug_time_stop - ret[1].thug_time_start > 0, "Thug should have run was some time")


	def testUrlDanger1(self):
		jobId = com.Console.submitJob("thug feed.url=http://js.honeysploit.hsn/dangerous.html")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].isSet("thug_active"), True)
		self.assertEquals(ret[1].thug_active, True)
		self.assertEqual(ret[1].isSet("thug_behaviors"), True)
		behHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].thug_behaviors.key) , method="GET")
		bList = ow.fromBehaviorList(behHandle)
		self.assertTrue(len(bList) > 0, "Behavior shouldn't be zero.")
		self.assertEqual(ret[1].isSet("js_context_list"), True)
		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].js_context_list.key) , method="GET")
		cList = ow.fromJSContextList(contHandle)
		self.assertTrue(len(cList) > 0, "Contexts should have been reported")
		self.assertEqual(ret[1].isSet("thug_time_start"), True)
		self.assertEqual(ret[1].isSet("thug_time_stop"), True)
		self.assertTrue(ret[1].thug_time_stop - ret[1].thug_time_start > 0, "Thug should have run was some time")

	def testUrlDanger2(self):
		jobId = com.Console.submitJob("thug feed.url=http://js.honeysploit.hsn/dangerous_3atonce.html")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].isSet("thug_active"), True)
		self.assertEquals(ret[1].thug_active, True)
		self.assertEqual(ret[1].isSet("thug_behaviors"), True)
		behHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].thug_behaviors.key) , method="GET")
		bList = ow.fromBehaviorList(behHandle)
		self.assertTrue(len(bList) > 0, "Behavior shouldn't be zero.")
		self.assertEqual(ret[1].isSet("js_context_list"), True)
		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].js_context_list.key) , method="GET")
		cList = ow.fromJSContextList(contHandle)
		self.assertTrue(len(cList) > 0, "Contexts should have been reported")
		self.assertEqual(ret[1].isSet("thug_time_start"), True)
		self.assertEqual(ret[1].isSet("thug_time_stop"), True)
		self.assertTrue(ret[1].thug_time_stop - ret[1].thug_time_start > 0, "Thug should have run was some time")

	def testUrlDanger3(self):
		jobId = com.Console.submitJob("thug feed.url=http://js.honeysploit.hsn/dangerous2.html")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].isSet("thug_active"), True)
		self.assertEquals(ret[1].thug_active, True)
		self.assertEqual(ret[1].isSet("thug_behaviors"), True)
		behHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].thug_behaviors.key) , method="GET")
		bList = ow.fromBehaviorList(behHandle)
		self.assertTrue(len(bList) > 0, "Behavior shouldn't be zero.")
		self.assertEqual(ret[1].isSet("js_context_list"), True)
		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].js_context_list.key) , method="GET")
		cList = ow.fromJSContextList(contHandle)
		self.assertTrue(len(cList) > 0, "Contexts should have been reported")
		self.assertEqual(ret[1].isSet("thug_time_start"), True)
		self.assertEqual(ret[1].isSet("thug_time_stop"), True)
		self.assertTrue(ret[1].thug_time_stop - ret[1].thug_time_start > 0, "Thug should have run was some time")

	def testUrlDanger4(self):
		jobId = com.Console.submitJob("thug feed.url=http://js.honeysploit.hsn/filtertests.html")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 120, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].isSet("thug_active"), True)
		self.assertEquals(ret[1].thug_active, True)
		self.assertEqual(ret[1].isSet("thug_behaviors"), True)
		behHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].thug_behaviors.key) , method="GET")
		bList = ow.fromBehaviorList(behHandle)
		self.assertTrue(len(bList) > 0, "Behavior shouldn't be zero.")
		self.assertEqual(ret[1].isSet("js_context_list"), True)
		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].js_context_list.key) , method="GET")
		cList = ow.fromJSContextList(contHandle)
		self.assertTrue(len(cList) > 0, "Contexts should have been reported")
		self.assertEqual(ret[1].isSet("thug_time_start"), True)
		self.assertEqual(ret[1].isSet("thug_time_stop"), True)
		self.assertTrue(ret[1].thug_time_stop - ret[1].thug_time_start > 0, "Thug should have run was some time")

	def runTest(self):
		pass

if __name__ == "__main__":
	import signal
	a = ThugIntegrationTest()
	try:
		a.setUp()
		a.testUrlNASK()
		signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
