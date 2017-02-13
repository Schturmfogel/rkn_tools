#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from peewee import Proxy, Model, CharField, TextField, DateField, DateTimeField, IntegerField, BigIntegerField, \
				   BooleanField, SqliteDatabase, PostgresqlDatabase, ForeignKeyField

logger = logging.getLogger(__name__)
database_proxy = Proxy()


class Dump(Model):
	param = CharField(primary_key=True, max_length=255, null=False)
	value = TextField(null=False)

	class Meta(object):
		database = database_proxy


class Item(Model):
	content_id = BigIntegerField(null=False, index=True)
	include_time = DateTimeField(null=False)
	urgency_type = IntegerField(null=False, default=0)
	entry_type = IntegerField(null=False)
	block_type = TextField(null=False, default='default')
	hash_record = TextField(null=False)
	decicion_date = DateField(null=False)
	decicion_num = TextField(null=False)
	decision_org = TextField(null=False)
	add = BigIntegerField(null=False, index=True)
	purge = BigIntegerField(null=True, index=True)

	class Meta(object):
		database = database_proxy


class IP(Model):
	item = ForeignKeyField(Item, on_delete='CASCADE', on_update='CASCADE', index=True)
	content_id = BigIntegerField(null=False, index=True)
	ip = TextField(null=False, index=True)
	mask = IntegerField(null=False, default=32)
	add = BigIntegerField(null=False, index=True)
	purge = BigIntegerField(null=True, index=True)
	# version = IntegerField(null=False, default=4)   # ip protocol version (4 or 6)
	# source = TextField(null=False)   # dump or resolver source

	class Meta(object):
		database = database_proxy


class DNSResolver(Model):
	domain = TextField(null=False)
	ip = TextField(null=False, index=True)
	mask = IntegerField(null=False, default=32)
	version = IntegerField(null=False, default=4)
	add = BigIntegerField(null=False, index=True)
	purge = BigIntegerField(null=True, index=True)

	class Meta(object):
		database = database_proxy


class URL(Model):
	item = ForeignKeyField(Item, on_delete='CASCADE', on_update='CASCADE', index=True)
	content_id = BigIntegerField(null=False, index=True)
	url = TextField(null=False, index=True)
	add = BigIntegerField(null=False, index=True)
	purge = BigIntegerField(null=True, index=True)

	class Meta(object):
		database = database_proxy


class History(Model):
	request_code = TextField(null=False)
	dump = BooleanField(null=False, default=False)
	resolver = BooleanField(null=False, default=False)
	date = DateTimeField(null=False)

	class Meta(object):
		database = database_proxy

def init_db(cfg):
	path_py = str(os.path.dirname(os.path.abstract(__file__)))
	login = cfg.User()
	password = cfg.Password()
	host = cfg.Host()
	port = cfg.Port()
	name_db = cfg.Name()
	type_db = int(cfg.Type())
	blacklist_db = False

	if type_db == 0:
		blacklist_db = SqliteDatabase(path_py + '/' + name_db + '.db', pragmas=(('foreign_keys, 1'),))
		database_proxy.initialize(blacklist_db)
		database_proxy.create_tables([Dump, Item, IP, DNSResolver, Domain, URL, History], safe=True)
		init_dump_tbl()
		logger.info('Check database: SQLite OK')

	elif type_db == 1:
		import psycopg2
		from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

		db = psycopg2.connect(dbname='postgres', host=host, port=port, user=login, password=password)
		db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
		cursor = db.cursor()
		check_db = "SELECT datname FROM pg_catalog.pg_database WHERE lower(datname) = lower('" + name_db + "')"
		cursor.execute(check_db)
		db_exist_flag = cursor.fetchone()
		if not db_exist_flag:
			create_db = "CREATE DATABASE " + name_db + " WITH ENCODING = 'UTF8' " \
													   "LC_COLLATE = 'ru_RU.UTF-8' "\
													   "LC_CTYPE = 'ru_RU.UTF-8'"
			cursor.execute(create_db)
			privileges_set = "GRANT ALL PRIVILEGES ON DATABASE " + name_db + " TO " + login
			cursor.execute(privileges_set)
		cursor.close()
		blacklist_db = PostgresqlDatabase(name_db, host=host, port=port, user=login, password=password)
		database_proxy.initialize(blacklist_db)
		init_dump_tbl()
		logger.info('Check database: PostgreSQL OK')

	else:
		logger.info('Wrong DB type. Check configuration.')
		exit()

	return blacklist_db

def init_dump_tbl():
	try:
		Dump.get(Dump.param == 'lastDumpDate')
	except Dump.DoesNotExist:
		Dump.create(param='lastDumpDate', value='1325376000')

	try:
		Dump.get(Dump.param == 'lastDumpDateUrgently')
	except Dump.DoesNotExist:
		Dump.create(param='lastDumpDateUrgently', value='1325376000')

	try:
		Dump.get(Dump.param == 'lastAction')	
	except Dump.DoesNotExist:
		Dump.create(param='lastAction', value='get_last_dump_date')

	try:
		Dump.get(Dump.param == 'lastResult')
	except Dump.DoesNotExist:
		Dump.create(param='lastResult', value='default')

	try:
		Dump.get(Dump.param == 'lastCode')
	except Dump.DoesNotExist:
		Dump.create(param='lastCode', value='default')

	try:
		Dump.get(Dump.param == 'dumpFormatVersion')
	except Dump.DoesNotExist:
		Dump.create(param='dumpFormatVersion', value='2.2')

	try:
		Dump.get(Dump.param == 'webServiceVersion')
	except Dump.DoesNotExist:
		Dump.create(param='webServiceVersion', value='3')

	try:
		Dump.get(Dump.param == 'docVersion')
	except Dump.DoesNotExist:
		Dump.create(param='docVersion', value='4')