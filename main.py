from flask import Flask,Response,request, jsonify, redirect, url_for
# import pymongo
import json
from flask_serialize import FlaskSerialize
from flask_pymongo import PyMongo, ObjectId
from bson.json_util import dumps
from werkzeug.utils import secure_filename
import os
import face_recognition
from flask_cors import CORS
import random
import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_expects_json import expects_json
#from flask_mail import Mail
from flask_mail import Message, Mail


#with open('config.json', 'r') as c:
    #params = json.load(c)["params"]
app = Flask(__name__)
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'f8c8af91c81f94'
app.config['MAIL_PASSWORD'] = 'e89b08b34fb4d6'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

CORS(app)
app.secret_key = "secret key"
app.config['MONGO_URI'] = "mongodb://localhost:27017/face_auth"
mongo = PyMongo(app)
db = mongo.db

# flask rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per minute", "1000 per second"],
)

company_schema = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'email': {'type': 'string'},
        'phone': {'type': 'number'}
    },
    'required': ['email', 'phone']
}

UPLOAD_FOLDER = '/Users/Hero/Documents/Projects/Dev/Third-Party-Auth-Backend/static/uploads'
TEMP_FOLDER = '/Users/Hero/Documents/Projects/Dev/Third-Party-Auth-Backend/static/temp_uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

class MongoAPI:
    def __init__(self, data):
        self.client = MongoClient("mongodb://localhost:27017/")  
      
        database = data['face_auth']
        collection = data['users']
        cursor = self.client[database]
        self.collection = cursor[collection]
        self.data = data

@app.route("/user",methods=["GET", "POST"])
@limiter.limit("100 per minute")
def users():
    
    if request.method == "POST":

        # checking file data there or not
        if 'file' not in request.files:
            return jsonify({"data":"no file found"})
        file = request.files['file']
        
        # checking file exists or not
        if file.filename == '': 
            return jsonify({"data":"No selected file"})
        
        if file:
            
            filename = secure_filename(file.filename)
            filename = request.form['email'].split("@")[0] + ".jpeg"
            
            # uploading file
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # print(data)
            # checking face in pic
            try:

                check_face = face_recognition.load_image_file("./static/uploads/" + filename)
                check_face_encoding = face_recognition.face_encodings(check_face)[0]
                email = request.form['email']
                password = request.form['password']
                image = "./static/uploads/" + filename
                new_user = { 'name': request.form['name'], 'email': email, 'password' : password , 'phone': request.form['phone'], "image":image, 'createdAt': datetime.datetime.now(), 'updatedAt' : datetime.datetime.now() }
                result = db.users.insert_one(new_user)
            
            except Exception as ex:

                # removing file from uploads folder
                pic_path = os.path.exists("./static/uploads/" + filename)
                if pic_path:
                    os.remove("./static/uploads/" + filename)
            
                return jsonify({"data":"no face found"})

            return jsonify({"data" : "User Created"})
        return jsonify({"data" : "file uploaded00000000"})        
    
    elif request.method == "GET":
    
        try:
    
            data =list(db.users.find())
            for user in data:
                user["_id"]= str(ObjectId(user["_id"]))
            return jsonify(data)
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})

@app.route("/user/<id>",methods=["GET", "PUT", "DELETE"])
@limiter.limit("1000 per minute")
def one_user(id):
    
    if request.method == "PUT":
    
        try:
    
            data = db.users.update_one({'_id':ObjectId(id)}, {'$set': {
                'name':request.json['name'],
                'email':request.json['email'],
                'phone':request.json['phone'],
                'password':request.json['password'],
                'updatedAt' : datetime.datetime.now()
            }})

            print(request.json, id)
            print(data)
            return jsonify({'Message':"User Updated"})
    
        except Exception as ex:
            print(ex)
            return jsonify({'Message':"Something went wrong"})
    
    elif request.method == "GET":
    
        try:
            print
            user = db.users.find_one({'_id':ObjectId(id)})
    
            return jsonify({
                '_id':str(ObjectId(user['_id'])),
                'name':user['name'],
                'email':user['email'],
                'phone':user['phone'],
                'password':user['password'],
                'image': 'http://localhost:5000' + user['image'].split('.')[1] + '.' +user['image'].split('.')[2],
                'createdAt': user['createdAt']
            })
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})
    
    elif request.method == "DELETE":
    
        try:
            db.users.delete_one({'_id':ObjectId(id)})
            return jsonify({'Message':"User Deleted"})
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})

