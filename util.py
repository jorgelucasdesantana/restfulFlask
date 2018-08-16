# util.py
#
# Comment: Utility functions.
#
#		
import hashlib
import os
import sys
from time import strftime
import subprocess
from config import SECRET_KEY
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from flask_restful import fields
import datetime
import logging
from config import FILELOG
import os
from logging.handlers import RotatingFileHandler


ErrorResponse = {
	'error_code': fields.Integer,
	'msg': fields.String
}

# Config system log.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = RotatingFileHandler(FILELOG, mode='a', maxBytes=1*1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

	
