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

import os
import sys
import re
import shutil
import socket
import subprocess
import time
import urllib
import urllib2
import xml.dom.minidom

from hsn2_commons.loggingSetup import logging, setupLogging
import hsn2_commons.hsn2objectwrapper as ow

class BackupException(Exception):
	'''
	Exception to be used when something goes wrong in a backup procedure.
	'''
	pass

class BackupSourceException(BackupException):
	'''
	Used when a file that is to be backed up wasn't found.
	'''
	pass

class BackupExistsException(BackupException):
	'''
	Used when a file that is to be backed up already has a backup file (not from this run).
	'''
	pass

class InitException(Exception):
	'''
	Exception to be used when trying to start a process.
	'''
	pass

class SetupException(Exception):
	'''
	Exception to be used when dealing with likely faulty setups.
	'''

class AlreadyExistsException(Exception):
	'''
	Used when object with same attributes already exists in dictionary. 
	'''
	pass

class Request(urllib2.Request):
	'''
	Extension of the urllib2.Request class in order to allow specifying additional method names (such as DELETE).
	'''
	def __init__(self, *args, **kwargs):
		self._method = kwargs.pop('method', None)
		urllib2.Request.__init__(self, *args, **kwargs)

	def get_method(self):
		return self._method if self._method else super(Request, self).get_method()

import unittest
class TestCaseVerbose(unittest.TestCase):

	def assertEqual(self, first, second, msg = None, name1 = None, name2 = None):
		first = str(first)
		second = str(second)
		if msg is None:
			if name1 is None:
				msg = "Expected: '%s'," % second
				msg += " got: '%s'." % first
			elif isinstance(name1, str):
				if name2 is None:
					msg = "Expected %s set to %s, got:\n" % (name1, second)
					msg += "%s." % first
				elif isinstance(name2, str):
					msg = "Expected %s == %s, got:\n" % (name1, name2)
					msg += "%s: %s.\n" % (name1, first)
					msg += "%s: %s." % (name2, second)
		unittest.TestCase.assertEqual(self, first, second, msg = msg)

	def assertEqualPages(self, first, second, msg = None):
		# TODO: add try-catch to avoid crashes on error 404
		handle1 = getUrlHandle(first, method = 'GET')
		html1 = ''.join(handle1.readlines())
		handle2 = getUrlHandle(second, method = 'GET')
		html2 = ''.join(handle2.readlines())
		if msg is None:
			msg = "Expected pages %s and %s to have the same content, but they differ:\n" % (first, second)
			msg += "first:\n%s\n" % html1
			msg += "second:\n%s" % html2
		unittest.TestCase.assertEqual(self, html1, html2, msg = msg)

	def assertGreater(self, a, b, msg = None, name1 = None, name2 = None):
		if msg is None and isinstance(name1, str) and isinstance(name2, str):
			msg = "Expected %s > %s.\n" % (name1, name2)
			msg += "%s: %d\n" % (name1, a)
			msg += "%s: %d" % (name2, b)
		unittest.TestCase.assertGreater(self, a, b, msg = msg)

	def assertSet(self, obj, attr, msg = None):
		if msg is None:
			msg = "Expected %s attribute set." % attr
		unittest.TestCase.assertTrue(self, obj.isSet(attr), msg = msg)

	def assertNotSet(self, obj, attr, msg = None):
		if msg is None:
			msg = "Expected %s attribute not set." % attr
		unittest.TestCase.assertFalse(self, obj.isSet(attr), msg = msg)

