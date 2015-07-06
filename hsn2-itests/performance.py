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
Created on 2012-06-15

@author: pawelch
'''

import commons as com
import logging
import couchdb
import uuid
import unittest
import time

class PerformanceTest(com.TestCaseVerbose):
	'''
	Test if nosetests are enough for performance plugin.
	'''
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName = self.__class__.__name__, testName = self._testMethodName, loglevel = logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Configuration.resetJobCounter()
		com.Starter.initCouchDB()
		com.Configuration.setServices(["feeder-list", "webclient", "swf-cve", "shell-scdbg", "js-sta", "reporter", "norm-url"])
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store-mongodb")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-file-feeder")
		com.Starter.initStart("hsn2-webclient")
		com.Starter.initStart("hsn2-js-sta")
		com.Starter.initStart("hsn2-norm-url")
		com.Starter.initStart("hsn2-swf-cve")
		com.Starter.initStart("hsn2-shell-scdbg")
		# TODO: remove this workaround after com.Starter.initCouchDB(wait=True) is fixed
		time.sleep(5)
		try:
			couchdb.Server().delete('hsn')
		except:
			pass
		com.Starter.initStart("hsn2-reporter")
		com.Configuration.setConsoleConf(host = "127.0.0.1", port = 5672, timeout = 4)

	def testPerformanceSimple(self):
		'''
		Jobs executed sequentially, workflow: simple.hwl
		'''
		passed = True
		jlog = com.JmeterLog()
		totalLabel = "Total Time for %s" % self._testMethodName
		totalUid = uuid.uuid4()
		jlog.start(totalLabel, totalUid)
		com.Configuration.setWorkflow("/tmp/tests/workflows/simple/simple.hwl")
		label = self._testMethodName
		for i in range(10):
			uid = uuid.uuid4()
			jlog.start(label, uid)
			jobId = com.Console.submitJob("simple feeder1.url=http://js.honeysploit.hsn/dangerous2.html")
			if jobId is not None:
				finished = com.Console.waitForCompletion(jobId, 30, 2, True)
			else:
				finished = False

			if finished is False:
				passed = False

			jlog.stop(label, uid)
			jlog.success(label, uid, bool(finished))
			jlog.addsample(label, uid)
		jlog.stop(totalLabel, totalUid)
		jlog.success(totalLabel, totalUid, True)
		jlog.addsample(totalLabel, totalUid)
		com.Configuration.setConf("/tmp/tests/out/%s.jml" % label, jlog.toxml())
		self.assertTrue(passed, "Seems like one or more jobs failed to submit/complete")

	def testPerformanceCrawlShallow(self):
		'''
		Jobs executed sequentially, workflow: crawl-shallow
		'''
		passed = True
		com.Configuration.setWorkflow("/tmp/tests/workflows/performance/crawl-shallow.hwl")
		jlog = com.JmeterLog()
		totalLabel = "Total Time for %s" % self._testMethodName
		totalUid = uuid.uuid4()
		jlog.start(totalLabel, totalUid)
		label = self._testMethodName
		for i in range(10):
			uid = uuid.uuid4()
			jlog.start(label, uid)
			jobId = com.Console.submitJob("crawl-shallow feeder.url=http://js.honeysploit.hsn/dangerous2.html")
			if jobId is not None:
				finished = com.Console.waitForCompletion(jobId, 30, 2, True)
			else:
				finished = False

			if finished is False:
				passed = False

			jlog.stop(label, uid)
			jlog.success(label, uid, bool(finished))
			jlog.addsample(label, uid)
		jlog.stop(totalLabel, totalUid)
		jlog.success(totalLabel, totalUid, True)
		jlog.addsample(totalLabel, totalUid)
		com.Configuration.setConf("/tmp/tests/out/%s.jml" % label, jlog.toxml())
		self.assertTrue(passed, "Seems like one or more jobs failed to submit/complete")

	def allJobsFinished(self):
		# TODO: once reasonable time-frames are established it might be a good idea to add a timeout to this function and it's calls.
		processing = True
		output = None
		while processing:
			time.sleep(3)
			output = com.Console.call("hc j l")
			processing = "PROCESSING" in output[1]
		logging.info(output)

	def performanceMultiThreadSimple(self, num = 10):
		'''
		Jobs submitted sequentially, workflow: simple.hwl.
		Execution control dependent on framework.
		'''
		passed = True
		com.Configuration.setWorkflow("/tmp/tests/workflows/simple/simple.hwl")
		jlog = com.JmeterLog()
		totalLabel = "Total Time for %s" % self._testMethodName
		totalUid = uuid.uuid4()
		jlog.start(totalLabel, totalUid)
		uidList = dict()
		label = self._testMethodName
		for i in range(num):
			uid = i #uuid.uuid4()
			jlog.start(label, uid)
			jobId = com.Console.submitJob("simple feeder1.url=http://js.honeysploit.hsn/dangerous2.html")
			uidList[uid] = jobId
		self.allJobsFinished()
		jlog.stop(totalLabel, totalUid)
		jlog.success(totalLabel, totalUid, True)
		jlog.addsample(totalLabel, totalUid)
		for item in uidList.iteritems():
			uid = item[0]
			jobId = item[1]
			if jobId is not None:
				details = com.JobDetails(jobId)
				duration = int(details.get("job_processing_time_sec")) * 1000
				finished = "COMPLETED" in details.get("job_status")
			else:
				finished = False
				duration = 0

			if finished is False:
				passed = False

			jlog.stop(label, uid, duration)
			jlog.success(label, uid, bool(finished))
			jlog.addsample(label, uid)
		com.Configuration.setConf("/tmp/tests/out/%s.jml" % label, jlog.toxml())
		self.assertTrue(passed, "Seems like one or more jobs failed to submit/complete")

	def performanceMultiThreadCrawlShallow(self, num = 10):
		'''
		Jobs submitted sequentially, workflow: crawl-shallow.hwl.
		Execution control dependent on framework.
		'''
		passed = True
		com.Configuration.setWorkflow("/tmp/tests/workflows/performance/crawl-shallow.hwl")
		jlog = com.JmeterLog()
		totalLabel = "Total Time for %s" % self._testMethodName
		totalUid = uuid.uuid4()
		jlog.start(totalLabel, totalUid)
		uidList = dict()
		label = self._testMethodName
		for i in range(num):
			uid = i #uuid.uuid4()
			jlog.start(label, uid)
			jobId = com.Console.submitJob("crawl-shallow feeder.url=http://js.honeysploit.hsn/dangerous2.html")
			uidList[uid] = jobId
		self.allJobsFinished()
		jlog.stop(totalLabel, totalUid)
		jlog.success(totalLabel, totalUid, True)
		jlog.addsample(totalLabel, totalUid)
		for item in uidList.iteritems():
			uid = item[0]
			jobId = item[1]
			if jobId is not None:
				details = com.JobDetails(jobId)
				duration = int(details.get("job_processing_time_sec")) * 1000
				finished = "COMPLETED" in details.get("job_status")
			else:
				finished = False
				duration = 0

			if finished is False:
				passed = False

			jlog.stop(label, uid, duration)
			jlog.success(label, uid, bool(finished))
			jlog.addsample(label, uid)
		com.Configuration.setConf("/tmp/tests/out/%s.jml" % label, jlog.toxml())
		self.assertTrue(passed, "Seems like one or more jobs failed to submit/complete")

	def testPerformanceMultiThreadSimple10(self):
		self.performanceMultiThreadSimple(10)

	def testPerformanceMultiThreadSimple100(self):
		self.performanceMultiThreadSimple(100)

	def testPerformanceMultiThreadSimple1000(self):
		self.performanceMultiThreadSimple(1000)

	def testPerformanceMultiThreadSimple2000(self):
		self.performanceMultiThreadSimple(2000)

	def testPerformanceMultiThreadCrawlShallow10(self):
		self.performanceMultiThreadCrawlShallow(10)

	def testPerformanceMultiThreadCrawlShallow100(self):
		self.performanceMultiThreadCrawlShallow(100)

	def testPerformanceMultiThreadCrawlShallow1000(self):
		self.performanceMultiThreadCrawlShallow(1000)

	def testPerformanceMultiThreadCrawlShallow2000(self):
		self.performanceMultiThreadCrawlShallow(2000)
