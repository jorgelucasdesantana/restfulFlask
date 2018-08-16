# Rest: user
#
# Comment: User CRUD.
#
#		
from flask_restful import Api, Resource, reqparse, fields, marshal
from pymongo import MongoClient
from flask import request
from bson.objectid import ObjectId
from passlib.apps import custom_app_context as pwd_context
from config import FlaskAPI, mongoDB, SECRET_KEY, SESSION_DURATION
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from util import ErrorResponse, logger


#Server response
User = {
	'workername': fields.String,
	'username': fields.String,
	'id': fields.String,
	'passwd': fields.String,
	'security_level': fields.Integer
}

UserResponse = {
	'users': fields.List(fields.Nested(User)),
	'error_code': fields.Integer,
	'msg': fields.String
}

class RestUsers(Resource):
	def __init__(self):
		self.reqparsePost = reqparse.RequestParser()
		self.reqparsePost.add_argument('workername', type=str, required=True,
                                   help='No workername provided.',
                                   location='json')
		self.reqparsePost.add_argument('username', type=str, required=True,
                                   help='No username provided.',
                                   location='json')
		self.reqparsePost.add_argument('passwd', type=str, required=True,
                                   help='No passwd provided.',
                                   location='json')
		self.reqparsePost.add_argument('security_level', type=int, required=True,
                                   help='No security_level provided.',
                                   location='json')

		self.reqparsePut = reqparse.RequestParser()
		self.reqparsePut.add_argument('id', type=str, required=True,
                                   location='json')                                   
		self.reqparsePut.add_argument('passwd', type=str, required=False,
                                   help='No passwd provided.',
                                   location='json')
		self.reqparsePut.add_argument('security_level', type=int, required=False,
                                   help='No security_level provided.',
                                   location='json')
                                   
				
		super(RestUsers, self).__init__()
	
	def getusers(self):
		c_Users = mongoDB['UserList']		
		
		response = {'users': [], 'error_code': 0, 'msg': ''}
		
		if c_Users is None:
			return marshal(response, UserResponse)
		
		l = c_Users.find()
		
		for i in l:
			response['users'].append({'workername': i['workername'], 
										'id': str(i['_id']),
										'username': i['username'],
										'security_level': i['security_level'],
										'passwd': i['passwd']})
			
		return marshal(response, UserResponse)

	def get(self):
		token = request.args.get('token', default = None, type = str)
		if not get_user_acess(token, 1):
			response = {'error_code': 1, 'msg': 'Acesso nao permitido.'}
			return marshal(response, ErrorResponse)
		
		return self.getusers()
		 
	def post(self):
		token = request.args.get('token', default = None, type = str)
		if not get_user_acess(token, 1):
			response = {'error_code': 1, 'msg': 'Acesso nao permitido.'}
			return marshal(response, ErrorResponse)
		
		args = self.reqparsePost.parse_args()
		
		c_Users = mongoDB['UserList']
		
		args['passwd'] = pwd_context.encrypt(args['passwd'])

		user_id = c_Users.insert_one(args)
		
		return self.getusers()
		
	def put(self):
		token = request.args.get('token', default = None, type = str)
		if not get_user_acess(token, 1):
			response = {'error_code': 1, 'msg': 'Acesso nao permitido.'}
			return marshal(response, ErrorResponse)

		args = self.reqparsePut.parse_args()
			
		if args['id'] is None:
			response = {'error_code': 1, 'msg': 'Campo id nao encontrado.'}
			return marshal(response, ErrorResponse)
			
		c_Users = mongoDB['UserList']

		user = c_Users.find_one({'_id': ObjectId(args['id'])})

		if user is None:
			response = {'error_code': 1, 'msg': 'User id nao encontrado.'}
			return marshal(response, ErrorResponse)

		#Only admin can change password for other users. 
		adm = c_Users.find_one({'username': get_username(token)})
		if adm is None:
			response = {'error_code': 1, 'msg': 'Usuario logado nao encontrado nos registros.'}
			return marshal(response, ErrorResponse)
		
		if adm['security_level'] > 0:
			if get_username(token) != user['username']:
				response = {'error_code': 1, 'msg': 'Somente administrador pode trocar a senha de outro usuario.'}
				return marshal(response, ErrorResponse)
		
		if args['passwd'] is not None:
			c_Users.update({'_id': ObjectId(args['id'])}, {'$set': {'passwd': pwd_context.encrypt(args['passwd'])}})
			#logout the user!
			c_Session = mongoDB['UserSession']
			c_Session.remove({'username': get_username('token')})
			
		if args['security_level'] is not None:
			c_Users.update({'_id': ObjectId(args['id'])}, {'$set': {'security_level': args['security_level']}})
			
		return self.getusers()
		
	def delete(self):
		token = request.args.get('token', default = None, type = str)
		if not get_user_acess(token, 0):
			response = {'error_code': 1, 'msg': 'Acesso nao permitido.'}
			return marshal(response, ErrorResponse)

		id = request.args.get('id', default = None, type = str)
		if id is None:
			response = {'error_code': 1, 'msg': 'Campo id nao encontrado.'}
			return marshal(response, ErrorResponse)
			
		c_Users = mongoDB['UserList']

		user = c_Users.find_one({'_id': ObjectId(id)})
		
		if user is None:
			response = {'error_code': 1, 'msg': 'Usuario nao encontrado.'}
			return marshal(response, ErrorResponse)
			
		if user['username'] == 'admin':
			response = {'error_code': 1, 'msg': 'Usuario admin nao pode ser removido.'}
			return marshal(response, ErrorResponse)
		
		c_Users.delete_one({'_id': ObjectId(id)})
						
		return self.getusers()
		
