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
import couchdb

class JsStaIntegrationTest(com.TestCaseVerbose):
	'''
	general info: https://drotest4.nask.net.pl:3000/issues/6420
	details: https://drotest4.nask.net.pl:3000/issues/5375

	Expected results from analysis process:
	* content of the web page will be downloaded and stored in the data store
	* JavaScript will be extracted from the web page source and stored for later analysis
	* the JavaScript will be analyzed by relevant analyzers and output from that analysis will be available for the user
	* JavaScript will be deobfuscated (if possible) and if a redirection technique is discovered, the URL to next web page will be extracted and stored
	** in case of multiple layers of obfuscation, all obtained JavaScripts are to be analyzed and all found relevant analysis results stored (that goes for all discovered URLs, exploits, etc.)
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
		com.Starter.initStart("hsn2-js-sta")
		com.Configuration.setConsoleConf(host="127.0.0.1", port=5672, timeout=4)

	def testJsStaBenign(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/js-sta-2.hwl")
		jobId = com.Console.submitJob("js-sta-2 feed.uri=/tmp/tests/resources/json/js-sta-benign.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].js_classification, "benign", "Expected JavaScript classified as obfuscated.")
		self.assertFalse(ret[1].js_malicious_keywords, "Expected js_malicious_keywords containing False.")
		# suspicious keywords found because of "document.write" inside js-sta-benign.proto
		self.assertTrue(ret[1].js_suspicious_keywords, "Expected js_suspicious_keywords containing False.")
		self.assertSet(ret[1], "creation_time")
		self.assertSet(ret[1], "js_sta_time_begin")
		self.assertSet(ret[1], "js_sta_time_end")
		self.assertSet(ret[1], "top_ancestor")
		self.assertSet(ret[1], "js_sta_results")
		self.assertSet(ret[1], "js_context_list")

	def testJsStaObfuscated(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/js-sta-2.hwl")
		jobId = com.Console.submitJob("js-sta-2 feed.uri=/tmp/tests/resources/json/js-sta-obfuscated.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].js_classification, "obfuscated", "Expected JavaScript classified as obfuscated.")
		self.assertFalse(ret[1].js_malicious_keywords, "Expected js_malicious_keywords containing False.")
		self.assertFalse(ret[1].js_suspicious_keywords, "Expected js_suspicious_keywords containing False.")
		self.assertSet(ret[1], "creation_time")
		self.assertSet(ret[1], "js_sta_time_begin")
		self.assertSet(ret[1], "js_sta_time_end")
		self.assertSet(ret[1], "top_ancestor")
		self.assertSet(ret[1], "js_sta_results")
		self.assertSet(ret[1], "js_context_list")

	def testJsStaMalicious(self):
		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/js-sta-2.hwl")
		jobId = com.Console.submitJob("js-sta-2 feed.uri=/tmp/tests/resources/json/js-sta-malicious.json")
		self.assertIsNotNone(jobId, "Returned job id is none.")
		finished = com.Console.waitForCompletion(jobId, 5, 1, True)
		self.assertTrue(finished, "Job failed or took too long.")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)
		self.assertEqual(ret[1].js_classification, "malicious", "Expected JavaScript classified as obfuscated.")
		self.assertTrue(ret[1].js_malicious_keywords, "Expected js_malicious_keywords containing True.")
		self.assertTrue(ret[1].js_suspicious_keywords, "Expected js_suspicious_keywords containing True.")
		self.assertSet(ret[1], "creation_time")
		self.assertSet(ret[1], "js_sta_time_begin")
		self.assertSet(ret[1], "js_sta_time_end")
		self.assertSet(ret[1], "top_ancestor")
		self.assertSet(ret[1], "js_sta_results")
		self.assertSet(ret[1], "js_context_list")

	def testJsStaFullJob(self):
		com.Starter.initCouchDB(wait=True)
		cdb = couchdb.Server()
		if 'hsn' in cdb:
			cdb.delete('hsn')
		com.Starter.initStart("hsn2-file-feeder")
		com.Starter.initStart("hsn2-webclient")
		com.Starter.initStart("hsn2-reporter")

		com.Configuration.setWorkflow("/tmp/tests/workflows/integration/js-sta-1.hwl")
		com.Configuration.setConf("/tmp/tests/file.txt", "http://js.honeysploit.hsn/dangerous2.html")
		jobId = com.Console.submitJob("js-sta-1")
		finished = com.Console.waitForCompletion(jobId, 50, 5, True)
		self.assertTrue(finished, "Job failed or took too long.")

		ret = com.Console.getDumpAsObjects(jobId, agg=self.testHelp.agg)

		# object 0, presence of required attributes
		self.assertSet(ret[0], "creation_time")
		self.assertSet(ret[0], "feeder_time_begin")
		self.assertSet(ret[0], "feeder_time_end")
		self.assertSet(ret[0], "url_count")
		self.assertSet(ret[0], "ipv4_count")
		self.assertSet(ret[0], "ipv6_count")
		self.assertSet(ret[0], "domain_count")
		self.assertSet(ret[0], "domain_idn_count")
		self.assertSet(ret[0], "top_ancestor")
		self.assertSet(ret[0], "depth")

		# object 0, values of required attributes
		self.assertGreater(ret[0].feeder_time_begin, ret[0].creation_time, name1="feeder_time_begin", name2="creation_time")
		self.assertGreater(ret[0].feeder_time_end, ret[0].feeder_time_begin, name1="feeder_time_end", name2="feeder_time_begin")
		self.assertEqual(ret[0].url_count, 1, name1="url_count")
		self.assertEqual(ret[0].ipv4_count, 0, name1="ipv4_count")
		self.assertEqual(ret[0].ipv6_count, 0, name1="ipv6_count")
		self.assertEqual(ret[0].domain_count, 1, name1="domain_count")
		self.assertEqual(ret[0].domain_idn_count, 0, name1="domain_idn_count")
		self.assertEqual(ret[0].top_ancestor, 1, name1="top_ancestor")
		self.assertEqual(ret[0].depth, 0, name1="depth")

		# object 1, presence of required attributes
		self.assertSet(ret[1], "html")
		self.assertSet(ret[1], "html_source")
		self.assertSet(ret[1], "url_original")
		self.assertSet(ret[1], "url_domain")
		self.assertSet(ret[1], "http_request")
		self.assertSet(ret[1], "http_code")
		self.assertSet(ret[1], "active")

		self.assertSet(ret[1], "creation_time")
		self.assertSet(ret[1], "js_sta_time_begin")
		self.assertSet(ret[1], "js_sta_time_end")
		self.assertSet(ret[1], "js_classification")
		self.assertSet(ret[1], "js_sta_results")
		self.assertSet(ret[1], "js_context_list")
		self.assertSet(ret[1], "js_malicious_keywords")
		self.assertSet(ret[1], "js_suspicious_keywords")

		self.assertSet(ret[1], "top_ancestor")
		self.assertSet(ret[1], "origin")
		self.assertSet(ret[1], "type")
		self.assertSet(ret[1], "depth")

		# object 1, values of required attributes
		self.assertEqual(ret[1].html, "True", name1="html")
		self.assertEqualPages("http://localhost:8080/data/%s/%s" % (jobId, ret[1].html_source.getKey()), "http://js.honeysploit.hsn/dangerous2.html")
		self.assertEqual(ret[1].url_original, "http://js.honeysploit.hsn/dangerous2.html", name1="url_original")
		self.assertEqual(ret[1].url_domain, "js.honeysploit.hsn", name1="url_domain")
		self.assertEqual(ret[1].http_code, 200, name1="http_code")
		self.assertEqual(ret[1].active, "True", name1="active")

		self.assertGreater(ret[1].js_sta_time_begin, ret[1].creation_time, name1="js_sta_time_begin", name2="creation_time")
		self.assertGreater(ret[1].js_sta_time_end, ret[1].js_sta_time_begin, name1="js_sta_time_end", name2="js_sta_time_begin")
		# TODO: clarify if it should be "obfuscated" instead
		self.assertEqual(ret[1].js_classification, "malicious", name1="js_classification")
		self.assertEqual(ret[1].js_malicious_keywords, "True", name1="js_malicious_keywords")
		self.assertEqual(ret[1].js_suspicious_keywords, "True", name1="js_suspicious_keywords")

		self.assertEqual(ret[1].top_ancestor, 2, name1="top_ancestor")
		self.assertEqual(ret[1].origin, "file", name1="origin")
		self.assertEqual(ret[1].type, "url", name1="type")
		self.assertEqual(ret[1].depth, 0, name1="depth")

		# object 2, presence of required attributes
		self.assertSet(ret[2], "html")
		self.assertSet(ret[2], "html_source")
		self.assertSet(ret[2], "url_original")
		self.assertSet(ret[2], "http_request")
		self.assertSet(ret[2], "http_code")
		self.assertSet(ret[2], "active")

		self.assertSet(ret[2], "creation_time")
		self.assertSet(ret[2], "js_sta_time_begin")
		self.assertSet(ret[2], "js_sta_time_end")
		self.assertSet(ret[2], "js_classification")
		self.assertSet(ret[2], "js_sta_results")
		self.assertSet(ret[2], "js_context_list")
		self.assertSet(ret[2], "js_malicious_keywords")
		self.assertSet(ret[2], "js_suspicious_keywords")

		self.assertSet(ret[2], "top_ancestor")
		self.assertSet(ret[2], "parent") #+++
		self.assertSet(ret[2], "origin")
		self.assertSet(ret[2], "type")
		self.assertSet(ret[2], "depth")
		self.assertSet(ret[2], "priority") #+++

		# object 2, values of required attributes
		self.assertEqual(ret[2].html, "True", name1="html")
		self.assertEqualPages("http://localhost:8080/data/%s/%s" % (jobId, ret[2].html_source.getKey()), "http://exploitserver.evil/eicar.html")
		self.assertEqual(ret[2].url_original, "http://exploitserver.evil/eicar.html", name1="url_original")
		self.assertEqual(ret[2].http_code, 200, "Expected http_code set to 200, got %s" % ret[1].http_code)
		self.assertEqual(ret[2].active, "True", "active")

		self.assertGreater(ret[2].js_sta_time_begin, ret[1].creation_time, name1="js_sta_time_begin", name2="creation_time")
		self.assertGreater(ret[2].js_sta_time_end, ret[1].js_sta_time_begin, name1="js_sta_time_end", name2="js_sta_time_begin")
		self.assertEqual(ret[2].js_classification, "malicious", name1="js_classification")
		self.assertEqual(ret[2].js_malicious_keywords, "True", name1="js_malicious_keywords")
		self.assertEqual(ret[2].js_suspicious_keywords, "True", name1="js_suspicious_keywords")

		self.assertEqual(ret[2].top_ancestor, 2, name1="top_ancestor")
		self.assertEqual(ret[2].parent, 2, name1="parent")
		self.assertEqual(ret[2].origin, "iframe", name1="origin")
		self.assertEqual(ret[2].type, "url", name1="type")
		self.assertEqual(ret[2].depth, 1, name1="depth")
		self.assertEqual(ret[2].priority, 0, name1="priority")

	def runTest(self):
		try:
			self.setUp()
			self.testJsStaBenign()
			#signal.pause()
		except KeyboardInterrupt:
			pass
		finally:
			self.doCleanups()
		try:
			self.setUp()
			self.testJsStaObfuscated()
			#signal.pause()
		except KeyboardInterrupt:
			pass
		finally:
			self.doCleanups()
		try:
			self.setUp()
			self.testJsStaMalicious()
			#signal.pause()
		except KeyboardInterrupt:
			pass
		finally:
			self.doCleanups()
		try:
			self.setUp()
			self.testJsStaFullJob()
			signal.pause()
		except KeyboardInterrupt:
			pass
		finally:
			self.doCleanups()

if __name__ == "__main__":
	import signal
	a = JsStaIntegrationTest()
	a.runTest()
