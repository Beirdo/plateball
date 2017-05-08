#! /usr/bin/env python3.5
# Copyright 2017 Gavin Hurlbut
# vim:ts=4:sw=4:ai:et:si:sts=4

import logging

logger = logging.getLogger(__name__)


def setupLogging(level):
    FORMAT = "%(asctime)s: %(name)s:%(lineno)d (%(threadName)s) - %(levelname)s - %(message)s"
    logging.basicConfig(format=FORMAT)
    logging.getLogger(None).setLevel(level)
    logging.captureWarnings(True)


def debugLogging(debug):
    if debug:
        logging.getLogger(None).setLevel(logging.DEBUG)
    else:
        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("AWSFirmwarePythonUtils.odin").setLevel(logging.ERROR)
        logging.getLogger("AWSFirmwarePythonUtils.dynamodbclient").setLevel(logging.ERROR)
        logging.getLogger("requests").setLevel(logging.CRITICAL)

