# May May Doh Atwat API

The May May Doh Atwat API is a Flask-based API for user registration, login, and appointment booking system. It provides endpoints for user signup, user login, protected resource access with token authentication, and appointment booking. The API utilizes MongoDB for data storage and Flask-Restful for creating the RESTful endpoints.


## **Prerequisites**

Make sure you have the following installed:



* Python 3.x
* Flask
* Flask-Restful
* PyJWT
* pymongo
* Flask-Cors


## **Getting Started**



1. Clone the repository:
2. shell
3. Copy code
4. `git clone &lt;repository-url>`
5. Install the dependencies:
6. shell
7. Copy code
8. `pip install -r requirements.txt`
9. Set up environment variables:
    * SECRET_DBKEY: Secret key for encoding and decoding JWT tokens.
    * DB_LINK: MongoDB connection link.
    * MAIL_ADDRESS: Email address for sending confirmation codes.
    * MAIL_PASSWORD: Password for the email account.
    * DOCTOR_MAIL: Email address for sending appointment information to doctors.
10. Run the Flask API:
11. shell
12. Copy code
13. `python app.py`


## **Endpoints**


### **User Signup**

Endpoint: `/signup`

Method: `POST`

Parameters:



* `firstName`: First name of the user (required)
* `lastName`: Last name of the user (required)
* `email`: Email address of the user (required)
* `password`: Password for the user (required)
* `role`: Role of the user (required)
* `dob`: Date of birth of the user (required)


### **User Login**

Endpoint: `/login/&lt;string:email>/&lt;string:password>`

Method: `GET`

Parameters:



* `email`: Email address of the user (required)
* `password`: Password for the user (required)


### **Protected Resource Access**

Endpoint: `/protected`

Method: `GET`

Parameters:



* `token`: Token received after successful login (required)


### **Email Confirmation**

Endpoint: `/confirmMail/&lt;string:code>`

Method: `GET`

Parameters:



* `code`: Confirmation code sent to the user's email address (required)


### **Appointment Booking**

Endpoint: `/send`

Method: `POST`

Parameters:



* `name`: Name of the patient (required)
* `address`: Address of the patient (required)
* `speciality`: Specialty of the doctor (required)
* `date`: Date and time of the appointment (required)
* `phone`: Phone number of the patient (required)


## **Authentication**

Token-based authentication is used for protecting the `/protected` endpoint. When a user logs in successfully, a JWT (JSON Web Token) is generated and returned as a response. This token should be included as a query parameter (`token`) when accessing the protected resource.


## **MongoDB Database**

The API uses a MongoDB database for storing user information and appointment details. The connection link should be provided as an environment variable (`DB_LINK`) before running the API.


## **Email Confirmation and Notification**

Confirmation codes are sent to users' email addresses for email confirmation during signup. The API uses the SMTP protocol to send emails. The email address and password for the email account should be provided as environment variables (`MAIL_ADDRESS` and `MAIL_PASSWORD`). Appointment information is also sent to doctors via email.
