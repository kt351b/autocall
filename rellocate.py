#!/usr/bin/python3.4
# coding: utf-8

import time
from sys import argv
import logging
from logging.handlers import WatchedFileHandler
import pymysql
# pymysql.install_as_MySQLdb()
import gc

# -- DB definions:
db_name = 'autocall'
host = 'XXX.XXX.XXX.XXX'
user = 'XXX.XXX.XXX'
passwd = 'XXX.XXX.XXX.XXX'
# table for API reading:
table_read = 'to_read'
# table for API writting:
table_parse = 'to_parse'

# ----- logger settings:
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# ---- syslog file settings:
fh = logging.handlers.WatchedFileHandler('/var/log/rellocate.log')
fh.setLevel(logging.INFO)  # For log-file output use logging.INFO to write to log
fh.setFormatter(formatter)
# ---- terminal log output settings:
# --- How to use DEBUG mode:
# --- For terminal output use logging.debug.
# --- Uncomment this line for debug only! Don't forget to comment this line back:
logger.setLevel(logging.DEBUG)
# --- And comment this line:
# logger.setLevel(logging.INFO)
# --- And don't forget to get it all back :)
# --- End of DEBUG mode block
ch = logging.StreamHandler()
ch.setFormatter(formatter)
# ------------------------------
logger.addHandler(fh)
# -   COMMENTED filehandler logging
# logger.addHandler(ch)

id, number, code, record, status = argv[1:]
logging.debug(
    "Got variables: id - {}, number - {}, code - {}, record - {}, status - {}".format(id, number, code, record, status))


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
                i += 1
                time.sleep(2)
                continue
        logging.debug("No connection to DB while db_connect func. Check DB definitions. Exiting!")
        logging.info("No connection to DB while db_connect func. Check DB definitions. Exiting!")
        raise SystemExit(1)


def get_code(cursor, db):
    try:
        sql_ins = """INSERT INTO %(table)s(`number`, `code`, `record`, `status`) VALUES ('%(number)s', '%(code)s', '%(record)s', '%(status)s')""" % {
            "table": table_read, "number": number, "code": code, "record": record, "status": status}
        cursor.execute(sql_ins)
        # INSERT INTO `to_read`(`number`, `code`, `record`, `status`) VALUES ('3590021', '3', '1', 'AN')

        sql_del = """DELETE FROM %(table)s WHERE id = '%(id)s'""" % {"table": table_parse, "id": id}
        cursor.execute(sql_del)
        db.commit()
        db.close()
        logging.info(sql_ins)
        logging.info(sql_del)
        gc.collect()
    except pymysql.err.OperationalError:
        db_connect()
    except (pymysql.err.ProgrammingError, pymysql.err.DataError, pymysql.err.IntegrityError) as error:
        logging.debug("Something went wrong with query!")
        logging.info("Something went wrong with query!")
        logging.debug(error)
        logging.info(error)


def initial():
    cursor, db = db_connect()
    get_code(cursor, db)


if __name__ == '__main__':
    initial()
