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
Created on 2012-06-13

@author: pawelch
'''

import commons as com
import logging
import os
import shutil
import time

class CaptureHPCIntegrationTest(com.TestCaseVerbose):
	'''
	general info: https://drotest4.nask.net.pl:3000/issues/6420
	details: https://drotest4.nask.net.pl:3000/issues/6417
	'''
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		#com.Starter.initRabbitMQ()
		#com.Configuration.setServices(["object-feeder","feeder-list", "webclient", "js-sta", "shell-scdbg", "swf-cve", "reporter"])
		#com.Configuration.resetJobCounter()
		#com.Starter.initStart("hsn2-framework")
		#com.Starter.initStart("hsn2-object-store")
		#com.Starter.initStart("hsn2-data-store")
		#com.Starter.initStart("hsn2-object-feeder")
		#com.Starter.initStart("hsn2-capture-hpc")
		if not os.path.exists("/etc/init.d/hsn2-capture-hpc-mock"):
			shutil.copyfile('/tmp/tests/lib/hsn2-capture-hpc-mock.initd', "/etc/init.d/hsn2-capture-hpc-mock")
			shutil.copymode('/tmp/tests/lib/hsn2-capture-hpc-mock.initd', "/etc/init.d/hsn2-capture-hpc-mock")
		com.CaptureHPC.clearLogs()
		com.Starter.initStart("hsn2-capture-hpc-mock")
		#com.Configuration.setWorkflow("/tmp/tests/workflows/integration/capture-hpc-1.hwl")
		#com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def _testHelperSending(self, url, jobid):
		com.CaptureHPC.add(url, jobid)
		self.assertTrue(com.CaptureHPC.checkStatus("QUEUED", jobid, url, 10),
									"Status QUEUED not added to log in expected time: should be less than %d seconds" % 10)
		self.assertTrue(com.CaptureHPC.checkStatus("SENDING", jobid, url),
									"Status SENDING not added to log in expected time: should be less than %d seconds" % 90)
		self.assertTrue(com.CaptureHPC.checkStatus("VISITING", jobid, url, 10),
									"Status VISITING not added to log in expected time: should be less than %d seconds" % 10)

	def _testHelperVisited(self, url, jobid):
		self.assertTrue(com.CaptureHPC.checkStatus("VISITED", jobid, url),
									"Status VISITED not added to log in expected time: should be less than %d seconds" % 90)

	def _testHelperBenign(self, url, jobid):
		self.assertTrue(com.CaptureHPC.checkStatus("BENIGN", jobid, url, 10),
									"Status BENIGN not added to log in expected time: should be less than %d seconds" % 10)

	def testCaptureBenign(self):
		jobid = "1"
		url = "http://detektywzlublina.pl/"
		self._testHelperSending(url, jobid)
		self._testHelperVisited(url, jobid)
		self._testHelperBenign(url, jobid)
		self.assertFalse(com.CaptureHPC.checkFileAdded(jobid, "log"), "Expected log file added in /tmp/hpc/changes")
		self.assertFalse(com.CaptureHPC.checkFileAdded(jobid, "zip"), "Expected zip file added in /tmp/hpc/changes")

	def testCaptureMalicious(self):
		jobid = "2"
		url = "http://www.qermi.pl/uslugi/serwis-ogrodowy-jac-pal_id987.xhtml"
		self._testHelperSending(url, jobid)
		self._testHelperVisited(url, jobid)
		self.assertTrue(com.CaptureHPC.checkStatus("MALICIOUS", jobid, url, 10),
									"Status MALICIOUS not added to log in expected time: should be less than %d seconds" % 10)
		self.assertTrue(com.CaptureHPC.checkFileAdded(jobid, "log"), "Expected log file added in /tmp/hpc/changes")
		self.assertTrue(com.CaptureHPC.checkFileAdded(jobid, "zip"), "Expected zip file added in /tmp/hpc/changes")

	def testCaptureNetworkError(self):
		jobid = "3"
		url = "http://www.test1retry.com/"
		self._testHelperSending(url, jobid)
		self.assertTrue(com.CaptureHPC.checkStatus("NETWORK_ERROR-408", jobid, url, 10),
									"Status NETWORK_ERROR-408 not added to log in expected time: should be less than %d seconds" % 10)
		self._testHelperVisited(url, jobid)
		self._testHelperBenign(url, jobid)
		self.assertFalse(com.CaptureHPC.checkFileAdded(jobid, "log"), "Expected log file added in /tmp/hpc/changes")
		self.assertFalse(com.CaptureHPC.checkFileAdded(jobid, "zip"), "Expected zip file added in /tmp/hpc/changes")
