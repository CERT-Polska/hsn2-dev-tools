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
Created on 19-04-2012

@author: wojciechm
'''
import sys
from hsn2_commons.hsn2taskprocessor import HSN2TaskProcessor
from hsn2_commons.hsn2taskprocessor import ParamException, ProcessingException
from hsn2_commons.hsn2osadapter import ObjectStoreException
from hsn2_commons.hsn2dsadapter import DataStoreException
import hsn2_commons.hsn2objectwrapper as ow
from hsn2_commons.hsn2service import HSN2Service
from hsn2_commons.hsn2service import startService
import os
import logging

class HSN2TestFeederProcessor(HSN2TaskProcessor):

	def taskProcess(self):
		filepath = None
		jobId = self.currentTask.job
		taskId = self.currentTask.task_id
		for param in self.currentTask.parameters:
			if param.name == "uri":
				filepath = param.value
				continue
		if filepath is None:
			raise ParamException("No file path passed.")
		try:
			objects = ow.toObjectsFromJSON(filepath, True)
			objects2 = list()
			skipped = 0
			for obj in objects:
				passed = True
				for attr in obj.getTypeStore().iteritems():
					logging.info(attr)
					if attr[1] == "BYTES":
						logging.info("got %s" % attr[0])
						key = getattr(obj,attr[0]).getKey()
						if isinstance(key, str) or isinstance(key, unicode):
							if os.path.exists(key):
								obj.addBytes(attr[0],long(self.dsAdapter.putFile(key, self.currentTask.job)))
							else:
								logging.warn("File not found.")
								passed = False
				if passed:
					objects2.append(obj)
				else:
					skipped += 1
			newObjIds = self.osAdapter.objectsPut(jobId,taskId,objects2)
			self.newObjects.extend(newObjIds)
		except IOError as e:
			raise ParamException("IOError - %s." % e)
			#raise ParamException("File '%s' not found." % filepath)
		except ValueError as e:
			raise ParamException("Trouble processing file - '%s'" % e.message)

		return ["Skipped %d objects" % skipped]


if __name__ == '__main__':
	startService(HSN2Service,HSN2TestFeederProcessor)