class Backup():
	'''
	Methods collected into a class for grouping by functionality.
	The class isn't meant to be instantiated. It's a Helper.
	'''
	ignore = False
	files = set()

	def __init__(self):
		'''
		Throws an Exception if instantiated.
		'''
		raise Exception("This class isn't meant to be instantiated.")

	@classmethod
	def backupFile(cls, fileP, suffix = ".bak", copy = True):
		'''
		Creates a backup of the chosen file in the same directory as the file itself.
		If the file does not exist or isn't accessible then a BackupException will be raised.
		If a backup file already exists for the file and it wasn't created in this run then a BackupException will be raised.
		Remember to call restoreFiles to rollback the changes at cleanup.
		@param fileP: The absolute path to the file that is to be backed up.
		@param suffix: The suffix used for marking the backup file.
		@param copy: if True then the file will be copied and otherwise it will be moved.
		'''
		if fileP not in cls.files:
			if not os.path.isfile(fileP):
				raise BackupSourceException("File '%s' does not exist or is not accessible." % fileP)
			backup = "%s%s" % (fileP, suffix)
			if os.path.isfile(backup) and cls.ignore is False:
				raise BackupExistsException("Backup file '%s' already exists." % backup)
			if copy:
				shutil.copy2(fileP, backup)
				logging.debug("Backed up '%s' (Copy)" % fileP)
			else:
				shutil.move(fileP, backup)
				logging.debug("Backed up '%s' (Move)" % fileP)
			cls.files.add(fileP)
			return True
		else:
			logging.info("File '%s' already backed up in this session. Skipping." % fileP)
			return False
	@classmethod
	def restoreFile(cls, fileP, suffix = ".bak"):
		'''
		Restores a backup of the chosen file.
		@param fileP: The absolute path to the file that was backed up (without the backup suffix).
		@param suffix: The suffix used for marking the backup file.
		'''
		backup = "%s%s" % (fileP, suffix)
		if os.path.isfile(backup):
			shutil.move(backup, fileP)
			logging.debug("Restored '%s' from backup" % fileP)

	@classmethod
	def restoreFiles(cls):
		'''
		Restore all files that were backed up in this run.
		'''
		for fileP in cls.files:
			cls.restoreFile(fileP)
		cls.files = set()

	@classmethod
	def backupOldLogs(cls, path = "/var/log/hsn2", suffix = ".log"):
		'''
		Backup all old log files at the specified path.
		@param path: The directory containing the files that are to be backed up.
		@param suffix: The suffix of the files that are to be backed up. Passing None means all files.
		'''
		if not os.path.isdir(path):
			return
		logFiles = os.listdir(path)
		for logFile in logFiles:
			if suffix is None or logFile[-len(suffix):] == suffix:
				Backup.backupFile(os.path.join(path, logFile), copy = False)

	@classmethod
	def backupCouchDB(cls, dbName = "hsn", path = "/var/lib/couchdb/1.1.1/", exception = False):
		fullPath = os.path.join(path, "%s.couch" % dbName)
		if os.path.isdir(fullPath):
			raise SetupException("CouchDB backup pointing to dir instead of file")
		try:
			cls.backupFile(fullPath)
		except BackupException as e:
			if exception:
				raise e

def getUrlHandle(url, data = None, method = "POST", timeout = 10):
	'''
	Wrapper for handling URL access. Retries 5 times in case of failure.
	@param url: The url that is to be accessed.
	@param data: The data that is to be POSTED.
	@param method: The name of the method that is to be sent.
	@param timeout: Number of seconds to wait for connection.
	'''
	req = Request(url, data, method = method)
	i = 0
	handle = None
	while True:
		try:
			handle = urllib2.urlopen(url = req, timeout = timeout)
			break
		except urllib2.URLError as e:
			i = i + 1
			if i < 5:
				time.sleep(1)
			else:
				raise e
	return handle

def getFromCouch(jobId, objectId, serviceName = "", verbose = True, url = "http://localhost:5984/hsn", timeout = 10):
	'''
	Wrapper for getting objects from couchDB.
	@param jobId: The job that the data belongs to.
	@param objectId: The objectId that the data belongs to.
	@param serviceName: The name of the service that was reported (reporter configuration).
	@param url: The location of the couch database REST api.
	@param timeout: Number of seconds to wait for connection.
	@return: dictionary with the data if the object was found and otherwise None
	'''
	if len(serviceName) > 0:
		serviceName = ":%s" % serviceName
	objUrl = "%s/%d:%d%s" % (url, long(jobId), long(objectId), serviceName)
	objUrl = urllib.quote(objUrl, safe = ":/")
	try:
		handle = getUrlHandle(objUrl, None, "GET")
	except urllib2.URLError as e:
		logging.error(e)
		return None
	import json
	text = ''.join(handle.readlines())
	if verbose:
		logging.info(text)
	dictionary = json.loads(text)
	return dictionary

