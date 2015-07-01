#!/usr/bin/python
# Cuckoo Sandbox - Automated Malware Analysis
# Copyright (C) 2010-2012  Claudio "nex" Guarnieri (nex@cuckoobox.org)
# http://www.cuckoobox.org
#
# This file is part of Cuckoo.
#
# Cuckoo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cuckoo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

import os
import sys
import logging
import tarfile
from time import sleep
from threading import Thread

from cuckoo.config.config import CuckooConfig
from cuckoo.config.constants import *
from cuckoo.core.db import CuckooDatabase

sys.path.append("/opt/hsn2/python/commlib")
import loggingSetup

class Analysis(Thread):
	"""
	This class handles the whole analysis process.
	"""
	def __init__(self, task = None, log = logging.getLogger()):
		Thread.__init__(self)
		self.task = task
		self.db = None
		self.dst_filename = None
		self.log = log

	def _save_results(self, src, dst):
		"""
		Saves analysis results from source to destination path.
		@param src: source path
		@param dst: destination path
		"""
		log = self.log

		if not os.path.isfile(src):
			log.error("The folder \"%s\" doesn't exist." % src)
			return False

		if not os.path.exists(dst):
			try:
				os.makedirs(dst)
			except (IOError, os.error), why:
				log.error("Unable to create directory \"%s\": %s" % (dst, why))
				return False
		else:
			log.error("The folder \"%s\" already exists. It should be used " \
					  "for storing results of task with ID %s. " \
					  "Have you deleted Cuckoo's database?"
					  % (dst, self.task["id"]))
			return False
		try:
			tar = tarfile.open(src, "r:gz")
			tar.extractall(path = dst)
			total = len(tar.getmembers())
			log.debug("Extracted %d elements" % total)
		except:
			log.error("Trouble extracting '%s'" % src)
			return False
		return True

	def run(self):
		"""
		Handles the analysis process and invokes all required procedures.
		"""
		log = logging.getLogger()
		success = True
		self.task["custom"] = str(self.task["custom"])
		self.db = CuckooDatabase()

		# Generate analysis results storage folder path with current task id.
		results_path = CuckooConfig().get_analysis_results_path()
		save_path = os.path.join(results_path, str(self.task["id"]))

		if (self.task["custom"] == "sleep"):
			import time
			# sleep longer than default timeout of hsn2-cuckoo
			time.sleep(905)
		# Additional check to verify that the are not saved results with the
		# same task ID.
		if os.path.exists(save_path):
			log.error("There are already stored results for current task " \
					  "with ID %d at path \"%s\". Abort."
					  % (self.task["id"], save_path))
			self.db.complete(self.task["id"], False)
			return False

		# Check if target file exists.
		log.debug(os.path.exists(self.task["custom"]))
		if not os.path.exists(self.task["custom"]):
			log.error("Cannot find custom file \"%s\". Abort."
					  % self.task["custom"])
			self.db.complete(self.task["id"], False)
			return False

		# Check if target is a directory.
		if os.path.isdir(self.task["custom"]):
			log.error("Specified target \"%s\" is a directory. Abort."
					  % self.task["custom"])
			self.db.complete(self.task["id"], False)
			return False

		# 4. Extract appropriate log archive as mock logs analysis results
		#    Modified _save_results so that it extracts the tar file passed in target
		self._save_results(self.task["custom"], save_path)

		# 5. Update task in database with proper status code.
		if success:
			self.db.complete(self.task["id"], True)
		else:
			self.db.complete(self.task["id"], False)
		log.info("Analyis completed.")

		return True

#				I have malwares for
#		  .---.	breakfast!
#		 /   6_6	   _	   .-.
#		 \_  (__\	 ("\	 /.-.\
#		 //   \\	   `\\   //   \\
#		((	 ))		\`-`/	 \'-')
#  =======""===""=========="""======="""===
#		   |||
#			|
def main():
	# Mock analysis Execution Flow:
	# 1.  Connect to database
	# 2.  Acquire task from database
	# 3.  Lock task
	# 4.  Extract appropriate log archive as mock logs analysis results
	# 5. Update task's status in database
	running = True
	log = logging.getLogger()

	# Loop until the end of the world.
	while running:
		db = CuckooDatabase()
		task = db.get_task()
		if not task:
			log.debug("No tasks pending.")
			sleep(1)
			continue

		log.info("Acquired analysis task for target \"%s\"." % task["target"])

		# 3. Lock acquired task. If it doesn't get locked successfully I
		# need to abort its execution.
		if not db.lock(task["id"]):
			log.error("Unable to lock task with ID %d." % task["id"])
			sleep(1)
			continue

		analysis = Analysis(task)
		analysis.setName(task["id"])
		analysis.log = log
		analysis.start()
		sleep(1)

	return



if __name__ == "__main__":
	loggingSetup.setupLogging(logPath = "/var/log/hsn2/cuckoo-mock.log", logToStream = True)
	try:
		main()
	except KeyboardInterrupt:
		sys.exit()
	except:
		pass

