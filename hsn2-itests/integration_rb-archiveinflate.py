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
Created on 04-05-2012

@author: wojciechm
'''

import commons as com
import logging

class ArchiveInflateIntegrationTest(com.TestCaseVerbose):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Starter.initCouchDB()
		com.Configuration.setServices(["object-feeder","rb-archiveinflate","reporter"])
		com.Configuration.resetJobCounter()
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-object-feeder")
		com.Starter.initStart("hsn2-rb-archiveinflate")
		com.Starter.waitCouchDB()
		com.Configuration.deleteCouchDB(database="hsn")
		com.Starter.initStart("hsn2-reporter")
		com.Configuration.setWorkflow("/tmp/tests/workflows/nuggets/rb-archiveinflate1.hwl")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testSupported(self):
		'''
		Test how the nugget reacts to a supported file and file-type.
		Expected behaviour:
		- set rb_archiveinflate_return_value to 0
		- total of 11 objects created in the job
		- first extracted file is a directory (size=0) named "files" with a specific hash
		'''
		jobId = com.Console.submitJob("rb-archiveinflate1 feed.uri=/tmp/tests/resources/json/rb-archiveinflate-supported.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_archiveinflate_return_value"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_archiveinflate_return_value, 0)
		self.assertEqual(len(ret), 11)
		self.assertEqual(ret[2].size,0)
		self.assertEqual(ret[2].filename,"files")
		self.assertEqual(ret[2].sha256,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-archiveinflate", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertIsNotNone(objDict, "Details in object don't have the value attribute.")
		self.assertIn({u'value': u'0', u'name': u'return value', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")

	def testUnsupportedType(self):
		'''
		Test results of processing a file that has an unsupported file-type defined.
		Expected behaviour:
		- set rb_archiveinflate_return_value to 2
		'''
		jobId = com.Console.submitJob("rb-archiveinflate1 feed.uri=/tmp/tests/resources/json/rb-archiveinflate-unsupportedtype.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_archiveinflate_return_value"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_archiveinflate_return_value, 2)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-archiveinflate", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertIsNotNone(objDict, "Details in object don't have the value attribute.")
		self.assertIn({u'value': u'2', u'name': u'return value', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")

	def testUnsupportedFile(self):
		'''
		Test results of processing a file that is mistakenly identified as an archive.
		Expected behaviour:
		- set rb_archiveinflate_return_value to 2
		'''
		jobId = com.Console.submitJob("rb-archiveinflate1 feed.uri=/tmp/tests/resources/json/rb-archiveinflate-unsupportedfile.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 16, 2, True)
		self.assertTrue(finished, "Job failed or took too long.")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertTrue(ret[1].isSet("rb_archiveinflate_return_value"), "Expected attribute wasn't set.")
		self.assertEqual(ret[1].rb_archiveinflate_return_value, 2)
		objDict = com.getFromCouch(jobId, ret[1].getObjectId(), "rb-archiveinflate", verbose=False)
		self.assertIsNotNone(objDict, "Failed to get object from couch.")
		objDict = objDict.get('details')
		self.assertIsNotNone(objDict, "Details not found in object.")
		objDict = objDict.get('value')
		self.assertIsNotNone(objDict, "Details in object don't have the value attribute.")
		self.assertIn({u'value': u'2', u'name': u'return value', u'structure': u'text'}, objDict,
					"Didn't find structure message in the details attribute.")

	def runTest(self):
		pass

if __name__ == "__main__":
	import signal
	a = ArchiveInflateIntegrationTest()
	try:
		a.setUp()
		a.testSupported()
		signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
	try:
		a.setUp()
		a.testUnsupportedType()
		signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
	try:
		a.setUp()
		a.testUnsupportedFile()
		signal.pause()
	except KeyboardInterrupt:
		pass
	finally:
		a.doCleanups()