class Console():
	'''
	Methods collected into a class for grouping by functionality.
	The class isn't meant to be instantiated. It's a Helper.
	'''
	completedRegexp = re.compile(r"COMPLETED")
	abortedRegexp = re.compile(r"ABORTED|FAILED")
	jobIdRegexp = re.compile(r"The job has been accepted.\s*\(Id=(\d+)\)")
	dumpRegexp = re.compile(r"Dump file (\d+.json)")

	@classmethod
	def sysCall(cls, args, inputVals = None, shell = False, cwd = None, stderr = False):
		'''
		Wrapper for handling synchronous calls to external binaries.
		Removed redirect of STDERR as it was causing communicate to block in some cases.
		@param args: The arguments to invoke (args[0] is the path to the executable)
		@param inputVals: Data that is to be passed to stdin.
		@param shell: Whether this is meant to be invoked in the sh interpreter.
		@param cwd: The working directory to use for the call.
		@param stderr: Whether to capture stderr.
		@return: tuple (return value, STDOUT, STDERR) for the process that was called.
		'''
		if stderr: stderr = subprocess.PIPE
		else: stderr = None
		proc = subprocess.Popen(args, shell = shell, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = stderr, close_fds = True, cwd = cwd, universal_newlines = True)
		out = proc.communicate(inputVals)
		retval = proc.returncode
		return (retval, out[0], out[1])

	@classmethod
	def call(cls, string, stderr = False):
		'''
		Wrapper for handling simple synchronous calls to external binaries. Calls sysCall.
		@param string: The string that will be split into arguments for the call.
		@param stderr: Whether to capture stderr.
		@return: tuple (return value, STDOUT, STDERR) for the process that was called.
		'''
		logging.info("Calling: %s" % string)
		return cls.sysCall(string.split(), stderr = stderr)

	@classmethod
	def submitJob(cls, params, verbose = True):
		'''
		Helper for submitting jobs and retrieving their ids.
		@param params: The workflow name and parameters that are to be submitted with the job.
		@param verbose: Whether the response is to appear in the logging output.
		@return: jobId if found a job id and otherwise None.
		'''
		params = "hc j s " + params
		ret = cls.call(params)
		if verbose:
			logging.info(ret[1])
		result = cls.jobIdRegexp.search(ret[1])
		if result is None: return None
		else:
			return result.group(1)

	@classmethod
	def waitForCompletion(cls, jobId = 1, maxTime = 20, period = 2, verbose = False):
		'''
		Waits for console to report job as completed/aborted.
		@param id: The id of the job that the function will be waiting for.
		@param maxTime: The maximum amount of time to wait. If set to a negative number then keeps waiting.
		@param period:
		'''
		jobId = int(jobId)
		command = "hc j d %d" % jobId
		timeStart = time.time()
		timeNow = time.time()
		while maxTime < 0 or (timeNow - timeStart < maxTime):
			timeNow = time.time()
			time.sleep(period)
			output = cls.call(command)
			output = output[1]
			if verbose:
				logging.info(output)
			if cls.completedRegexp.search(output):
				return output
			if cls.abortedRegexp.search(output):
				return False
		return False

	@classmethod
	def getDumpAsObjects(cls, jobId, agg = None):
		ret = Console.call("unicorn -dump %d" % int(jobId))
		result = cls.dumpRegexp.search(ret[1])
		if result is None:
			return None
		else:
			result = (result.groups(1))[0]
			path = os.path.join("/tmp", "tests", "dump", result)
			result = ow.toObjectsFromJSON(path, ignoreIds = False)
			result = sorted(result, key = lambda x: x.getObjectId())
			if agg is None:
				os.remove(path)
			else:
				agg.aggregateFile(path)
			return result

class CaptureHPC():
	'''
	Methods collected into a class for grouping by functionality.
	The class isn't meant to be instantiated. It's a Helper.
	'''

	log = "/tmp/hpc/url.log"
	logs = "/tmp/hpc"

	def __init__(self):
		'''
		Throws an Exception if instantiated.
		'''
		raise Exception("This class isn't meant to be instantiated.")

	@classmethod
	def add(cls, url, jobid):
		host = 'localhost'
		port = 31337
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host, port))
		command = "addurl %s %s" % (url, jobid)
		s.send(command)
		time.sleep(2)
		s.close()

	@classmethod
	def clearLogs(cls, logs = None):
		if logs is None:
			logs = cls.logs
		Console.call("rm -rf %s" % logs)

	@classmethod
	def getLog(cls, log = None):
		if log is None:
			log = cls.log
		with open(log, "r") as f:
			ret = f.read()
		return ret

	@classmethod
	def checkStatus(cls, status, jobid, url, timeout = 90):
		'''
		Checks if the status of the url processed by capture-hpc appeared in log file.
		@param status: string, a status to ask for
		@param jobid: string, expected job id
		@param url: string, url processed by capture-hpc
		@param timeout: int, a number of seconds to wait for status to show up
		'''
		time_started = time.time()
		timeout_time = time_started + timeout
		logging.info("Checking log for: %s %s %s" % (status, jobid, url))
		while "%s %s %s" % (status, jobid, url) not in cls.getLog() and time.time() < timeout_time:
			time.sleep(1)
		time_finished = time.time()
		if time_finished < timeout_time:
			logging.info("Finished after %d seconds." % (time_finished - time_started))
			return True
		else:
			logging.info("%s %s %s not added to %s in expected time (less than %d seconds)" % (status, jobid, url, cls.log, timeout))
			return False

	@classmethod
	def checkFileAdded(cls, jobid, fileext):
		if not os.path.exists("/tmp/hpc/changes"):
			return False
		import datetime
		today = datetime.datetime.now().strftime("%d%m%Y")
		mask = "%s_%s" % (jobid, today)
		for f in os.listdir("/tmp/hpc/changes"):
			if mask in f and fileext in f:
				return True
		return False

