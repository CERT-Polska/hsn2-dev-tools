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
Created on 2012-05-10

@author: pawelch
'''

import commons as com
import logging
import couchdb
#from jsonpath import jsonpath

class SimpleJobIntegrationTest(com.TestCaseVerbose):
	testHelp = None

	def setUp(self):
		self.testHelp = com.TestHelp("/var/log/hsn2/", suiteName=self.__class__.__name__, testName=self._testMethodName, loglevel=logging.INFO)
		self.addCleanup(self.testHelp.done)
		com.Starter.initRabbitMQ()
		com.Configuration.resetJobCounter()
		com.Website("/tmp/tests/workflows/simple",80)
		com.Starter.initCouchDB(wait=True)
		com.Starter.initStart("hsn2-framework")
		com.Starter.initStart("hsn2-object-store-mongodb")
		com.Starter.initStart("hsn2-data-store")
		com.Starter.initStart("hsn2-file-feeder")
		com.Starter.initStart("hsn2-webclient")
		com.Starter.initStart("hsn2-js-sta")
		cdb = couchdb.Server()
		if 'hsn' in cdb:
			cdb.delete('hsn')
		com.Starter.initStart("hsn2-reporter")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)
		com.Configuration.setWorkflow("/tmp/tests/workflows/simple/simple.hwl")
		com.Configuration.setConf("/tmp/tests/file.txt", "http://localhost/")

	def testSimpleJob(self):
		logging.info("Test if CouchDB responds to HTTP requests...")
		ret = com.Console.call("curl 127.0.0.1:5984 --stderr /dev/null")
		logging.info(ret[1])
		self.assertIn('{"couchdb":"Welcome","version":"1.2', ret[1], "Couldn't connect to CouchDB.")

		logging.info("Test if submitted job is accepted...")
		jobId = com.Console.submitJob("simple --param feeder1.uri=/tmp/tests/file.txt")
		self.assertIsNotNone(jobId, "Job ID not found.")
		logging.info('The job ID is %s' % jobId)

		logging.info("Test if job finishes successfully...")
		completed = com.Console.waitForCompletion(jobId=jobId, maxTime=30, period=1, verbose=True)
		ret = com.Console.call("hc j d %s" % jobId)
		logging.info(ret[1])
		self.assertTrue(completed, "Job failed to finish successfully.")
		# TODO: check time elapsed if completed in >30s

		logging.info("Test if job finished in less than 30 seconds...")
		jd = com.JobDetails(jobId)
		timeElapsed = int(jd.get("job_processing_time_sec"))
		self.assertGreaterEqual(50, timeElapsed, "The job %s took %s seconds, which is more than accepted 30s" % (jobId, timeElapsed))

		logging.info("Test if there are 4 objects found by unicorn...")
		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(len(ret), 4, "Expected 2 objects from unicorn, received %d" % len(ret))

		logging.info("Test if there are 2 objects found in CouchDB...")
		couch = couchdb.Server()['hsn']
		self.assertEqual(len(couch), 2, "Expected 2 objects from CouchDB, received %d" % len(couch))

		logging.info("Test if JavaScript contexts are consistent between webclient and js-sta...")
		for objId in couch:
			self.assertIn(objId, [str(jobId) + ":2:js-sta", str(jobId) + ":2:webclient"], "%s is not allowed object id in CouchDB" % objId)

		logging.info("Test if there is 1 context detected by webclient...")
		ret = couch[str(jobId) + ':2:webclient']['details']['value']
		i = 0
		for c in ret:
			if c['name'] == u'js_contexts':
				break
			i += 1
		self.assertEqual(len(ret[i]['value']), 10, "Expected 10 JavaScript context in 1:2:webclient, found %s" % len(ret[i]['value']))

		logging.info("Test if there is 1 context analysed by js-sta...")
		ret = couch[str(jobId) + ':2:js-sta']['details']['value'][0]['value']
		self.assertEqual(len(ret), 10, "Expected 10 JavaScript context in 1:2:js-sta, found %s" % len(ret))

#		logging.info("Test if content 0 is obfuscated...")
#		ret = jsonpath(couch[str(jobId) + ':2:js-sta'],"$.details.value[?(@.name='Individual contexts')].value[?(@.name='Context no. 0')].value[?(@.name='classification')].value")[0]
#		self.assertEqual(ret, u'OBFUSCATED', "Expected context 0 classified as OBFUSCATED, got %s" % ret)

		logging.info("Test if there is max. 1 HTTP request...")
		ret = com.Configuration.getConf("/var/log/hsn2/site-80.log")
		self.assertEqual(len(ret), 1, "Expected 1 HTTP request, got %d" % len(ret))

		logging.info("Test if there is 1 file attached to 1:2:webclient...")
		ret = couch[str(jobId) + ':2:webclient']['_attachments'].keys()
		self.assertEqual(len(ret), 1, "Expected 1 attachment to 1:2:webclinet, got %d" % len(ret))

		handle = com.getUrlHandle('http://localhost:80', method='GET')
		html = ''.join(handle.readlines())
		attachment = ''.join(couch.get_attachment(str(jobId) + ":2:webclient","%s" % ret[0]).readlines())
		msg = "Expected HTML attached to 1:2:webclient is exactly the same as the page from http://localhost, but they differ:\nhtml:\n%s\nattachment:\n%s" % (html, attachment)
		self.assertEqual(html, attachment, msg)

	def runTest(self):
		pass
