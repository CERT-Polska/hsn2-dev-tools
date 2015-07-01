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


import datetime
import logging
import os
import random
import re
import select
import signal
import shutil
import socket
import sys
import threading
import time

sys.path.append("/opt/hsn2/python/commlib")
from hsn2service import HSN2Service, startService
from multiprocessing import Process

'''
Created on 2012-06-04

@author: pawelch
'''
class HSN2CaptureHPCMockProcessor(Process):
	def __init__(self,connector,datastore,serviceName,serviceQueue,objectStoreQueue,**extra):
		Process.__init__(self)
		self.serviceName = serviceName

		self.host = ''
		self.port = 31337
		self.backlog = 5
		self.size = 1024
		self.server = None
		self.threads = []
		self.running = False
		logging.debug("reading sample logs")
		self.urls = parselog("/tmp/tests/resources/logs/capture-hpc/output.log")

	def open_socket(self):
		try:
			self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server.bind((self.host,self.port))
			self.server.listen(self.backlog)
		except socket.error, (val, msg):
			if self.server:
				self.server.close()
			print "Could not open socket:", msg
			sys.exit(1)

	def run(self):
		signal.signal(signal.SIGTERM, self.process_signal)
		signal.signal(signal.SIGINT, self.process_signal)
		signal.signal(signal.SIGQUIT, self.process_signal)

		self.open_socket()
		sinput = [self.server]
		self.running = True
		while self.running:
			try:
				rlist, wlist, xlist = select.select(sinput,[],[])
				for s in rlist:
					if s == self.server:
						c = HSN2CaptureHPCMockResponder(self.server.accept(),self.urls)
						c.daemon = True
						c.start()
						self.threads.append(c)
			except:
				self.stop()

		print "stopping gracefully: closing socket server..."
		self.server.close()
		print "stopping gracefully: closing threads / waiting for clients for disconnecting (closing socket)"
		for c in self.threads:
			c.join()
		exit(0)

	def stop(self):
		self.running = False

	def process_signal(self, sig, stack):
		if sig in (signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
			self.stop()

class HSN2CaptureHPCMockResponder(threading.Thread):
	def __init__(self,(client,address),urls):
		threading.Thread.__init__(self)
		self.client = client
		self.address = address
		self.size = 1024
		self.urls = urls

	def __processurl(self, url, jobid, reallogs):
		'''
		Method mimics URL processing by adding proper lines to capture-hpc log
		'''
		if not os.path.exists("/tmp/hpc"):
			logging.debug("Creating /tmp/hpc")
			os.makedirs("/tmp/hpc")
		logdata = defaultURL['1']
		if url in defaultURL:
			logdata = defaultURL[url]
		if reallogs:
			rjobid = random.sample(self.urls[url], 1)[0]
			logdata = self.urls[url][rjobid]
		for entry in logdata:
			entrytime = datetime.datetime.now()
			logline = "%s %s %s %s %s %s\n" % (
																				entrytime.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3],
																				entry.ip,
																				entry.processing,
																				entry.status,
																				jobid,
																				url
																				)
			with open("/tmp/hpc/url.log", "a") as f:
				f.write(logline)
			logging.debug("saved to /tmp/hpc/url.log: %s" % logline.rstrip('\n'))
			processingtime = random.uniform(0.5, 1) * entry.duration
			if processingtime > 90:
				processingtime = 60
			logging.debug("wait time before changing status: %d seconds" % processingtime)

			if entry.log is not None or entry.zip is not None:
				if not os.path.exists("/tmp/hpc/changes"):
					#logging.debug("Creating /tmp/changes")
					os.makedirs("/tmp/hpc/changes")
			if entry.log is not None:
				shutil.copyfile(entry.log, "/tmp/hpc/changes/%s_%s.log" % (jobid, entrytime.strftime("%d%m%Y_%H%M%S")))
			if entry.zip is not None:
				shutil.copyfile(entry.zip, "/tmp/hpc/changes/%s_%s.zip" % (jobid, entrytime.strftime("%d%m%Y_%H%M%S")))

			time.sleep(processingtime)
		logging.debug("finished with %s" % url)

	def run(self):
		running = True
		while running:
			data = self.client.recv(self.size)
			if data:
				m = re.search('addurl\s(\S+)\s(\d+)', data)
				'''
				jobs are added only for correct command syntax:
					addurl<whitespace>url<whitespace>jobid
				'''
				if m is not None:
					url = m.group(1)
					jobid = m.group(2)
					reallogs = False
					if url in self.urls:
						logging.debug("URL found in real capture-hpc logs: %s. They will be used to create similar logs" % url)
						reallogs = True
					else:
						logging.debug("URL not found in real capture-hpc logs: %s. Using defaults for log generation." % url)
					self.__processurl(url, jobid, reallogs)
					# TODO: remove this line after debug in socket client is not required
					self.client.send(data)
				else:
					logging.debug("Bad command received: %s" % data)
			else:
				self.client.close()
				running = False