class Starter():
	'''
	Methods collected into a class for grouping by functionality.
	The class isn't meant to be instantiated. It's a Helper.
	'''
	inits = list()

	def __init__(self):
		'''
		Throws an Exception if instantiated.
		'''
		raise Exception("This class isn't meant to be instantiated.")

	@classmethod
	def isRunning(cls, pid):
		'''
		Used for checking is a process is running or not.
		@param pid: Must be a path pointing to a pid file, a process name or a pid.
		@return: True is the process is running. Otherwise false.
		'''
		if isinstance(pid, str):
			inPid = os.path.join("/var/run", "%s.pid" % (pid))
			if not os.path.isfile(inPid):
				inPid = os.path.join("/var/run", "%s" % (pid), "%s.pid" % (pid))
			if not os.path.isfile(inPid):
				return False
			inPid = ''.join(Configuration.getConf(inPid)).strip()
			if len(inPid) == 0:
				return False
		elif isinstance(pid, int):
			inPid = str(pid)
		else:
			raise SetupException("Passed pid value is neither a string nor an integer.")

		if len(inPid) > 0:
			ret = Console.sysCall(["/bin/ps", "-p", inPid])
			if len(ret[1]) > 28:
				return True
			else:
				return False
		else: return False

	@classmethod
	def initStart(cls, proc, autoStop = True, expected = "is running.\n", service = True):
		'''
		Used for starting a process which has a startup file in the init.d directory.
		If the process return code was different than 0 then an InitException will be raised.
		If expected is passed and the process isn't running then an InitException will be raised.
		@param proc: the name of the startup script in the init.d directory.
		@param autoStop: if True then the process will be stopped when stopStartedInits is called.
		@param expected: the string that is expected to end the status string from an init script in it's running state. If None is passed then the status won't be checked.
		'''
		if service:
			procFull = "service %s" % proc
		else:
			procFull = "/etc/init.d/%s" % proc
			
		cls.initStop(proc, verbose = False)
		ret = Console.call("%s %s" % (procFull, "start"))
		if ret[0] != 0:
			logging.error(ret)
			raise InitException("Couldn't start init")
		if expected is not None:
			if not cls.initStatus(proc, expected):
				raise InitException("%s didn't start" % proc)
		if autoStop:
			cls.inits.append((proc, expected))
		logging.info("Init '%s' started" % proc)

	@classmethod
	def initRabbitMQ(cls, autoStop = True):
		Starter.initStart("rabbitmq-server", autoStop, expected = "...done.\n", service = False)

	@classmethod
	def initCouchDB(cls, autoStop = True, wait = False):
		if wait:
			Starter.initStart("couchdb", autoStop, expected = "time to relax.\n")
		else:
			Starter.initStart("couchdb", autoStop, expected = None)

	@classmethod
	def initStatus(cls, proc, expected = "is running.\n", pid = None):
		'''
		Used for checking if a process that was started with it's init.d startup file is running.
		@param proc: the name of the startup script in the init.d directory (or an absolute path).
		@param expected: the string that is expected to end the status string from an init script in it's running state.
		@return: True if the expected string was found at the end of the status message and otherwise False.
		'''
		procFull = "service %s" % proc
		expLen = len(expected)

		timeout = 60
		keep_running = True
		start = time.time()
		while keep_running:
			ret = Console.call("%s %s" % (procFull, "status"), True)
			if ret[0] == 0 or time.time() - start > timeout:
				keep_running = False
			else:
				time.sleep(1)

		if ret[1][-expLen:] != expected:
			logging.info("Got:'%s', Expected:'%s'" % (ret[1][-expLen:], expected))
			return False
		return True

	@classmethod
	def waitCouchDB(cls):
		Starter.initStatus("couchdb", expected = "time to relax.\n")

	@classmethod
	def initStop(cls, proc, expected = None, verbose = True):
		'''
		Used for stopping a process which has a startup file in the init.d directory.
		If expected is passed and the process isn't running then an InitException will be raised.
		@param proc: the name of the startup script in the init.d directory (or an absolute path).
		@param expected: the string that is expected to end the status string from an init script in it's running state. If None is passed then the status won't be checked.
		'''
		procFull = "service %s" % proc
		if expected is not None:
			if not cls.initStatus(proc, expected):
				raise InitException("%s was dead before calling stop." % proc)
		Console.call("%s %s" % (procFull, "stop"))
		if verbose:
			logging.info("Init '%s' stopped" % proc)

	@classmethod
	def stopStartedInits(cls):
		'''
		Used for stopping all processes that were started with initStart with the autoStop parameter set to True.
		Processes will be stopped in the reverse order of how they were started.
		'''
		for i in range(len(cls.inits)):
			initFile = cls.inits.pop()
			try:
				cls.initStop(initFile[0], initFile[1])
			except BaseException as e:
				logging.warn(e)
			#logging.info("Init '%s' stopped" % initFile[0])

class LogAggregator():
	'''
	Collects files with a defined suffix from specified paths.
	'''
	putTo = None

	def __init__(self, putTo = "/var/log/hsn2/", merge = False):
		'''
		Sets up the aggregator.
		@param putTo: The path in which the logs are to be aggregated. This should not be the same as the default log path!
		@param merge: Whether the directory specified by putTo should be removed and recreated (in order to delete all content).
		'''
		self.putTo = os.path.abspath(putTo)
		if os.path.isdir(self.putTo):
			if not merge:
				shutil.rmtree(self.putTo)
				os.makedirs(self.putTo)
		else:
			os.makedirs(self.putTo)

	def aggregate(self, takeFrom = "/var/log/hsn2", suffix = ".log"):
		'''
		Collect chosen files into a separate directory.
		@param takeFrom: where files will be taken from
		@param suffix: The suffix of the files that are to be aggregated. Passing None means all files.
		'''
		takeFrom = os.path.abspath(takeFrom)
		if takeFrom == self.putTo:
			logging.warning("takeFrom is the same as putTo '%s'. Aggregation skipped!" % takeFrom)
		else:
			logFiles = os.listdir(takeFrom)
			for logFile in logFiles:
				if suffix is None or os.path.splitext(logFile)[1] == suffix:
					shutil.move(os.path.join(takeFrom, logFile), os.path.join(self.putTo, logFile))
			logging.info("Aggregated logs from %s to %s" % (takeFrom, self.putTo))

	def aggregateFile(self, filePath):
		'''
		Collect chosen files into a separate directory.
		@param filePath: the file to aggregate
		'''
		split = os.path.split(filePath)
		shutil.move(filePath, os.path.join(self.putTo, split[1]))
		logging.info("Aggregated %s to %s" % (filePath, self.putTo))

