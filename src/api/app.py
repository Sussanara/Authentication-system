"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_cors import CORS
from api.utils import APIException, generate_sitemap
from models import db, User
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
import datetime

app = Flask(_name_)
app.config['DEBUG'] = True
app.config['ENV'] = 'development'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///database.db'
app.config['JSON_SORT_KEYS'] = False

db.init_app(app)
Migrate(app,db)
CORS(app)
jwt = JWTManager(app)


@app.route('/', methods = ['GET'])
def default():
    return jsonify({"msg" : "API Working!"}), 200

@app.route('/login',methods = ['POST'])
def login_handle():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email : return jsonify({"msg" : "Email is required!"}), 400
    if not password : return jsonify({"msg" : "Password is required!"}), 400

    userFound = User.query.filter_by(email = email).first()
    if not userFound : return jsonify({"status" : "failed" , "msg" : "User not found, sign up instead."}) , 401
    if not check_password_hash(userFound.password,password): return jsonify({"status" : "failed" , "msg" : "Password is incorrect."}), 401

    access_expiration = datetime.timedelta(minutes=3)
    access_token = create_access_token(identity=userFound.id, expires_delta=access_expiration)

    data = {
        "access_token": access_token,
        "user" : userFound.serialize()
    }

    return jsonify({"status" : "success", "message": "Login successful", "data" : data}),200

@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email: return jsonify({"status" : "failed" , "msg" : "Email is required!"}), 400
    if not password: return jsonify({"status" : "failed", "msg" : "Password is required!"}), 400

    user = User()
    user.email = email
    user.password = generate_password_hash(password)
    user.save()

    if user:
        return jsonify({"status" : "success" , "msg" : "Register successful"}),200
    else:
        return jsonify({"status" : "failed" , "msg" : "Error registering user"}),400

@app.route('/private', methods=['GET'])
@jwt_required()
def private():
    id = get_jwt_identity()
    session_user = User.query.get(id)

    return jsonify(session_user.serialize()),200



# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    app.run()

