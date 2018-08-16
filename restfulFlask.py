from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from pymongo import MongoClient
from config import app

#Each rest must be implemented as a class on a new source file.
#All rest files must be imported here
import RestUser
import RestLog

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
