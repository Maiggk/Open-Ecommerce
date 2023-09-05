from logging import exception
import MySQLdb
from django.conf import settings
from django.core.exceptions import *
from django.db.utils import *
from MySQLdb import ProgrammingError


#https://mysqlclient.readthedocs.io/user_guide.html
class SybremDb:

    def __init__(self):
        try:
            self._conn = MySQLdb.connect(host=settings.AWS_DB_HOST,
                                            passwd=settings.AWS_DB_KEY,
                                            user=settings.AWS_DB_USER,
                                            db="sybremdb",
                                            port=3306,
                                        #  charset='utf8',
                                            charset='latin2',
                                            connect_timeout=2)
        except:
            raise Exception("ConnectionTimeout")
        self._cursor = self._conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params=None):
        try:
            self.cursor.execute(sql, params or ())
            return self.fetchall()
        except MySQLdb.ProgrammingError:
            print("*** Error executing query: Programing syntax error ***")
            raise ProgrammingError( "*** Error executing query: Programing syntax error ***")
        except MySQLdb.IntegrityError:
            print("*** IntegrityError inserting/updating info ***")
            raise MySQLdb.IntegrityError("*** IntegrityError inserting/updating info ***")
        # except Exception as e:
        #     raise Exception("ConnectionTimeout")