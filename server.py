from flask import Flask, jsonify, request,g
from flask_restful import Api, Resource,reqparse
from jwt import encode,decode
from datetime import datetime,timedelta
from functools import wraps
from pymongo import MongoClient
from flask_cors import CORS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from random import randint
import os


confirmation_codes = {}

app = Flask(__name__)
api = Api(app)
CORS(app)
app.config['SECRET_KEY'] = os.environ['SECRET_DBKEY']

cluster = MongoClient(os.environ['DB_LINK'])
db = cluster["may"]
collection = db["users"]

def send_confirmation_code(firstname,lastname,email,password,dob,role):

    confirmation_code = str(randint(100000, 999999))

    # Set up the email message
    msg = MIMEMultipart()
    msg['From'] = os.environ['MAIL_ADDRESS']
    msg['To'] = email
    msg['Subject'] = 'Confirm Your Code'

    # Create the HTML content
    html = f"""
    <html>
    <head>
    <style>
        body {{
            background-color: #f5f5f5;
            font-family: Arial, sans-serif;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0px 0px 10px #cccccc;
            padding: 30px;
            margin: 50px auto;
            max-width: 600px;
        }}
        h1 {{
            color: #4c4c4c;
            text-align: center;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        .code {{
            background-color: #D02E83;
            color: white;
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            margin: 20px auto;
            width: 300px;
            border-radius: 10px;
            box-shadow: 0px 0px 10px #cccccc;
        }}
        p {{
            color: #4c4c4c;
            font-size: 16px;
            line-height: 1.5;
            margin-bottom: 20px;
            text-align:center;
        }}
    </style>
    </head>
    <body>
        <div class="container">
            <h1>Confirm Your Code</h1>
            <p>Thank you for registering. Your confirmation code is:</p>
            <div class="code">{confirmation_code}</div>
        </div>
    </body>
    </html>
    """

    # Add the HTML content to the email message
    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    # Set up the SMTP server connection
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # or 465 for SSL
    smtp_username = os.environ['MAIL_ADDRESS']
    smtp_password = os.environ['MAIL_PASSWORD']
    smtp_conn = SMTP(smtp_server, smtp_port)
    smtp_conn.starttls()
    smtp_conn.login(smtp_username, smtp_password)

    # Send the email
    smtp_conn.sendmail(msg['From'], msg['To'], msg.as_string())

    # Close the connection
    smtp_conn.quit()

    user_info = {
    "firstname": firstname,
    "lastname": lastname,
    "password": password,
    "email": email,
    "dob": dob,
    "role": role
    }

    confirmation_codes[confirmation_code] = user_info

def send_info_doctor(name,address,speciality,datentime,phone):
    # Set up the email message
    msg = MIMEMultipart()
    msg['From'] = os.environ['MAIL_ADDRESS']
    msg['To'] = os.environ['DOCTOR_MAIL']
    msg['Subject'] = 'Confirm Your Code'

    # Create the HTML content
    html = f"""
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Poppins', sans-serif;
                background-color: #f2f2f2;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #ffffff;
                box-shadow: 0px 0px 10px 0px rgba(0,0,0,0.1);
                border-radius: 10px;
            }}
            .logo {{
                display: block;
                margin: 0 auto;
                max-width: 200px;
            }}
            h1 {{
                margin-top: 50px;
                font-size: 36px;
                text-align: center;
                color: #333333;
            }}
            h2 {{
                font-size: 28px;
                text-align: center;
                color: #333333;
            }}
            .info {{
                margin-top: 50px;
                margin-bottom: 50px;
                text-align: center;
            }}
            label {{
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                display: block;
                margin-bottom: 10px;
            }}
            p {{
                font-size: 20px;
                color: #666666;
                margin-bottom: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img class="logo" src="img.jpg" alt="Logo">
            <h1>Appointment Confirmation</h1>
            <h2>Congratulations Doctor!</h2>
            <div class="info">
                <label for="">Address</label>
                <p>{address}</p>
                <label for="">Speciality</label>
                <p>{speciality}</p>
                <label for="">Name</label>
                <p>{name}</p>
                <label for="">Phone Number</label>
                <p>{phone}</p>
                <label for="">Date</label>
                <p>{datentime}</p>
            </div>
        </div>
    </body>
    </html>
    """


    # Add the HTML content to the email message
    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    # Set up the SMTP server connection
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # or 465 for SSL
    smtp_username = os.environ['MAIL_ADDRESS']
    smtp_password = os.environ['MAIL_PASSWORD']
    smtp_conn = SMTP(smtp_server, smtp_port)
    smtp_conn.starttls()
    smtp_conn.login(smtp_username, smtp_password)

    # Send the email
    smtp_conn.sendmail(msg['From'], msg['To'], msg.as_string())

    # Close the connection
    smtp_conn.quit()



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return {'message': 'Token is missing'}, 401
        
        try:
            data = decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            g.user = data['email']

        except:
            return {'message': 'Token is invalid'}, 401

        return f(*args, **kwargs)

    return decorated

