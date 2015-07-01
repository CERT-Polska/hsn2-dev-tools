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

class PingIntegrationTest(unittest.TestCase):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Starter.initStart("hsn2-framework")

	def testPingOK(self):
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=2)
		ret = com.Console.call("hc ping")
		logging.info(ret[1])
		self.assertIn("The framework is alive.", ret[1], "Couldn't receive ping response from framework.")

	def testPingNotOK(self):
		com.Configuration.setConsoleConf(host="127.0.0.1", port=9550, timeout=2)
		ret = com.Console.call("hc ping")
		logging.info(ret[1])
		self.assertIn("ERROR: Cannot connect to HSN2 Bus because 'Can't connect to RabbitMQ", ret[1], "Expected error.")
