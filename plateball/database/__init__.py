#! /usr/bin/env python3.5
# Copyright 2017 Gavin Hurlbut
# vim:ts=4:sw=4:ai:et:si:sts=4

import logging

from peewee import Model, Proxy, OperationalError, IntegrityError
from playhouse.pool import PooledSqliteDatabase

logger = logging.getLogger(__name__)

db_proxy = Proxy()


class BaseModel(Model):
    fields = []

    class Meta:
        database = db_proxy

    def __str__(self):
        attrs = {attr: str(getattr(self, attr, None))
                 for attr in self.fields}
        return str(attrs)


class Database(object):
    def __init__(self, filename, tables, foreign_keys=None):
        self.filename = filename
        maxConn = 50
        timeout = 600
        self.db = PooledSqliteDatabase(self.filename, max_connections=maxConn,
                                      stale_timeout=timeout)
        db_proxy.initialize(self.db)

        logger.info("Connecting to database %s" % self.filename)
        self.db.connect()
        self.db.create_tables(tables, safe=True)
        if foreign_keys:
            for (klass, key) in foreign_keys.items():
                try:
                    self.db.create_foreign_key(klass, key)
                except OperationalError as e:
                    (code, message) = e.args
                    if code != 1022:
                        logger.exception(exceptionDetails(e))
                except IntegrityError as e:
                    (code, message) = e.args
                    if code != 1215:
                        logger.exception(exceptionDetails(e))
                except Exception as e:
                    logger.exception(exceptionDetails(e))
        self.db.close()

    def execution_context(self):
        return self.db.execution_context()

    def bulkSave(self, objList, ignoreDupes=False):
        with self.db.execution_context():
            for obj in objList:
                try:
                    obj.save()
                except IntegrityError as e:
                    if not ignoreDupes:
                        logger.exception(exceptionDetails(e))
                    pass
                except Exception as e:
                    logger.exception(exceptionDetails(e))
                    pass

    def get_or_create_save(self, klass, item):
        with self.db.execution_context():
            (dbitem, created) = klass.get_or_create(**item)
            if created:
                dbitem.save()
            return dbitem

