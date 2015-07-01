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
import sys
sys.path.append("/opt/hsn2/python/commlib")
import logging
import unittest

class CuckooIntegrationTest(com.TestCaseVerbose):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName = self.__class__.__name__, testName = self._testMethodName, loglevel = logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Starter.initCouchDB()
		com.Configuration.setServices(["cuckoo", "reporter", "feeder-list"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-file-feeder")
		com.Starter.initStart("hsn2-cuckoo")
		com.Starter.initStart("cuckoo-mock")
		com.Starter.waitCouchDB()
		com.Configuration.deleteCouchDB(database = "hsn")
		com.Starter.initStart("hsn2-reporter")
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/cuckoo.hwl")
		com.Configuration.setConsoleConf(host = "127.0.0.1", port = 5672, timeout = 4)

	def testWithClassification(self):
		jobId = com.Console.submitJob("cuckoo feed.url=http://www.nask.pl cuckoo1.custom=/tmp/tests/resources/logs/cuckoo/213.tar.gz")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg = self.testHelp.agg)
		self.assertEqual(ret[1].isSet("cuckoo_time_start"), True)
		self.assertEqual(ret[1].isSet("cuckoo_time_stop"), True)
		self.assertTrue(ret[1].cuckoo_time_stop - ret[1].cuckoo_time_start > 0, "Cuckoo should have run was some time")
		self.assertEqual(ret[1].isSet("cuckoo_screenshots"), True)
		self.assertEqual(ret[1].isSet("cuckoo_report_json"), True)
		self.assertEqual(ret[1].isSet("cuckoo_report_html"), False)
		self.assertEqual(ret[1].isSet("cuckoo_pcap"), False)
		self.assertEqual(ret[1].isSet("cuckoo_classification"), True)
		self.assertEqual(ret[1].isSet("cuckoo_classification_reason"), True)

	def testWithoutClassification(self):
		jobId = com.Console.submitJob("cuckoo feed.url=http://www.nask.pl cuckoo1.custom=/tmp/tests/resources/logs/cuckoo/210.tar.gz")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg = self.testHelp.agg)
		self.assertEqual(ret[1].isSet("cuckoo_time_start"), True)
		self.assertEqual(ret[1].isSet("cuckoo_time_stop"), True)
		self.assertTrue(ret[1].cuckoo_time_stop - ret[1].cuckoo_time_start > 0, "Cuckoo should have run was some time")
		self.assertEqual(ret[1].isSet("cuckoo_screenshots"), True)
		self.assertEqual(ret[1].isSet("cuckoo_report_json"), True)
		self.assertEqual(ret[1].isSet("cuckoo_report_html"), False)
		self.assertEqual(ret[1].isSet("cuckoo_pcap"), False)
		self.assertEqual(ret[1].isSet("cuckoo_classification"), False)
		self.assertEqual(ret[1].isSet("cuckoo_classification_reason"), False)

	def testDifferentParamters(self):
		jobId = com.Console.submitJob("cuckoo feed.url=http://www.nask.pl cuckoo1.custom=/tmp/tests/resources/logs/cuckoo/210.tar.gz \
			cuckoo1.timeout=10 cuckoo1.priority=1 cuckoo1.package=ie cuckoo1.save_pcap=True cuckoo1.save_report_json=False \
			cuckoo1.save_report_html=True cuckoo1.save_screenshots=False\
		")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg = self.testHelp.agg)
		self.assertEqual(ret[1].isSet("cuckoo_time_start"), True)
		self.assertEqual(ret[1].isSet("cuckoo_time_stop"), True)
		self.assertTrue(ret[1].cuckoo_time_stop - ret[1].cuckoo_time_start > 0, "Cuckoo should have run was some time")
		self.assertEqual(ret[1].isSet("cuckoo_screenshots"), False)
		self.assertEqual(ret[1].isSet("cuckoo_report_json"), False)
		self.assertEqual(ret[1].isSet("cuckoo_report_html"), True)
		self.assertEqual(ret[1].isSet("cuckoo_pcap"), True)

	def testFailed(self):
		'''
			Job should fail as no log archive is defined via cuckoo1.custom.
		'''
		jobId = com.Console.submitJob("cuckoo feed.url=http://www.nask.pl")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertFalse(finished, "Job passed. Should have failed.")
		ret = com.Console.getDumpAsObjects(jobId, agg = self.testHelp.agg)
		self.assertEqual(ret[1].isSet("cuckoo_time_start"), False)
		self.assertEqual(ret[1].isSet("cuckoo_time_stop"), False)
		self.assertEqual(ret[1].isSet("cuckoo_screenshots"), False)
		self.assertEqual(ret[1].isSet("cuckoo_report_json"), False)
		self.assertEqual(ret[1].isSet("cuckoo_report_html"), False)
		self.assertEqual(ret[1].isSet("cuckoo_pcap"), False)

	def testTimeout(self):
		jobId = com.Console.submitJob("cuckoo feed.url=http://www.nask.pl \
			cuckoo1.custom=sleep\
		")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertFalse(finished, "Job passed. Should have failed.")
		ret = com.Console.getDumpAsObjects(jobId, agg = self.testHelp.agg)
		self.assertEqual(ret[1].isSet("cuckoo_time_start"), False)
		self.assertEqual(ret[1].isSet("cuckoo_time_stop"), False)
		self.assertEqual(ret[1].isSet("cuckoo_screenshots"), False)
		self.assertEqual(ret[1].isSet("cuckoo_report_json"), False)
		self.assertEqual(ret[1].isSet("cuckoo_report_html"), False)
		self.assertEqual(ret[1].isSet("cuckoo_pcap"), False)

	def testTimeoutNoReports(self):
		jobId = com.Console.submitJob("cuckoo feed.url=http://www.nask.pl \
			cuckoo1.custom=/tmp/tests/resources/logs/cuckoo/noreports.tar.gz \
		")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertFalse(finished, "Job passed. Should have failed.")
		ret = com.Console.getDumpAsObjects(jobId, agg = self.testHelp.agg)
		self.assertEqual(ret[1].isSet("cuckoo_time_start"), False)
		self.assertEqual(ret[1].isSet("cuckoo_time_stop"), False)
		self.assertEqual(ret[1].isSet("cuckoo_screenshots"), False)
		self.assertEqual(ret[1].isSet("cuckoo_report_json"), False)
		self.assertEqual(ret[1].isSet("cuckoo_report_html"), False)
		self.assertEqual(ret[1].isSet("cuckoo_pcap"), False)

	def runTest(self):
		pass
