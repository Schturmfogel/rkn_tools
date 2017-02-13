#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import logging
import os.path
import re
import time
import urllib
import zipfile
from base64 import b64decode
from datetime import datetime
from db import Dump, Item, IP, Domain, URL, History
from lxml.etree import ElementTree
from peewee import fn
from rkn_info import RKNInfo

logger = logging.getLogger(__name__)


class Core(object):
	def __init__(self, transact, cfg):
		self.path_py = str(os.path.dirname(os.path.abspath(__file__)))
		self.transact = transact
		self.session = RKNInfo()
		self.update_dump = self.session.get_last_dump_date_ex()
		self.cfg = cfg
		self.code = None
		self.code_id = None

	@staticmethod
	def date_time_xml_to_db(date_time_xml):
		date_time_db = date_time_xml.replace('T', ' ')
		return date_time_db

	def check_service_upd(self):
		msg = ''

		logger.info('Current versions: webservice: %s, dump: %s, doc: %s',
					Dump.get(Dump.param == 'webServiceVersion').value,
					Dump.get(Dump.param == 'dumpFormatVersion').value,
					Dump.get(Dump.param == 'docVersion').value)
		if self.update_dump.webServiceVersion != Dump.get(Dump.param == 'webServiceVersion').value:
			logger.warning('New webservice: %s', self.update_dump.webServiceVersion)
			msg = msg + 'Current webservice:' + Dump.get(Dump.param == 'webServiceVersion').value + \
						'\nNew webservice: ' + self.update_dump.webServiceVersion + '\n\n'
			Dump.update(value=self.update_dump.webServiceVersion).where(Dump.param == 'webServiceVersion').execute()

		if self.update_dump.dumpFormatVersion != Dump.get(Dump.param == 'dumpFormatVersion').value:
			logger.warning('New dumpFormatVersion: %s', self.update_dump.dumpFormatVersion)
			msg = msg + 'Current dumpFormatVersion:' + Dump.get(Dump.param == 'dumpFormatVersion').value + \
						'\nNew dumpFormatVersion: ' + self.update_dump.dumpFormatVersion + '\n\n'
			Dump.update(value=self.update_dump.dumpFormatVersion).where(Dump.param == 'dumpFormatVersion').execute()

		if self.update_dump.docVersion != Dump.get(Dump.param == 'docVersion').value:
			logger.warning('New docVersion: %s', self.update_dump.docVersion)
			msg = msg + 'Current docVersion:' + Dump.get(Dump.param == 'docVersion').value + \
						'\nNew docVersion: ' + self.update_dump.docVersion + '\n\n'
			Dump.update(value=self.update_dump.docVersion).where(Dump.param == 'docVersion').execute()

		return msg

	def check_new_dump(self):
		logger.info('Check if dump.xml has updates since last sync.')

		if self.cfg.lastDumpDateUrgently() and not self.cfg.lastDumpDate():
			last_date_dump = self.update_dump.lastDumpDateUrgently // 1000
			current_date_dump = int(Dump.get(Dump.param == 'lastDumpDateUrgently').value)
		elif self.cfg.lastDumpDate() and not self.cfg.lastDumpDateUrgently():
			last_date_dump = self.update_dump.lastDumpDate // 1000
			current_date_dump = int(Dump.get(Dump.param == 'lastDumpDate').value)
		else:
			last_date_dump = max(self.update_dump.lastDumpDate // 1000, self.update_dump.lastDumpDateUrgently // 1000)
			current_date_dump = max(int(Dump.get(Dump.param == 'lastDumpDate').value),
									int(Dump.get(Dump.param == 'lastDumpDateUrgently').value))

		logger.info('Current date: lastDumpDate: %s, lastDumpDateUrgently: %s',
					datetime.fromtimestamp(int(Dump.get(Dump.param == 'lastDumpDate').value)).strftime('%Y-%m-%d %H:%M:%S'),
					datetime.fromtimestamp(int(Dump.get(Dump.param == 'lastDumpDateUrgently').value)).strftime('%Y-%m-%d %H:%M:%S'))
		logger.info('Last date: lastDumpDate: %s, lastDumpDateUrgently: %s'.
					datetime.fromtimestamp(int(self.update_dump.lastDumpDate // 1000)).strftime('%Y-%m-%d %H:%M:%S'),
					datetime.fromtimestamp(int(self.update_dump.lastDumpDateUrgently // 1000)).strftime('%Y-%m-%d %H:%M:%S'))
		if last_date_dump != current_date_dump or Dump.get(Dump.param == 'lastResult').value == 'Error':
			logger.info('New dump is available.')
			Dump.update(value='getLastDumpDate').where(Dump.param == 'lastAction').execute()
			Dump.update(value='NewDump').where(Dump.param == 'lastResult').execute()
			return True
		else:
			logger.info('Dump date without changes.')
			Dump.update(value='getLastDumpDate').where(Dump.param == 'lastAction').execute()
			Dump.update(value='lastDump').where(Dump.param == 'lastResult').execute()
			return False

	def send_request(self):
		