# checking file extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/file",methods=["GET", "POST", "DELETE"])
def upload_file():

    if request.method == 'POST':
        
        # checking file data there or not
        if 'file' not in request.files:
            return jsonify({"data":"no file found"})
        file = request.files['file']
        
        # checking file exists or not
        if file.filename == '':
            return jsonify({"data":"No selected file"})
        
        if file:
            
            filename = secure_filename(file.filename)
            
            # uploading file
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # checking face in pic
            try:

                check_face = face_recognition.load_image_file("./static/uploads/" + filename)
                check_face_encoding = face_recognition.face_encodings(check_face)[0]
            
            except Exception as ex:
            
                # removing file from uploads folder
                pic_path = os.path.exists("./static/uploads/" + filename)
                if pic_path:
                    os.remove("./static/uploads/" + filename)
            
                return jsonify({"data":"no face found"})

            return jsonify({"data" : "file uploaded"})
    
    return jsonify({"data": "method not allowed"})

############################### User Login backend   ########################################

@app.route("/login-req", methods=["POST"])
@limiter.limit("100 per minute")
def login_request():
    email = request.json['email']
    user = db.users.find_one({"email":email})
    if(user is None):
        return jsonify({"message":"email not found"})
    token = random.randint(1111,9999)
    update_user = db.users.update_one({'email':email}, { '$set': { 'token' : token, 'updatedAt' : datetime.datetime.now() }})
    print(update_user)
    
    company_id = request.json['organization']
    company = db.companies.find_one({'_id': ObjectId(company_id)})

    if(company is None):
        return jsonify({"message": "no organization found"})

    history = {
                'user_id' : str(user['_id']),
                'company_id':str(company['_id']),
                'name' : company['name'],
                'email' : company['email'],
                'phone' : company['phone'],
                'token' : token,
                'time' : datetime.datetime.now()
            }

    db.history.insert_one(history)

    return jsonify(token)
    
def timeDifference(time1, time2):
    diff = time1 - time2
    return diff.total_seconds() / 60

@app.route("/login", methods=["POST"])
@limiter.limit("100 per minute")
def user_login():
    
    if request.method == 'POST':
        print(request.files)
        if 'file' not in request.files:
            return jsonify({"data":"no file found"})
    
        file = request.files['file']
    
        if file.filename == '':
            return jsonify({"data":"No selected file"})
    
        if file:
    
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['TEMP_FOLDER'], filename))

            # db query user email, image
            # face reco
            # companies

            try:
                email = request.form['email']
                token = request.form['token']
                print(email + " " + token)
                
                user = db.users.find_one({"email" : email})
                if(user is None):
                    return jsonify({"data":"email not found"})
                db_pic = face_recognition.load_image_file(user['image'])
                db_pic_encode = face_recognition.face_encodings(db_pic)[0]
    
            except Exception as ex:
                print(ex)
                return jsonify({"data" : "no face found in db"})

            try:
    
                current_pic = face_recognition.load_image_file("./static/temp_uploads/" + filename)
                current_pic_encode = face_recognition.face_encodings(current_pic)[0]

                pic_path = os.path.exists("./static/temp_uploads/" + filename)
                if pic_path:
                    os.remove("./static/temp_uploads/" + filename)

            except Exception as ex:
    
                pic_path = os.path.exists("./static/temp_uploads/" + filename)
                if pic_path:
                    os.remove("./static/temp_uploads/" + filename)
    
                return jsonify({"data" : "no face found"})

            results = face_recognition.compare_faces([db_pic_encode], current_pic_encode)
            print(user['_id'])
            if results[0] == True:
                return dumps(user)
            else:
                return jsonify({"data": "face not matched"})

            return jsonify({"data":filename})
        return jsonify({"data": "something went wrong"})
    return jsonify({"data": "method not allowed"})

