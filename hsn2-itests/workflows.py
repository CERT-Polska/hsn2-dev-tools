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

class WorkflowsIntegrationTest(unittest.TestCase):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Starter.initStart("hsn2-framework")
		time.sleep(3)
		com.Configuration.setWorkflow("/tmp/tests/workflows/simple/simple.hwl")

	def testWorkflowList(self):
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=2)
		ret = com.Console.call("hc w l")
		logging.info(ret[1])
		self.assertRegexpMatches(ret[1], "Found \d+ workflow\(s\):", "Framework should report at least 1 workflow.");
		self.assertRegexpMatches(ret[1], r'name:\s+simple', "Couldn't find workflow ID or workflow ID is different than simple")
		# TODO: restore line below, when enabling/disabling  workflows will be implemented
		#self.assertRegexpMatches(ret[1], r'enabled:\s+True', "The workflow hasn't been enabled.")
