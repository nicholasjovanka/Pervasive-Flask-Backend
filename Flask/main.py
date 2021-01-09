from flask import Flask, request, send_file, send_from_directory, safe_join, abort
from flask_cors import CORS, cross_origin
from flask_restful import Resource, Api
from json import dumps
from flask_jsonpify import jsonify
from datetime import datetime
from flask_mysqldb import MySQL


import pandas as pd
import time
import matplotlib.pyplot as plt
import math


#region Helper Functions
def getMET(angle):
    if 0 <= angle <=  5.0:
        return 3.5
    elif 5.1 <= angle <= 12:
        return 4.5
    elif -5 <= angle <= -0.1:
        return 3.5


def calorie_calculator(df,interval):
    interval = math.floor(interval)
    calories = 0
    i = 0
    until = 0
    total = df['Rotation'].tolist()[-1]
    while i < total:
        if (i + interval) <= total:
            until = i + interval
            data = df.iloc[i:until]
            angle = df.iloc[i:until]['Angle'].mean(axis= 0)
            calories+= (getMET(angle)*weight*3.5)/200
            i = until
        elif (i + interval)> total:
            data = df.iloc[i:]
            angle = df.iloc[i:]['Angle'].mean(axis= 0)
            calories+= (getMET(angle)*weight*3.5)/200
            i+= interval
    return calories

weight = 70

def process_data(df):
    startTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(df.iloc[0])))
    calculationData = df.iloc[1:len(df.index)-1]
    endTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(df.iloc[-1])))
    startTime = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
    endTime = datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S')
    calculationData = calculationData[0].str.split(',',1, expand=True)
    calculationData.columns=['Angle','Rotation']
    Converted_CD = calculationData.drop_duplicates('Rotation', keep='first').astype('float')
    plt.plot(Converted_CD['Rotation'],Converted_CD['Angle'])
    plt.xlabel("Number of Rotation")
    plt.ylabel("Angle")
    filepath ='./image/'+str(time.time())+'.png'
    plt.savefig(filepath,dpi=1000)
    distance_traveled = (3.14 * 62 * Converted_CD['Rotation'].tolist()[-1])/100
    time_delta = (endTime - startTime)
    total_seconds = time_delta.total_seconds()
    minutes = total_seconds/60
    minutes = int(minutes)
    rotations_per_minute = Converted_CD['Rotation'].tolist()[-1]/minutes
    calories_burned = calorie_calculator(Converted_CD,rotations_per_minute)
    return filepath, distance_traveled, calories_burned, rotations_per_minute, minutes, startTime, endTime

#endregion






app = Flask(__name__)
CORS(app)


app.config['MYSQL_HOST'] = 'ls-e233a8b9c9ebb55edb754ef0991a5280c1a1e830.ctwnxrfjixvr.ap-southeast-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'nicholas'
app.config['MYSQL_PASSWORD'] = 'tOVqBt5_c`I!EMKO4CB$Ce$.~2Lm74Uv'
app.config['MYSQL_DB'] = 'pervasive'

mysql = MySQL(app)

@app.route('/')
def index():
    return 'Flask is running!'

@app.route('/sendResult',methods=['POST'])
def test():
    if 'data' not in request.files:
        print('no files found')
    else:
        a = request.files['data']
        filename = str(time.time())
        a.save('./resultsDump/'+filename+'.csv')
        print(filename)
        df = pd.read_csv('./resultsDump/'+filename+'.csv',sep='\n',header = None)
        filepath, distance_traveled, calories_burned, rotations_per_minute, minutes, startTime, endTime = process_data(df)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO pervasive_data(calorie_burned, distance_traveled, starttime, endtime, duration, rpm, image_path) VALUES (%s, %s, %s, %s, %s, %s, %s)", (calories_burned, distance_traveled, startTime, endTime, minutes, rotations_per_minute, filepath))
        mysql.connection.commit()
        cur.close()

    return jsonify({'msg':'success'})



@app.route('/getLatest',methods=['GET'])
def test2():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM pervasive_data WHERE id=(SELECT MAX(id) FROM pervasive_data);")
        results = cur.fetchall()[0]

        response = {
            "id":results[0],
            "calorie_burned":results[1],
            "distance_traveled":results[2],
            "startTime":results[3],
            "endTime":results[4],
            "duration":results[5],
            "rpm":results[6],

        }
        print(type(response))
        print(results)
        return jsonify(response)
    except:
        return jsonify({"status":"error"})

@app.route('/getLatestImage',methods=['GET'])
def imagefetch():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM pervasive_data WHERE id=(SELECT MAX(id) FROM pervasive_data);")
        results = cur.fetchall()[0] 
        return send_file(results[7])
    except:
        return jsonify({"status":"error"})

@app.route('/getSpecific',methods=['GET'])
def specific():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM pervasive_data WHERE id="+request.form['id'] +";")
        results = cur.fetchall()[0]
        response = {
            "id":results[0],
            "calorie_burned":results[1],
            "distance_traveled":results[2],
            "startTime":results[3],
            "endTime":results[4],
            "duration":results[5],
            "rpm":results[6],

        }
        print(type(response))
        print(results)
        return jsonify(response)
    
    except:
        return jsonify({"status":"error"})
    

@app.route('/getRecentTwenty',methods=['GET'])
def recent():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id , starttime from pervasive_data order by id desc limit 20;")
    results = cur.fetchall()
    print(len(results))
    response ={}
    for i in range(len(results)):
        response[i] = {
            "id":results[i][0],
            "startTime":results[i][1],
        }
    return jsonify(response)

if __name__ == "__main__":
   app.run()