class Website():
	'''
	Class for handling setting up and shutting down websites used for tests.
	'''
	sites = dict()
	proc = None
	filePath = None
	port = None

	def __init__(self, filePath, port, logTo = "/var/log/hsn2"):
		'''
		Sets up a SimpleHTTPServer with a root at the given filePath.
		If the website root doesn't exist then a SetupException will be raised.
		If a website was already started in this run on the port with a different filePath then a SetupException will be raised.
		Repeated calls with the same port and filePath will be ignored (but logged).
		@param filePath: The root of the website.
		@param port: The port on which the website is to be available.
		@param logTo: Where to store the access log file for the site (named site-<PORT>.log).
		'''
		if not os.path.isdir(filePath):
			raise SetupException("Specified path is not a accessible directory %s" % (filePath))
		if (self.__class__.sites.get(port) is None):
			self.proc = subprocess.Popen(["python", "-m", "SimpleHTTPServer", "%d" % port],
							stdout = open(os.path.join(logTo, "site-%d.log" % port), "w"),
							stderr = subprocess.STDOUT,
							cwd = filePath)
			self.filePath = filePath
			self.port = port
			self.__class__.sites[port] = self
			logging.info("Setup website with root at '%s on port %d" % (filePath, port))
		else:
			filePath2 = self.__class__.sites[port].getFilePath()
			if (filePath != filePath2):
				raise SetupException("A site using the port %d has already been setup with it's root at %s" % (port, filePath2))
			else:
				logging.info("Site on port %d with root at %s already running. Skipping setup." % (port, filePath2))

	def getFilePath(self):
		return self.filePath

	def getPort(self):
		return self.port

	def shutdownWebsite(self):
		'''
		Shutdown a website which was started in this run on the given port.
		'''
		logging.info("Shutting down website on port %d" % self.getPort())
		self.proc.terminate()
		return True

	@classmethod
	def shutdownWebsites(cls):
		'''
		Shutdown all websites that were started in this run.
		'''
		if cls.sites is not None:
			for site in cls.sites:
				cls.sites[site].shutdownWebsite()