class LogEntry:
	def __init__(self, duration, date, ip, processing, status, jobid):
		self.duration = duration
		self.date = date
		self.ip = ip
		self.processing = processing
		self.status = status
		self.jobid = jobid
		self.zip = None
		self.log = None
		if status == "VISITING" and date is not None:
			zip = "/tmp/tests/resources/logs/capture-hpc/changes/%s_%s.zip" % (self.jobid, self.date.strftime("%d%m%Y_%H%M%S"))
			log = zip[:-3] + "log"
			'''
			if self.jobid in ["29", "30", "31", "32", "34", "61", "70", "93"]:
				logging.debug("Tried to find %s_%s.log for job %s" % (self.jobid, self.date.strftime("%d%m%Y_%H%M%S"), self.jobid))
			'''
			if os.path.isfile(log):
				#logging.debug("Found %s file associated to job %s" % (log, self.jobid))
				self.log = log
			if os.path.isfile(zip):
				#logging.debug("Found %s file associated to job %s" % (zip, self.jobid))
				self.zip = zip

# date and jobid not used, so set to None - these attributes are used only for entries which have any log/zip files attached
defaultURL = {
						'1': [
								LogEntry(30, None, '0.0.0.0', 'T', 'QUEUED', None),
								LogEntry(5, None, '10.1.1.3', 'T', 'SENDING', None),
								LogEntry(30, None, '10.1.1.3', 'T' , 'VISITING', None),
								LogEntry(0, None, '10.1.1.3', 'T' , 'VISITED', None),
								LogEntry(0, None, '10.1.1.3', 'F' , 'BENIGN', None)
								],
						'http://www.test1retry.com/': [
								LogEntry(30, None, '0.0.0.0', 'T', 'QUEUED', None),
								LogEntry(5, None, '10.1.1.7', 'T', 'SENDING', None),
								LogEntry(5, None, '10.1.1.7', 'T' , 'VISITING', None),
								LogEntry(30, None, '10.1.1.7', 'T' , 'NETWORK_ERROR-408', None),
								LogEntry(5, None, '10.1.1.4', 'T', 'SENDING', None),
								LogEntry(30, None, '10.1.1.4', 'T' , 'VISITING', None),
								LogEntry(0, None, '10.1.1.4', 'T' , 'VISITED', None),
								LogEntry(0, None, '10.1.1.4', 'F' , 'BENIGN', None)
								]
						}

def parselog(path=None):
	'''
	Reads original HSN2 Capture HPC logs and produces similar output for mock service.
	'''
	urls = {} # dictionary with process data for each URL
	if path is None:
		path = "/tmp/hpc/url.log"
	log = open(path, "rU")
	for line in log:
		parselogline(line, urls)
	log.close()
	return urls

def parselogline(line, urls):
	date, time, ip, processing, status, jobid, url = line.split()
	# TODO: update, when #7092 is implemented to capture-hpc
	date = datetime.datetime.strptime(date + " " + time, "%d.%m.%Y %H:%M:%S.%f")
	duration = 0
	if url not in urls:
		urls[url] = {}
	if jobid not in urls[url]:
		urls[url][jobid] = []
	else:
		previous = len(urls[url][jobid]) - 1
		urls[url][jobid][previous].duration = (date - urls[url][jobid][previous].date).total_seconds()
	urls[url][jobid].append(LogEntry(duration, date, ip, processing, status, jobid))

if __name__ == "__main__":
	startService(HSN2Service,HSN2CaptureHPCMockProcessor)