@app.route("/login-user", methods=["POST"])
@limiter.limit("100 per minute")
def user_login_dash():
    
    if request.method == 'POST':
        
        try:
                email = request.json['email']
                password = request.json['password']
                
                user = db.users.find_one({"email" : email})
                
                if user is None:
                    return jsonify({"data" : "Email Not Found"})

                if(user['password'] == password):
                    print("user is corrent")
                    return jsonify({
                        'company_id':str(ObjectId(user['_id'])),
                        'name':user['name'],
                        'email':user['email'],
                        'phone':user['phone'],
                        'image': 'http://localhost:5000' + user['image'].split('.')[1] + '.' +user['image'].split('.')[2],
                        'createdAt': user['createdAt']
                    })
                else:
                    print("password is  not matched")
                    return jsonify({"data" : "password not matched"})
                
        except Exception as ex:
            print(ex)
            return jsonify({"data" : "something went wrong"})

    return jsonify({"data": "method not allowed"})    

########################## Company Backend ##############################

@app.route("/company",methods=["GET", "POST"])
@limiter.limit("100 per minute")
# @expects_json(company_schema)
def company():
    
    if request.method == "POST":
    
        try:
            name = request.json['name']
            email = request.json['email']
            phone = request.json['phone']
            phone = int(phone)
            
            company = db.companies.find_one({'email': email})
            if company:
                return jsonify({'company_id':str(ObjectId(company['_id']))})        
            
            result = db.companies.insert_one({ 'name': name, 'email' : email, 'phone' : phone})
            print(company)  
            return jsonify({'company_id':str(ObjectId(company['_id']))})
    
        except Exception as ex:
            print(ex)
            return jsonify({'data':"Something went wrong"})
    
    elif request.method == "GET":
    
        try:
    
            data =list(db.company.find())
            for user in data:
                user["_id"]= str(ObjectId(user["_id"]))
            return jsonify(data)
    
        except Exception as ex:
            return jsonify({'data':"Something went wrong"})

@app.route("/company/<id>",methods=["GET", "PUT", "DELETE"])
@limiter.limit("100 per minute")
def onecompany(id):
    
    if request.method == "PUT":
    
        try:
    
            db.company.update_one({'_id':ObjectId(id)}, {'$set': {
                'name':request.json['name'],
                'email':request.json['email'],
                'web':request.json['web'],
            }})
            return jsonify({'data':"User Updated"})
    
        except Exception as ex:
            return jsonify({'data':"Something went wrong"})
    
    elif request.method == "GET":
    
        try:
    
            user = db.company.find_one({'_id':ObjectId(id)})
    
            return jsonify({
                '_id':str(ObjectId(user['_id'])),
                'name':user['name']
            })
    
        except Exception as ex:
            return jsonify({'data':"Something went wrong"})
    
    elif request.method == "DELETE":
    
        try:
            db.company.delete_one({'_id':ObjectId(id)})
            return jsonify({'data':"User Deleted"})
    
        except Exception as ex:
            return jsonify({'data':"Something went wrong"})

############################### User Login History #######################

@app.route('/history/<id>', methods=["GET"])
@limiter.limit("100 per minute")
def login_history(id):
    try:

        # history =list(db.history.find({'user_id' : id}))
        history =list(db.history.aggregate( [ { "$match" : { "user_id": id } }, { "$sort" : { "time" : -1 } } ] ) )
        for data in history:
            data["_id"]= str(ObjectId(data["_id"]))
        return jsonify(history)        

    except Exception as ex:
        return jsonify({"error": ex})

@app.route('/history/<id>', methods=["DELETE"])
@limiter.limit("100 per minute")
def delete_history(id):
    if request.method == "DELETE":

        try:
            
            db.history.delete_many({'user_id': id})
            return jsonify({"data": "all history deleted"})        

        except Exception as ex:
            return jsonify({"error": ex})
    return jsonify({"data" : "method not allowed"})

if __name__ == '__main__':
    app.run(debug=True)