class Configuration():
	'''
	Methods collected into a class for grouping by functionality.
	The class isn't meant to be instantiated. It's a Helper.
	'''
	hsn2TestPath = "/tmp/tests"
	hsn2InstallPath = "/opt/hsn2"
	couchLogPath = "/var/log/couchdb"

	def __init__(self):
		'''
		Throws an Exception if instantiated.
		'''
		raise Exception("This class isn't meant to be instantiated.")

	@classmethod
	def getConf(cls, path):
		'''
		Read a configuration file into a list.
		@param path: The path to the file.
		@return: A list of strings.
		'''
		fileH = open(path, "r")
		conf = fileH.readlines()
		fileH.close()
		return conf

	@classmethod
	def getWorkflowName(cls, path):
		'''
		Read a configuration file into a list.
		@param path: The path to the file.
		@return: Workflow name.
		'''
		from xml.dom.minidom import parse
		name = parse(path).childNodes[0].getAttribute("name")
		if name == "":
			name = os.path.split(path)[1].replace(".hwl", "")
		return name

	@classmethod
	def setConf(cls, path, conf):
		'''
		Write a configuration file from a list of strings.
		@param path: The path to the file.
		@param conf: A list of strings.
		'''
		fileH = open(path, "w")
		fileH.writelines(conf)
		fileH.close()

	@classmethod
	def setWorkflowsFolder(cls, path):
		'''
		Change the workflow directory setting in the Framework configuration file.
		@param path: Directory containing workflows to add.
		'''
		if os.path.isdir(path):
			logging.info("Searching for .hwl files in %s" % path)
			for f in os.listdir(path):
				if re.search('\.hwl$', f) is not None:
					cls.setWorkflow(os.path.join(path, f))

	@classmethod
	def setWorkflow(cls, path, name = None):
		'''
		Change the workflow directory setting in the Framework configuration file.
		@param path: Full path to .hwl workflow file.
		@param name: Optional name for the workflow.
		'''
		if os.path.isfile(path):
			logging.info("Updating new workflow: %s" % path)
			if name is None:
				name = cls.getWorkflowName(path)
			Console.call("hc w u -f %s %s" % (path, name))

	@classmethod
	def setServices(cls, serviceList, confFile = "/etc/hsn2/framework.conf"):
		'''
		Change the workflow directory setting in the Framework configuration file.
		@param path: The new value of the workflow directory setting.
		@param confFile: Path to the configuration file.
		'''
		if os.path.isfile(confFile):
			Backup.backupFile(confFile)
		serviceList = ', '.join(serviceList)
		logging.info("Setting services to %s" % serviceList)
		conf = cls.getConf(confFile)
		pattern = re.compile(r"AMQP.services=.*")
		for i in range(len(conf)):
			match = pattern.match(conf[i])
			if match is not None:
				conf[i] = pattern.sub("AMQP.services=%s" % serviceList, conf[i], 1)
				break
		cls.setConf(confFile, conf)

	@classmethod
	def setConsoleConf(cls, host = "127.0.0.1", port = 5672, timeout = 4, confFile = "/etc/hsn2/console.conf"):
		'''
		Create a new configuration file for the console.
		@param host: The address of the broker (RabbitMQ)
		@param port: The port of the broker(RabbitMQ)
		@param timeout: Console command timeout in seconds.
		@param confFile: Path to the configuration file.
		'''
		if os.path.isfile(confFile):
			Backup.backupFile(confFile, copy = False)
		conf = cls.getConf(os.path.join(cls.hsn2TestPath, "hc.cnf.template"))
		for i in range(len(conf)):
			conf[i] = re.sub(r"{TIMEOUT}", "%d" % timeout, conf[i], 1)
			conf[i] = re.sub(r"{HOST}", "%s" % host, conf[i], 1)
			conf[i] = re.sub(r"{PORT}", "%d" % port, conf[i], 1)
		cls.setConf(confFile, conf)

	@classmethod
	def setCouchConf(cls, logPath = couchLogPath):
		'''
		Modify the couchdb configuration files. Set logging level to debug.
		@param logPath: The path where the logs should be created.
		'''
		if os.path.isdir(logPath):
			if os.path.isfile(os.path.join(logPath, "couch.log")):
				Backup.backupFile(os.path.join(logPath, "couch.log"), copy = False)
			if os.path.isfile(os.path.join(logPath, "couch_stdout.log")):
				Backup.backupFile(os.path.join(logPath, "couch_stdout.log"), copy = False)
			if os.path.isfile(os.path.join(logPath, "couch_stderr.log")):
				Backup.backupFile(os.path.join(logPath, "couch_stderr.log"), copy = False)
		else:
			os.makedirs(logPath)
		conf = cls.getConf("/etc/default/couchdb")
		for i in range(len(conf)):
			conf[i] = re.sub(r"COUCHDB_STDOUT_FILE.*", "COUCHDB_STDOUT_FILE=%s/%s" % (logPath, "couch_stdout.log"), conf[i], 1)
			conf[i] = re.sub(r"COUCHDB_STDERR_FILE.*", "COUCHDB_STDOUT_FILE=%s/%s" % (logPath, "couch_stderr.log"), conf[i], 1)
		cls.setConf("/etc/hsn2/console.conf", conf)
		conf = cls.getConf("/etc/couchdb/default.ini")
		pattern = re.compile(r"\s^level.*")
		for i in range(len(conf)):
			match = pattern.match(conf[i])
			if match is not None:
				conf[i] = pattern.sub("level=debug", conf[i], 1)
				break
		cls.setConf("/etc/couchdb/default.ini", conf)

	@classmethod
	def deleteCouchDB(cls, url = "http://localhost:5984", database = "hsn"):
		'''
		Deletes the specified couch database.
		@param url: location of the couchdb instance
		@param database: the name of the database that is to be cleared.
		'''
		try:
			deletion = getUrlHandle("%s/%s" % (url, database), method = "DELETE").readlines()
			logging.info("Deleting couchdb database: %s/%s - %s" % (url, database, ''.join(deletion).strip()))
		except urllib2.HTTPError as e:
			if e.code == 404:
				logging.info("Couchdb database not found at: %s/%s" % (url, database))
			else:
				raise e
		#logging.info("Creating couchdb database: %s/%s - %s" % (url,database, ''.join(getUrlHandle("%s/%s" % (url, database),method="PUT").readlines()).strip()))

	@classmethod
	def resetJobCounter(cls):
		pass
		'''
		Resets the job id counter.
		'''
		#path = "%s/framework/jobId.seq" % cls.hsn2InstallPath
		#if os.path.isfile(path):
		#	Backup.backupFile(path)
		#fh = open(path, "w")
		#fh.write("0")
		#fh.close()
		#logging.info("Resetting Job counter... Done")

	@classmethod
	def setHSN2InstallPath(cls, path):
		cls.hsn2InstallPath = path

	@classmethod
	def setHSN2TestPath(cls, path):
		cls.hsn2TestPath = path

	@classmethod
	def setCouchLogPath(cls, path):
		cls.couchLogPath = path

