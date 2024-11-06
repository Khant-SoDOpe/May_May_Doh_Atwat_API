from flask import Flask, jsonify, request, g
from flask_restful import Api, Resource, reqparse
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta
from functools import wraps
from pymongo import MongoClient
from flask_cors import CORS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from random import randint
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
api = Api(app)
CORS(app)
app.config['SECRET_KEY'] = os.environ['SECRET_DBKEY']

# Database configuration
class Database:
    def __init__(self, db_link):
        cluster = MongoClient(db_link)
        self.db = cluster["may"]
        self.users = self.db["users"]
        self.bookings = self.db["bookings"]

db = Database(os.environ['DB_LINK'])

# Email handling
class EmailService:
    def __init__(self):
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.smtp_username = os.environ['MAIL_ADDRESS']
        self.smtp_password = os.environ['MAIL_PASSWORD']

    def send_email(self, recipient_email, subject, html_content):
        msg = MIMEMultipart()
        msg['From'] = self.smtp_username
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        
        with SMTP(self.smtp_server, self.smtp_port) as smtp_conn:
            smtp_conn.starttls()
            smtp_conn.login(self.smtp_username, self.smtp_password)
            smtp_conn.sendmail(msg['From'], msg['To'], msg.as_string())

email_service = EmailService()

# Authentication service
class AuthService:
    @staticmethod
    def generate_token(email, exp_days=1):
        payload = {
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=exp_days)
        }
        return encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_token(token):
        try:
            data = decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return data['email']
        except (ExpiredSignatureError, InvalidTokenError):
            return None

    @staticmethod
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.args.get('token')
            if not token:
                return {'message': 'Token is missing'}, 401

            user_email = AuthService.verify_token(token)
            if not user_email:
                return {'message': 'Token is invalid or expired'}, 401
            
            g.user = user_email
            return f(*args, **kwargs)
        return decorated

# Resources
class SignupResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('firstName', type=str, required=True, help='Firstname cannot be blank')
        parser.add_argument('lastName', type=str, required=True, help='Lastname cannot be blank')
        parser.add_argument('email', type=str, required=True, help='Email cannot be blank')
        parser.add_argument('password', type=str, required=True, help='Password cannot be blank')
        parser.add_argument('role', type=str, required=True, help='Role cannot be blank')
        parser.add_argument('dob', type=str, required=True, help='Date of birth cannot be blank')

        args = parser.parse_args()
        hashed_password = generate_password_hash(args['password'], method='sha256')

        if db.users.find_one({'email': args['email']}):
            return {'message': 'Email already exists'}, 409

        confirmation_code = str(randint(100000, 999999))
        html_content = f"""
            <html>
            <body>
                <h1>Confirm Your Code</h1>
                <p>Your confirmation code is: <b>{confirmation_code}</b></p>
            </body>
            </html>
        """
        email_service.send_email(args['email'], 'Confirm Your Code', html_content)
        
        db.users.insert_one({
            "firstname": args['firstName'],
            "lastname": args['lastName'],
            "email": args['email'],
            "password": hashed_password,
            "dob": args['dob'],
            "role": args['role'],
            "confirmation_code": confirmation_code,
            "is_confirmed": False
        })

        return {'message': 'Signup successful. Check your email for confirmation code.'}, 201

class ConfirmEmailResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, help='Email cannot be blank')
        parser.add_argument('code', type=str, required=True, help='Confirmation code cannot be blank')
        args = parser.parse_args()

        user = db.users.find_one({"email": args['email'], "confirmation_code": args['code']})
        if user:
            db.users.update_one({'email': args['email']}, {'$set': {'is_confirmed': True}})
            return {'message': 'Email confirmed successfully'}, 200
        else:
            return {'message': 'Invalid code or email'}, 400

class LoginResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, help='Email cannot be blank')
        parser.add_argument('password', type=str, required=True, help='Password cannot be blank')
        args = parser.parse_args()

        user = db.users.find_one({"email": args['email']})
        if user and check_password_hash(user['password'], args['password']):
            if not user['is_confirmed']:
                return {'message': 'Email not confirmed'}, 403

            token = AuthService.generate_token(user["email"])
            return {'token': token}, 200
        return {'message': 'Invalid email or password'}, 401

class ProtectedResource(Resource):
    @AuthService.token_required
    def get(self):
        user = db.users.find_one({"email": g.user})
        if user:
            user.pop('_id', None)
            user.pop('password', None)
            user.pop('confirmation_code', None)
            return jsonify(user)
        return {'message': 'User not found'}, 404

class AppointmentResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help='Name cannot be blank')
        parser.add_argument('address', type=str, required=True, help='Address cannot be blank')
        parser.add_argument('speciality', type=str, required=True, help='Speciality cannot be blank')
        parser.add_argument('date', type=str, required=True, help='Date cannot be blank')
        parser.add_argument('phone', type=str, required=True, help='Phone number cannot be blank')
        
        args = parser.parse_args()

        html_content = f"""
            <html>
            <body>
                <h1>New Appointment</h1>
                <p>Name: {args['name']}</p>
                <p>Address: {args['address']}</p>
                <p>Speciality: {args['speciality']}</p>
                <p>Date: {args['date']}</p>
                <p>Phone: {args['phone']}</p>
            </body>
            </html>
        """
        email_service.send_email(os.environ['DOCTOR_MAIL'], 'New Appointment Confirmation', html_content)

        db.bookings.insert_one({
            "name": args['name'],
            "address": args['address'],
            "speciality": args['speciality'],
            "date": args['date'],
            "phone": args['phone']
        })

        return {'message': 'Appointment booked successfully'}, 201

# Register resources
api.add_resource(SignupResource, '/signup')
api.add_resource(ConfirmEmailResource, '/confirm_email')
api.add_resource(LoginResource, '/login')
api.add_resource(ProtectedResource, '/protected')
api.add_resource(AppointmentResource, '/appointment')

if __name__ == "__main__":
    app.run(debug=True)
