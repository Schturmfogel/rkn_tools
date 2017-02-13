#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import suds.client
from base64 import b64encode

API_URL = "http://vigruzki.rkn.gov.ru/services/OperatorRequest/?wsdl"


class RKNInfoException(RuntimeError):
	pass


class RKNInfo(object):

	def __init__(self):
		self.client = suds.client.Client(API_URL)

	def get_last_dump_date_ex(self):
		result = self.client.service.get_last_dump_date_ex()
		return result

	def get_last_dump_date(self):
		result = self.client.service.get_last_dump_date()
		return result

	def send_request(self, request_file, signature_file, version_num='2.2'):
		if not os.path.exists(request_file):
			raise RKNInfoException('No request file')
		if not os.path.exists(signature_file):
			raise RKNInfoException('No signature file')

		with open(request_file, "rb") as f:
			data = f.read()

		xml = b64encode(data)
		xml = xml.decode('utf-8')

		with open(signature_file, "rb") as f:
			data = f.read()

		cert = b64encode(data)
		cert = cert.decode('utf-8')

		result = self.client.service.send_request(xml, cert, version_num)
		return dict((k, v) for (k, v) in result)

	def get_result(self, code):
		result = self.client.service.get_result(code)
		return dict((k, v) for (k, v) in result)