class TestHelp():
	agg = None

	def __init__(self, aggregateTo, suiteName, testName, loglevel = logging.DEBUG):
		try:
			aggregateTo = os.path.join(aggregateTo, suiteName, testName)
			self.agg = LogAggregator(aggregateTo)
			setupLogging(logPath = os.path.join(aggregateTo, "%s.log " % testName), logToStream = True, logLevel = loglevel)
			Backup.backupOldLogs()
			Backup.backupCouchDB("hsn", exception = False)
		except (BackupException, IOError, OSError) as e:
			Backup.restoreFiles()
			raise e

	def done(self):
		couchAggregate = False
		if ("couchdb", None) in Starter.inits or ("couchdb", "time to relax.\n") in Starter.inits:
			couchAggregate = True
		Starter.stopStartedInits()
		Website.shutdownWebsites()
		self.agg.aggregate(takeFrom = "/var/log/hsn2")
		if couchAggregate:
			self.agg.aggregate(takeFrom = "/var/log/couchdb")
		self.agg.aggregate("/var/log/rabbitmq", suffix = None)
		Backup.restoreFiles()
		setupLogging(logPath = None, logToStream = False)

class JobDetails():
	properties = {}

	def __init__(self, jobId = 1):
		'''
		Gathers all information about job from "hc j d".
		@param jobId: The id of the job about which the details will be gathered.
		'''
		self.jobId = jobId
		lines = Console.call("hc j d %s" % self.jobId)[1].split('\n')
		for line in lines:
			if re.search(r'^\s', line) is None:
				continue
			elif re.search(r'task_count', line) is None:
				ret = re.search(r'\s*(\S+)\s*(\S.*)', line) #\s*([A-Z]+)
				if ret is None:
					logging.warning("job details fail: %s" % line)
					continue
				logging.debug("job details: %s = %s" % (ret.group(1), ret.group(2)))
				self.properties[ret.group(1)] = '%s' % ret.group(2)
			else:
				ret = re.search(r'\s*task_count_(\S+)\s*(\d+)\/(\d+)', line)
				if ret is None:
					logging.error("job details fail: %s" % line)
					continue
				logging.debug("job details: task_count_%s = %s/%s" % (ret.group(1), ret.group(2), ret.group(3)))
				self.properties[ret.group(1)] = (ret.group(2), ret.group(3))

	def get(self, param):
		return self.properties[param]

	def __getitem__(self, param):
		return self.get(param)

import datetime
class JmeterSample():
	'''
	Used by JmeterLog class and not intended to be used directly.
	'''
	def __init__(self, label):
		self.start = time.time() * 1000 #datetime.datetime.now()
		self.label = label
		self.duration = 0
		self.success = "false"

	def stop(self):
		stop = time.time() * 1000
		self.duration = stop - self.start

	def setsuccess(self):
		self.success = "true"

	def setfailure(self):
		self.success = "false"

	def setDuration(self, duration):
		self.duration = duration

	def getDOMElement(self):
		doc = xml.dom.minidom.getDOMImplementation().createDocument(None, None, None)
		element = doc.createElement("httpSample")
		element.setAttribute("t", "%d" % self.duration)
		element.setAttribute("lt", "0")
		element.setAttribute("ts", "%d" % self.start)
		element.setAttribute("s", self.success)
		element.setAttribute("lb", self.label)
		element.setAttribute("rc", "200")
		element.setAttribute("rm", "OK")
		element.setAttribute("tn", "Thread Group 1-1")
		element.setAttribute("dt", "text")
		element.setAttribute("by", "9379")
		return element

class JmeterLog():
	'''
	Creates Jmeter alike log files.

	Important JMeter XML attributes:
	lb      Label
	s       Success flag (true/false) - i.e. false when job takes longer than accepted
	t       Elapsed time (milliseconds)
	ts      timeStamp (milliseconds since midnight Jan 1, 1970 UTC)

	Ignored JMeter XML attributes:
	by      Bytes (fixed size used)
	dt      Data type (always "text")
	lt      Latency = time to initial response (milliseconds) - not all	samplers support this (always 0)
	rc      Response Code (always 200)
	rm      Response Message (always "OK")
	tn      Thread Name (always "Thread Group 1-1")

	Unused JMeter XML attributes:
	de      Data encoding
	ec      Error count (0 or 1, unless multiple samples are aggregated)
	hn      Hostname where the sample was generated
	na      Number of active threads for all thread groups
	ng      Number of active threads in this group
	sc      Sample count (1, unless multiple samples are aggregated)
	
	Usage:
	log = JmeterLog()
	uid = uuid.uuid4()
	log.start("PerformanceTest", uid)
	# do anything you want to measure
	log.stop("PerformanceTest", uid)
	# assert anything, then:
	log.success("PerformanceTest", uid, True)
	# or:
	log.success("PerformanceTest", uid, False)
	# default is failure, so above isn't necessary
	log.addsample("PerformanceTest", uid) # for storing results
	'''
	def __init__(self):
		self.dom = xml.dom.minidom.parseString('<testResults version="1.2"></testResults>')
		self.samples = {}

	def start(self, label, uid):
		'''
		@param label: label that will be used for given sample, i.e. test name
		@param uid: unique ID, i.e. created by uuid.uuid4()
		'''
		if "%s%s" % (label, uid) in self.samples.keys():
			raise AlreadyExistsException()
		self.samples["%s%s" % (label, str(uid))] = JmeterSample(label)

	def stop(self, label, uid, duration = None):
		'''
		@param label: should match the label used for start method
		@param uid: should match the uid used for start method
		@param duration: duration in miliseconds if it is being set manually else None 
		'''
		if duration is None:
			self.samples["%s%s" % (label, uid)].stop()
		else:
			self.samples["%s%s" % (label, uid)].setDuration(duration)

	def success(self, label, uid, success):
		'''
		@param label: should match the label used for start method
		@param uid: should match the uid used for start method
		@param success: True/False
		'''
		if success:
			self.samples["%s%s" % (label, uid)].setsuccess()
		else:
			self.samples["%s%s" % (label, uid)].setfailure()

	def addsample(self, label, uid):
		'''
		Used for storing single test result a.k.a. sample.
		@param label: should match the label used for start method
		@param uid: should match the uid used for start method
		'''
		self.dom.childNodes[0].appendChild(self.samples["%s%s" % (label, uid)].getDOMElement())

	def toxml(self):
		return self.dom.toxml()

	def toprettyxml(self):
		return self.dom.toprettyxml()