FlaskAPI.add_resource(RestUsers, '/webfront/api/v1.0/users', endpoint='users')


UserLoginResponse = {
	'error_code': fields.Integer,
	'msg': fields.String,
	'token': fields.String
}

class RestUserLogin(Resource):
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('username', type=str, required=True,
                                   help='No username provided.',
                                   location='json')
		self.reqparse.add_argument('passwd', type=str, required=False,
                                   help='No passwd provided.',
                                   location='json')
				
		super(RestUserLogin, self).__init__()

	def post(self):
		args = self.reqparse.parse_args()
		
		c_Users = mongoDB['UserList']
		
		user = c_Users.find_one({'username': args['username']})
		if user is None:
			response = {'error_code': 1, 'msg': 'Usuario ou senha errados.'}
			return marshal(response, ErrorResponse)

		valid = pwd_context.verify(args['passwd'], user['passwd'])
		
		if not valid:
			response = {'error_code': 1, 'msg': 'Usuario ou senha errados.'}
			return marshal(response, ErrorResponse)

		c_Session = mongoDB['UserSession']
		
		session = c_Session.find_one({'username': args['username']})
		if session:
			c_Session.remove({'username': args['username']}, multi=True)
		
		s = Serializer(SECRET_KEY, expires_in = SESSION_DURATION*60*60)
		token = s.dumps({ 'username': args['username']})
		token = str(token).split('\'')
		
		data = {
			'username': args['username'],
			'token': token[1],
		}

		c_Session.insert_one(data)
		
		response = {'error_code': 0, 'msg': '', 'token': token[1]}
		
		return marshal(response, UserLoginResponse)
		
	def delete(self):
		token = request.args.get('token', default = None, type = str)
		if token is None:
			response = {'error_code': 1, 'msg': 'Campo token nao encontrado.'}
			return marshal(response, ErrorResponse)
			
		c_Session = mongoDB['UserSession']
		
		user = c_Session.find_one({'username': get_username(token)})
		if user is None:
			response = {'error_code': 1, 'msg': 'Usuario nao encontrado.'}
			return marshal(response, ErrorResponse)
			

		c_Session.remove({'username': get_username(token)})
		
		response = {'error_code': 0, 'msg': ''}
		return marshal(response, UserLoginResponse)
		
FlaskAPI.add_resource(RestUserLogin, '/webfront/api/v1.0/login', endpoint='login')
	
def get_user_acess(token, permission):
	if token is None:
		return False
			
	s = Serializer(SECRET_KEY)
	
	try:
		data = s.loads(token)
	except SignatureExpired:
		logger.info('Signature expired.')
		return  False
	except BadSignature:
		logger.info('Bad signature.')
		return False
		
	c_Session = mongoDB['UserSession']
	session = c_Session.find_one({'username': data['username']})
	if session is None:
		logger.info('%s has no session.' % data['username'])
		return False
			
	if str(session['token']) != token:
		logger.info('Wrong token.')
		return False
			
	c_Users = mongoDB['UserList']
	user = c_Users.find_one({'username': data['username']})
	if user is None:
		logger.info('User not found (%s).' % data['username'])
		return False
		
	if user['security_level'] <= permission:
		return True
		
	return False

def get_username(token):
	if token is None:
		return None
		
	s = Serializer(SECRET_KEY)
	
	try:
		data = s.loads(token)
	except SignatureExpired:
		logger.info('Signature expired.')
		return  None
	except BadSignature:
		logger.info('Bad signature.')
		return None
		
	c_Users = mongoDB['UserList']
		
	user = c_Users.find_one({'username': data['username']})
	if user is None:
		logger.info('User not found (%s).' % data['username'])
		return None
		
	return user['username']
	

#Add admin user on the firt execution.
c_Users = mongoDB['UserList']	
admin = c_Users.find_one({'username': 'admin'})
if admin is None:
	data = {
		'workername': 'Administrador',
		'username': 'admin',
		'passwd': pwd_context.encrypt('admin'),
		'security_level': 0
	}
	
	c_Users.insert(data)

