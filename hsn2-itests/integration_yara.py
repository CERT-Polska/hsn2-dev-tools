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
Created on 2012-07-13

@author: pawelch
'''

import commons as com
import hsn2_commons.hsn2objectwrapper as ow
import logging

class YaraIntegrationTest(com.TestCaseVerbose):
	testHelp = None

	def assertRuleMatches(self, matches, rule, namespace):
		match = [match for match in matches if match['rule'] == '%s' % rule]
		self.assertTrue(len(match) == 1, "There should be one yara match based on rule %s" % rule)

		self.assertEqual(match[0]['namespace'], '%s' % namespace)

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		#com.Starter.initCouchDB()
		com.Configuration.setServices(["yara","reporter","object-feeder"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store-mongodb")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Starter.initStart("hsn2-yara")
		#com.Starter.waitCouchDB()
		#com.Configuration.deleteCouchDB(database="hsn")
		#com.Starter.initStart("hsn2-reporter")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/yara.hwl")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testFailed(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/yara-1.hwl")
		jobId = com.Console.submitJob("yara-1 feed.uri=/tmp/tests/resources/json/yara-simple.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertFalse(finished, "Job should fail.")

		details = com.JobDetails(jobId)
		self.assertTrue(details["job_status"] in ("FAILED", "ABORTED"))
		self.assertEqual(details["job_error_message"], "Both rules_filename and rules_string are missing. One of them is required.", name1="job_error_message")

	def testCompletedWithMatches(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/yara-1.hwl")
		jobId = com.Console.submitJob("yara-1 feed.uri=/tmp/tests/resources/json/yara-simple.json yara1.rules_filename=/tmp/tests/resources/yara/rules1.yar")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		details = com.JobDetails(jobId)
		self.assertEqual(details["job_status"], "COMPLETED", name1="job_status")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("yara_time_start"))
		self.assertTrue(ret[1].isSet("yara_time_stop"))
		self.assertTrue(ret[1].yara_time_stop - ret[1].yara_time_start >= 0)
		self.assertTrue(ret[1].isSet("yara_matches_found"))
		self.assertTrue(ret[1].isSet("yara_matches_list"))
		self.assertTrue(ret[1].yara_matches_found)

		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].yara_matches_list.key) , method="GET")
		matches = ow.fromYaraMatchesList(contHandle)
		self.assertTrue(len(matches) == 2, "There should be two yara matches for test-file.txt")

		self.assertRuleMatches(matches, 'TextExample', 'default')
		self.assertRuleMatches(matches, 'AnotherTextExample', 'default')

	def testCompletedNoMatches(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/yara-1.hwl")
		jobId = com.Console.submitJob("yara-1 feed.uri=/tmp/tests/resources/json/yara-simple.json yara1.rules_filename=/tmp/tests/resources/yara/rules2.yar")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		details = com.JobDetails(jobId)
		self.assertEqual(details["job_status"], "COMPLETED", name1="job_status")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("yara_time_start"))
		self.assertTrue(ret[1].isSet("yara_time_stop"))
		self.assertTrue(ret[1].yara_time_stop - ret[1].yara_time_start >= 0)
		self.assertTrue(ret[1].isSet("yara_matches_found"))
		self.assertFalse(ret[1].isSet("yara_matches_list"))
		self.assertFalse(ret[1].yara_matches_found)

	def testPackersExe(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/yara-1.hwl")
		jobId = com.Console.submitJob("yara-1 feed.uri=/tmp/tests/resources/json/yara-exe.json yara1.rules_filename=/tmp/tests/resources/yara/packers.yar")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		details = com.JobDetails(jobId)
		self.assertEqual(details["job_status"], "COMPLETED", name1="job_status")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("yara_time_start"))
		self.assertTrue(ret[1].isSet("yara_time_stop"))
		self.assertTrue(ret[1].yara_time_stop - ret[1].yara_time_start > 0, "Expected yara running for more than 0 milliseconds.")
		self.assertTrue(ret[1].isSet("yara_matches_found"))
		self.assertFalse(ret[1].isSet("yara_matches_list"))
		self.assertFalse(ret[1].yara_matches_found)

	def testPackersUpx(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/yara-1.hwl")
		jobId = com.Console.submitJob("yara-1 feed.uri=/tmp/tests/resources/json/yara-upx.json yara1.rules_filename=/tmp/tests/resources/yara/packers.yar")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		details = com.JobDetails(jobId)
		self.assertEqual(details["job_status"], "COMPLETED", name1="job_status")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("yara_time_start"))
		self.assertTrue(ret[1].isSet("yara_time_stop"))
		self.assertTrue(ret[1].yara_time_stop - ret[1].yara_time_start > 0, "Expected yara running for more than 0 milliseconds.")
		self.assertTrue(ret[1].isSet("yara_matches_found"))
		self.assertTrue(ret[1].isSet("yara_matches_list"))
		self.assertTrue(ret[1].yara_matches_found)

		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].yara_matches_list.key) , method="GET")
		matches = ow.fromYaraMatchesList(contHandle)
		self.assertTrue(len(matches) == 1, "There should be one yara match for calc.upx")

		self.assertRuleMatches(matches, 'UPX', 'default')

	def testPcap(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/yara-1.hwl")
		jobId = com.Console.submitJob("yara-1 feed.uri=/tmp/tests/resources/json/yara-pcap.json yara1.rules_filename=/tmp/tests/resources/yara/http.yar")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		details = com.JobDetails(jobId)
		self.assertEqual(details["job_status"], "COMPLETED", name1="job_status")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("yara_time_start"))
		self.assertTrue(ret[1].isSet("yara_time_stop"))
		self.assertTrue(ret[1].yara_time_stop - ret[1].yara_time_start > 0, "Expected yara running for more than 0 milliseconds.")
		self.assertTrue(ret[1].isSet("yara_matches_found"))
		self.assertTrue(ret[1].isSet("yara_matches_list"))
		self.assertTrue(ret[1].yara_matches_found)

		contHandle = com.getUrlHandle("http://localhost:8080/data/%s/%d" % (jobId, ret[1].yara_matches_list.key) , method="GET")
		matches = ow.fromYaraMatchesList(contHandle)
		self.assertTrue(len(matches) == 4, "There should be four yara matches for dump.pcap")

		self.assertRuleMatches(matches, 'response_200', 'default')
		self.assertRuleMatches(matches, 'GET', 'default')
		self.assertRuleMatches(matches, 'POST', 'default')
		self.assertRuleMatches(matches, 'PUT', 'default')

	def runTest(self):
		pass