if __name__ == "__main__":
	setupLogging(logPath = None, logToStream = True, logLevel = logging.INFO)
	Configuration.setHSN2TestPath("/tmp/tests")
	try:
		Backup.backupOldLogs()
		Backup.backupCouchDB("hsn", exception = False)
		agg = LogAggregator(putTo = "/var/log/hsn2/c")
	except (BackupException, IOError, OSError) as e:
		Backup.restoreFiles()
		raise e

	setupLogging(logPath = "/var/log/hsn2/test.log", logToStream = True, logLevel = logging.DEBUG)
	logging.info("Testing commons")
	try:
		Configuration.resetJobCounter()
		Configuration.setConsoleConf("127.0.0.1", 5672, 4)
		Configuration.setCouchConf()
		Starter.isRunning("/var/run/couchdb/couchdb.pid")
		Configuration.setWorkflowsFolder("/tmp/tests/workflows/a")
		Website("/tmp/tests", 81)
		Website("/var/log", 82)
		Website("/var/log", 82)
		Starter.initCouchDB()
		Starter.initRabbitMQ()
		Starter.initStart("hsn2-framework")
		Starter.initStart("hsn2-object-store-mongodb")
		Starter.initStart("hsn2-data-store")
		Starter.initStart("hsn2-swf-cve")
		Starter.initStart("hsn2-js-sta")
		Starter.initStart("hsn2-webclient")
		Starter.initStart("hsn2-file-feeder")
		Starter.initStart("hsn2-swfScanner")
		Starter.initStart("hsn2-clamavNugget")
		Starter.initStart("hsn2-pdfFox")
		Starter.initStart("hsn2-archiveInflate")
		Starter.initStart("hsn2-mimeRecognizer")
		Starter.waitCouchDB()
		Configuration.deleteCouchDB()
		Starter.initStart("hsn2-reporter")

	except Exception as e:
		logging.error(e)
	finally:
		Starter.stopStartedInits()
		Website.shutdownWebsites()
		agg.aggregate(takeFrom = "/var/log/hsn2")
		agg.aggregate(takeFrom = "/var/log/couchdb")
		Backup.restoreFiles()

#_start_jar()
#{
#	java -jar $INSTALL_PATH/$1/hsn2-$1.jar `cat $TEST_DIR/params/$1` &
#	sleep 1
#}
#
#_stop_jar()
#{
#	echo -n "Stopping service $1... "
#	ID=`ps ax | grep java | grep "$1" | sed 's/^ *//' | cut -d' ' -f1`
#
#	if [ -z "$ID" ]; then
#		echo -n "not working... "
#	else
#		kill $ID
#		sleep 1
#	fi
#	#sleep 3;
#	echo "DONE"
#}

#_start_all()
#{
#	_start_initd "framework"
#
#	_start_initd "object-store"
#	_start_initd "data-store"
#	_start_initd "file-feeder"
#	_start_initd "webclient"
#	_start_initd "swf-cve"
#	_start_initd "js-sta"
#	_start_initd "shell-scdbg"
#	_start_initd "reporter"
#}
#
#_stop_all()
#{
#	_stop_initd "object-store"
#	_stop_initd "data-store"
#	_stop_initd "file-feeder"
#	_stop_initd "webclient"
#	_stop_initd "swf-cve"
#	_stop_initd "js-sta"
#	_stop_initd "shell-scdbg"
#	_stop_initd "reporter"
#
#	_stop_initd "framework"
#}

#_say_hello()
#{
#	echo "The $1() test has started..."
#}
#
#_say_goodbye()
#{
#	echo "The $1() test has finished."
#}