class ProtectedResource(Resource):
    @token_required
    def get(self):
        results = collection.find_one({"email":g.user})
        if results:
            results.pop('_id', None)
            results.pop('password',None)
            return jsonify(results)

class SignupResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        print(request.data)

        print(parser)
        parser.add_argument('firstName', type=str, required=True, help='Firstname cannot be blank')
        parser.add_argument('lastName', type=str, required=True, help='Lastname cannot be blank')
        parser.add_argument('email', type=str, required=True, help='Email cannot be blank')
        parser.add_argument('password', type=str, required=True, help='Password cannot be blank')
        parser.add_argument('role', type=str, required=True, help='Role cannot be blank')
        parser.add_argument('dob', type=str, required=True, help='Date of birth cannot be blank')

        args = parser.parse_args()
        
        firstname = args['firstName']
        lastname = args['lastName']
        email = args['email']
        password = args['password']
        dob = args['dob']
        role = args['role']

        if collection.find_one({'email': email}):
            return {'message': 'Email already exists'}, 409

        # post = {'firstName':firstname,'lastName':lastname,'email': email,'password': password}
        # collection.insert_one(post)

        send_confirmation_code(firstname,lastname,email,password, dob, role)
        
        return {'message': 'Signup successful'}, 201
        
class confirmMail(Resource):
    def get(self,code):

        if code in confirmation_codes:
            post = {'firstName':confirmation_codes[code]["firstname"],
                    'lastName':confirmation_codes[code]["lastname"],
                    'email':confirmation_codes[code]["email"],
                    'password': confirmation_codes[code]["password"],
                    'dob' : confirmation_codes[code]["dob"],
                    'role':confirmation_codes[code]["role"]
                    }
            collection.insert_one(post)
            del confirmation_codes[code]
        else:
            return{"message":"incompleted"}
    
        return {'message':'finished'}
    
class LoginResource(Resource):
    def get(self, email, password):

        results = collection.find_one({"email":email})
        if results:
            if password == results["password"]:
                token = encode({'email':results["email"],
                                'firstName':results["firstName"],
                                'lastName':results["lastName"],
                                'dob':results["dob"],
                                'role':results["role"],
                                'exp': datetime.utcnow() + timedelta(days=1)},
                                app.config['SECRET_KEY'], algorithm='HS256')
                return {'token': token}
            else:
                return jsonify({'message':'Wrong Password'}),401

        return jsonify({'message':'Username not found'}),401
    
class send_order(Resource):
    def post(self):
        send_data = reqparse.RequestParser()
        send_data.add_argument('name', type=str, required=True, help='name cannot be blank')
        send_data.add_argument('address', type=str, required=True, help='address cannot be blank')
        send_data.add_argument('speciality', type=str, required=True, help='speciality cannot be blank')
        send_data.add_argument('date', type=str, required=True, help='Date & Time cannot be blank')
        send_data.add_argument('phone', type=str, required=True, help='Phone Number cannot be blank')
        
        args = send_data.parse_args()
        
        name  = args['name']
        address = args['address']
        speciality = args['speciality']
        date = args['date']
        phone = args['phone']

        send_info_doctor(name,address,speciality,date,phone)

        collection = db["bookings"]
        post = {"name":name,
                "address":address,
                "speciality":speciality,
                "date":date,
                "phone":phone
                }
        collection.insert_one(post)

        return {'message':'finished'}

api.add_resource(LoginResource, '/login/<string:email>/<string:password>')
api.add_resource(ProtectedResource, '/protected')
api.add_resource(SignupResource,'/signup')
api.add_resource(confirmMail,"/confirmMail/<string:code>")
api.add_resource(send_order,'/send')

if __name__ == "__main__":
    app.run()