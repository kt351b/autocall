#!/usr/bin/python3.4
# coding: utf-8
# REPLACE ALL XXX... with your data in:
# DB definions, AMI definions, Dialplan definions

import time
from sys import argv
from asterisk.ami import AMIClient
from asterisk.ami import SimpleAction
import logging
from logging.handlers import WatchedFileHandler
import pymysql
from pymysql.err import IntegrityError
from pymysql.err import OperationalError
# pymysql.install_as_MySQLdb()
import gc

gc.enable()
#gc.set_debug(gc.DEBUG_LEAK)

#-- DB definions:
db_name = 'autocall'
host = 'XXX.XXX.XXX.XXX'
user = 'USERMANE'
passwd = 'PASSWORD'
table_parse = 'to_parse'

#-- AMI definions:
aster_server = 'XXX.XXX.XXX.XXX'
ami_port = 5038
ami_user = 'USER_FROM_/etc/asterisk/manager.conf'
ami_pass = 'PASSWORD_FROM_/etc/asterisk/manager.conf'

#-- Dialplan definions:
trunk = 'SIP/XXXXXXXXX/'
context = '9004'
#context = 'autocall'
exten = 's'
#callerid = 'YOUR_CALLER_ID'

#-- Code definions:
in_call = 5

# ----- logger settings:
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# ---- syslog file settings:
fh = logging.handlers.WatchedFileHandler('/var/log/dialer.log')
# For log-file output use logging.INFO to write to log
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
# ---- terminal log output settings:
# --- How to use DEBUG mode:
# --- For terminal output use logging.debug.
# --- Uncomment this line for debug only! Don't forget to comment this line back:
logger.setLevel(logging.DEBUG)
# --- And comment this line:
#logger.setLevel(logging.INFO)
# --- And don't forget to get it all back :)
# --- End of DEBUG mode block
ch = logging.StreamHandler()
ch.setFormatter(formatter)
# ------------------------------
logger.addHandler(fh)
#logger.addHandler(ch)
#-   COMMENTED channelhandler logging

#def ami_connect():
#	# AMI connection. username and secret create in /etc/asterisk/manager.conf:
#	client = AMIClient(address=aster_server, port=ami_port)
#	client.login(username=ami_user, secret=ami_pass)
#	return(client)

def db_connect():
	try:
		db = pymysql.connect(host=host, user=user, passwd=passwd, db=db_name, charset='utf8mb4')
		cursor = db.cursor()
		return cursor, db
	except pymysql.err.OperationalError:
		i = 1
		while i < 3:
			try:
				db = pymysql.connect(host=host, user=user, passwd=passwd, db=db_name, charset='utf8mb4')
				cursor = db.cursor()
				return cursor, db
			except (pymysql.err.OperationalError, pymysql.InterfaceError):
				logging.debug("Maybe no connection to DB while db_connect func. Reconnection. Attempt - {}".format(i))
				logging.info("Maybe no connection to DB while db_connect func. Reconnection. Attempt - {}".format(i))
				i+=1
				time.sleep(2)
				continue
		logging.debug("No connection to DB while db_connect func. Check DB definitions. Exiting!")
		logging.info("No connection to DB while db_connect func. Check DB definitions. Exiting!")
		raise SystemExit(1)

def get_code(cursor, db):
	try:
		sql = """SELECT id, number, record FROM `%(table)s` WHERE code = 0""" %{"table": table_parse}
		cursor.execute(sql)
		for row in cursor:
			id, number, shablon = row
			logging.debug("Number - {} with id - {} and code = 0:".format(number, id) )
			logging.info("Number - {} with id - {} and code = 0:".format(number, id) )
			sql_del = """UPDATE %(table)s SET code = '%(in_call)d' where id = %(id)s""" % {
				"table": table_parse,
				"in_call": in_call,
				"number": number,
				"id": id}
			cursor.execute(sql_del)
			db.commit()
			ami_action(number, shablon, cursor, db, id)
			time.sleep(1)
		gc.collect()
	except pymysql.err.OperationalError:
		db_connect()
	except (pymysql.err.ProgrammingError, pymysql.err.DataError, pymysql.err.IntegrityError) as error:
		logging.debug("Something went wrong with query!")
		logging.info("Something went wrong with query!")
		logging.debug(error)
		logging.info(error)

def ami_action(number, shablon, cursor, db, id):
	Channel = trunk+number
	logging.debug("Channel - {}".format(Channel) )
	#logging.info("Channel - {}".format(Channel) )
	# Variable=id=3
	var = "VAR="+str(shablon)+str(id)
	# Connect to AMI
	client = AMIClient(address=aster_server, port=ami_port)
	client.login(username=ami_user, secret=ami_pass)

	action = SimpleAction(
			'Originate',
			 Channel=Channel,
			 Exten=exten,
			 Context=context,
			 Priority=1,
			 CallerID=number,
			 Variable=var,)
	try:
		client.send_action(action)
		client.logoff()
	except Exception as ex:
		print(ex)


def initial():
		while True:
			cursor, db = db_connect()
			get_code(cursor, db)

if __name__ == '__main__':
    initial()
