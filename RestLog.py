# Rest: log
#
# Comment: Get system log.
#
#		
from flask_restful import Api, Resource, reqparse, fields, marshal
from pymongo import MongoClient
from flask import request
from config import FlaskAPI, mongoDB, FILELOG
from util import ErrorResponse, logger
from RestUser import get_user_acess
import os


LogResponse = {
	'log': fields.String,
	'error_code': fields.Integer,
	'msg': fields.String
}

class RestLog(Resource):
	def __init__(self):
				
		super(RestLog, self).__init__()
	
	def get(self):
		token = request.args.get('token', default = None, type = str)
		if not get_user_acess(token, 1):
			response = {'error_code': 1, 'msg': 'Acesso nao permitido.'}
			return marshal(response, ErrorResponse)
			
		logger.handlers[0].flush()
		
		strlog = ''
		with open(FILELOG, 'r') as f:
			for l in f:
				strlog += l
		
		response = {
			'log': strlog,
			'error_code': 0,
			'msg': ''
		}
		
		return marshal(response, LogResponse)
		 
	
FlaskAPI.add_resource(RestLog, '/webfront/api/v1.0/log', endpoint='log')

