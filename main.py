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

app = Flask(__name__)
CORS(app)
app.secret_key = "secret key"
app.config['MONGO_URI'] = "mongodb://localhost:27017/face_auth"
mongo = PyMongo(app)
db = mongo.db

UPLOAD_FOLDER = '/Users/Hero/Documents/Projects/Dev/Third-Party-Auth-Backend/static/uploads'
TEMP_FOLDER = '/Users/Hero/Documents/Projects/Dev/Third-Party-Auth-Backend/static/temp_uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

@app.route("/user",methods=["GET", "POST"])
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
            # filename = "monster"
            
            # uploading file
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # print(data)
            # checking face in pic
            try:

                check_face = face_recognition.load_image_file("./static/uploads/" + filename)
                check_face_encoding = face_recognition.face_encodings(check_face)[0]
                email = request.form['email']
                image = "./static/uploads/" + filename
                new_user = { 'name': request.form['name'], 'email': request.form['email'], 'phone': request.form['phone'], "image":image }
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
    
            data =list(db.find())
            for user in data:
                user["_id"]= str(ObjectId(user["_id"]))
            return jsonify(data)
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})

@app.route("/user/<id>",methods=["GET", "PUT", "DELETE"])
def one_user(id):
    
    if request.method == "PUT":
    
        try:
    
            db.update_one({'_id':ObjectId(id)}, {'$set': {
                'name':request.json['name'],
                'email':request.json['email']
            }})
            return jsonify({'Message':"User Updated"})
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})
    
    elif request.method == "GET":
    
        try:
    
            user = db.find_one({'_id':ObjectId(id)})
    
            return jsonify({
                '_id':str(ObjectId(user['_id'])),
                'name':user['name']
            })
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})
    
    elif request.method == "DELETE":
    
        try:
            db.delete_one({'_id':ObjectId(id)})
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


@app.route("/login", methods=["POST"])
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
                # print(email)
                user = db.users.find_one({"email" : email})
                print(user)
                if(user is None):
                    return jsonify({"data":"profile not found"})
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

            if results[0] == True:
                return jsonify({"data": "face matched","userinfo":user["name"]})
            else:
                return jsonify({"data": "face not matched"})

            return jsonify({"data":filename})
        return jsonify({"data": "method not allowed000000000000"})
    return jsonify({"data": "method not allowed"})

########################################################

@app.route("/company",methods=["GET", "POST"])
def company():
    
    if request.method == "POST":
    
        try:
            result = db.company.companies.insert_one(request.json)
            return jsonify({'msg': 'data inserted'})
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})
    
    elif request.method == "GET":
    
        try:
    
            data =list(db.company.find())
            for user in data:
                user["_id"]= str(ObjectId(user["_id"]))
            return jsonify(data)
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})

@app.route("/company/<id>",methods=["GET", "PUT", "DELETE"])
def onecompany(id):
    
    if request.method == "PUT":
    
        try:
    
            db.company.update_one({'_id':ObjectId(id)}, {'$set': {
                'name':request.json['name'],
                'email':request.json['email']
            }})
            return jsonify({'Message':"User Updated"})
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})
    
    elif request.method == "GET":
    
        try:
    
            user = db.company.find_one({'_id':ObjectId(id)})
    
            return jsonify({
                '_id':str(ObjectId(user['_id'])),
                'name':user['name']
            })
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})
    
    elif request.method == "DELETE":
    
        try:
            db.company.delete_one({'_id':ObjectId(id)})
            return jsonify({'Message':"User Deleted"})
    
        except Exception as ex:
            return jsonify({'Message':"Something went wrong"})

if __name__ == '__main__':
    app.run(debug=True)