from flask import Flask, request, jsonify
from threading import Thread
from icalendar import Calendar, Event
from dataclasses import dataclass
import schedule
import configparser
import datetime
import http.server
import socketserver
import sqlite3
import time
import atexit
import subprocess
import os
import json
import requests

@dataclass
class Metadata:
    status: str
    expiration: str


app = Flask(__name__)

status = "available"
expiration_time = datetime.datetime.now()

##load in config from ini
global config_json_file_name
global current_config
global current_json_config
config = configparser.ConfigParser()
config.read('config.ini')
current_config = config
##need to check that these things exist i think lol TODO
##write config to a dict to a json for use
def build_fresh_config_dict():
    config_dict = {
        'database': {
            'db_host': current_config.get('database', 'db_host'),
            'db_file_title': current_config.get('database', 'db_file_title')
        },
        'server': {
            'server_host': current_config.get('server', 'server_host'),
            'server_port': current_config.get('server', 'server_port'),
            'server_debug': current_config.get('server', 'server_debug')
        },
        'user': {
            'user_name': current_config.get('user', 'user_name'),
            'user_key': current_config.get('user', 'user_key')
        },
        'calendar': {
            'calendar_at': current_config.get('calendar', 'calendar_at')
        }
    }
    return config_dict

config_dict = build_fresh_config_dict()
config_json_file_name = 'config.json'
with open(config_json_file_name, 'w') as json_file:
    json.dump(config_dict, json_file)
##read for use
with open(config_json_file_name, 'r') as json_file:
    config_json = json.load(json_file)
    current_json_config = config_json

##key checker
def status_validation(key, recieved_key):
    if key != recieved_key:
        print("failed key")
        return "Unauthorized Token", 401
    else: 
        pass
        print("key accepted")


@app.route('/set_status', methods=['POST'])
def set_status():
    #phase this out soon
    #global status, expiration_time
    
    #checking if correct token is recieved in req
    status_validation(current_config.get('user','user_key'), request.headers.get('token'))

    req_status = request.json.get('status')

    ##make this make sure that the time is atleast 5 minutes or so
    duration = request.json.get('duration', 30)

    #validate status

    #currently rejecting what is being sent from test
    if req_status.strip() not in ["busy", "available"]:
        return "Invalid Status", 400
    
    status = req_status
    expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)
    user_from_config = current_json_config.get('user','user_name')
    user_from_config = user_from_config['user_name']
    try:
        connection = sqlite3.connect('stored_state.db')
        cursor = connection.cursor()
        result = cursor.execute('''
            UPDATE savedState SET status = (?), expiration = (?)
            WHERE user = (?)
        ''', status, expiration_time, user_from_config)
        connection.commit()
    except sqlite3.Error as error:
        print("failed to update savedState table", error)

    finally:
        if(connection):
            connection.close()
    return "Status Updated", 200

@app.route('/get_status', methods=['GET'])
def get_status():
    retrieved_metadata = get_metadata_from_db()
    #status validation
    print(retrieved_metadata.status)
    return jsonify({"status": retrieved_metadata.status, "expiration_time": retrieved_metadata.expiration})

##background status process
def status_expiration():
    while "status" in locals():
        if status == "busy":
            if expiration_time <= datetime.datetime.now():
                status = "available"
        time.sleep(60)

def get_metadata_from_db():
    try:
        user_from_config = current_json_config.get('user','user_name')
        user_from_config = user_from_config['user_name']
    except: 
        print("user was unable to retrieved from current_json_config")
    try:
        connection = sqlite3.connect('stored_state.db')
        cursor = connection.cursor()
        result = cursor.execute('''
            SELECT status, expiration FROM savedState
            WHERE user = (?)
        ''', user_from_config)
        fetched_data = result.fetchone()
        metadata_return = Metadata(status = fetched_data[0], expiration = fetched_data[1])
        connection.commit()
    except sqlite3.Error as error:
        print("failed to retrieve status", error)
    finally:
        if(connection):
            connection.close()
            return metadata_return

    
    
if __name__ == '__main__':
    status_checker_thread = Thread(target=status_expiration)
    status_checker_thread.start()
    server_host = current_config.get('server','server_host')
    server_debug = current_config.get('server','server_debug')
    server_port = current_config.get('server','server_port')
    app.run(host=server_host, debug=server_debug, port = server_port)
