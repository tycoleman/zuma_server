from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

import json
import random
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from email.utils import formataddr
import smtplib
import math
import os
import stripe
import time
import string
import binascii

import asyncio
from uuid import uuid4
from aioapns import APNs, NotificationRequest, PushType

from math import radians, sin, cos, sqrt, atan2


app = Flask(__name__)

CORS(app)

#config = {
#  apiKey: "AIzaSyDFC8lWQ4wh6UDngOGcUDvvriD5bOORc1U",
#  authDomain: "zuma-39233.firebaseapp.com",
#  projectId: "zuma-39233",
#  storageBucket: "zuma-39233.appspot.com",
#  messagingSenderId: "90592976863",
#  appId: "1:90592976863:web:d2c86b6dc9d51df6a62e6a",
#  measurementId: "G-Q1SXWQ5HCE"
#};


@app.route("/")
def base():
	return "<h1 style='color:black'><center>All Systems Operational</center><br><br><center>Development</center></h1>"
 


@app.route("/sendNotification/", methods=['POST'])
def sendNotification():
    cert_path = os.path.join(os.path.dirname(__file__), 'apns-dev-cert.pem')

    data = json.loads(request.data)


    apns_cert_client = APNs(
        client_cert = cert_path,
        use_sandbox = True,
    )

    requestNotification = NotificationRequest(
        device_token = data["token"],
        message = {
            "aps": {
                "alert": data["alert"],
                "badge": data["badge"],
                "sound": "default"
            }
        },
    )
    
    print("Received data:", data)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(apns_cert_client.send_notification(requestNotification))
    
    return 'Notification sent'


    

@app.route("/sendSupportEmail/<email>/<subject>/<message>")
def sendBaymazeSupportEmail(email,subject,message):

    email_sender = 'adrian@tutortree.com'
#    email_receiver = 'tylerscoleman@gmail.com'
    email_receiver = 'adrian@tutortree.com'

    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr((str(Header('Zuma Support', 'utf-8')), email_sender))
    msg['To'] = email_receiver
    msg['Subject']= subject


    text = "Zuma Support Ticket"
    html = """\
    <html>
    <head>
      <meta charset="utf-8">
      <link rel="stylesheet" type="text/css" href="http://www.jointutortree.com/wp-content/uploads/2018/07/tstyle.css">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link href="https://fonts.googleapis.com/css?family=Roboto:400,500,900" rel="stylesheet">
      <meta property="og:title" content="TutorTree">
    </head>


    <body>
      <div class="container" id="container">
        <center><img id="icon" style="background-color: white;
      width: 40px;
      height: auto;
      padding: 15 5 5 5;
      margin-top: 15px;"src="https://firebasestorage.googleapis.com/v0/b/baymaze-85263.appspot.com/o/BayMaze%20Logo%20White%20Background.png?alt=media&token=b92ef489-104d-4344-a6f1-8bd5368d8962"/></center>
        <br><br>
        <p id="subtext" style="text-align: center;margin-bottom:-15px;"><b>New Support Ticket</b></p>
        <p id="subtext" style="text-align: center;margin-bottom:-15px;">""" + message + """</p>
        <br>
    </body>

    <html>
    """
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    connection = smtplib.SMTP('smtp.office365.com', 587)
    connection.starttls()
    connection.login(email_sender, 'InfInIty00')
    connection.sendmail(email_sender, email_receiver, msg.as_string())
    connection.quit()
    return "Sent"
    
    
    
    
    
## Firestore setup
#cred = credentials.Certificate("path/to/serviceAccountKey.json")
#firebase_admin.initialize_app(cred)
#db = firestore.client()

def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius of the earth in miles
    R = 3958.8

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def find_match(user_id, users_info):
    user = users_info[user_id]
    best_match_id = None
    best_match_score = -1
    for uid, uinfo in users_info.items():
        if uid == user_id or user["Dating Preference"] not in [uinfo["Gender"], "Either"]:
            continue
        
        # Simple scoring system
        score = sum(int(user_interest == uinfo_interest)
                    for user_interest, uinfo_interest in zip(user["Interests"], uinfo["Interests"]))
        
        # Increment score if age difference is less than 5
        if abs(user["Age"] - uinfo["Age"]) <= 5:
            score += 1
        
        # Increment score if distance is less than or equal to 50 miles
        distance = calculate_distance(user["lat"], user["lon"], uinfo["lat"], uinfo["lon"])
        if distance <= 50:
            score += 1

        if score > best_match_score:
            best_match_id = uid
            best_match_score = score

    return best_match_id

def create_matches():
    # Get all user data
    users_ref = db.collection(u'users')
    users_docs = users_ref.stream()
    users_info = {doc.id: doc.to_dict() for doc in users_docs}
    
    # Find matches for all users
    matches = {}
    for user_id in users_info.keys():
        match = find_match(user_id, users_info)
        if match:
            matches[user_id] = match

    # Store matches in Firestore
    for user_id, match_id in matches.items():
        doc_ref = db.collection(u'matches').document(user_id)
        doc_ref.set({u'match_id': match_id})
        
if __name__ == "__main__":
    create_matches()

    
    
