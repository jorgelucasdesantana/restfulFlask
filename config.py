from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from pymongo import MongoClient
import configparser
import io
import sys
import os

#Secret KEY for user login, changes every time that server reboots.
SECRET_KEY =  bytearray(os.urandom(32))

#Configure Flask app
app = Flask(__name__, static_url_path="")
FlaskAPI = Api(app)

#Start MongoDB
clientMongo = MongoClient()
mongoDB = clientMongo['VideoControl']

FILELOG = 'server.log'
SESSION_DURATION = 60
