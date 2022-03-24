#! /usr/bin/sh
import pymysql
from flask import Flask
from flask import render_template
from flask import request,redirect,url_for,flash,session,send_from_directory
from flask import jsonify
from flask import Response
import urllib
import json
import traceback  
import os
import time
import sys
import importlib
import shutil
import datetime
import zipfile
import io  
import sys  
import _thread 
import subprocess
import time as time1 
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') 


app = Flask(__name__)

UPLOAD_FOLDER = 'upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  

ID_UPLOAD_FOLDER="id"
app.config['ID_UPLOAD_FOLDER'] = ID_UPLOAD_FOLDER

basedir = os.path.abspath(os.path.dirname(__file__))  
ALLOWED_EXTENSIONS = set(['txt', 'png', 'jpg', 'xls', 'JPG', 'png', 'xlsx', 'gif', 'GIF'])  

ID_ALLOWED_EXTENSIONS = set(['png','PNG'])


def run(user_id, file_name, old_fname):

    db = pymysql.connect(
                           host='107.182.182.18',
                           port= 3306 ,
                           user= 'root',
                           passwd='pwd_aitrans',
                           db='user_info')
    cursor = db.cursor()
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    path = u"'/root/mmgc/team/" +user_id + u"/submit/'" 
    folder = os.path.exists(path)
    print(path)
    if folder:
        shutil.rmtree(path)
    #print("/home/team/" +user_id + "/" + file_name)
    z = zipfile.ZipFile( u"/root/mmgc/team/" +user_id + u"/" + file_name, 'r')
    z.extractall(path= u'/root/mmgc/team/'+ user_id + u"/" )
    z.close()
    print("python3 " + u'"/root/mmgc/team/' + user_id + u'/run.py"' + u'  "' + user_id + u'"  ' +u'"'+ old_fname+u'"')
    try:
        output= subprocess.getstatusoutput("python3 " + u'"/root/mmgc/team/' + user_id + u'/run.py"' + u'  "' + user_id + u'"  ' + u'"'+old_fname+u'"' )
        #output=subprocess.getstatusoutput("python3 " +u'/root/hello.py' ) 
        print(output)
        #sys.path.append(u"/home/team/" + user_id + u"/")
        #import online
        #result =  online.test(user_id)
        #sys.path.remove(u"/home/team/" + user_id + u"/")
    except:
        sql = "INSERT INTO mmgc_result  VALUES ('%s' , '%s','%s', %s, %s ,' path error');"%(user_id, old_fname,time,0, 0)
        try:
             cursor.execute(sql)
             print(" Path Error")
             db.commit()
             db.close()
        except:
             traceback.print_exc()
             db.rollback()
             db.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
def id_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ID_ALLOWED_EXTENSIONS

'''
user_id = "pied piper"
sys.path.append(u'/home/team/' + user_id + u'/submit/')
import ABR as ABR1
global abr1
abr1 = ABR1.Algorithm()
#abr1.Initial()
#sys.path.remove(u'/home/team/' + user_id + u'/submit/')

@app.route('/abr/',methods = ['POST','GET'])
def abr():
    #print(request.headers)
    #print(request.form)
    BIT_RATE = [500.0, 1200.0]
    if request.method == "POST":
        teamid_str         = request.form.get('teamid')
        timestamp_str      = request.form.get('timestamp')
        time_interval_str  = request.form.get('time_interval')
        send_data_size_str = request.form.get('send_data_size')
        frame_time_len_str = request.form.get('frame_time_len')
        rebuf_time_str     = request.form.get('rebuf_time')
        buffer_size_str    = request.form.get('buffer_size')
        end_delay_str      = request.form.get('end_delay')
        buffer_flag_str    = request.form.get('buffer_flag')
        cdn_flag_str       = request.form.get('cdn_flag')
        cdn_has_frame_str  = request.form.get('cdn_has_frame')
        frame_type_str     = request.form.get('frame_type')
        quality_str        = request.form.get('quality')

        teamid_arr = str(teamid_str).split("mlinkm/")
        teamid = teamid_arr[1]
        timestamp = int(timestamp_str)

        time_interval_arr = time_interval_str.split(",")
        time_interval = []
        for i in range(1,len(time_interval_arr) -1):
            time_interval.append(float(time_interval_arr[i]) / 1000)
        
        send_data_size_arr = send_data_size_str.split(",")
        send_data_size = []
        for i in range(1,len(send_data_size_arr) -1):
            send_data_size.append(int(send_data_size_arr[i]) * 8) 

        frame_time_len_arr = frame_time_len_str.split(",")
        frame_time_len = []
        for i in range(1,len(frame_time_len_arr) -1):
            frame_time_len.append(float(frame_time_len_arr[i]) / 1000) 

        buffer_size_arr = buffer_size_str.split(",")
        buffer_size = []
        for i in range(1,len(buffer_size_arr) -1):
            buffer_size.append(float(buffer_size_arr[i]) /1000) 

        end_delay_arr = end_delay_str.split(",")
        end_delay = []
        for i in range(1,len(end_delay_arr) -1):
            end_delay.append(float(end_delay_arr[i]) / 1000) 

        frame_type_arr = frame_type_str.split(",")
        frame_type = []
        for i in range(1,len(frame_type_arr) -1):
            frame_type.append(int(frame_type_arr[i]))  

        quality_arr = quality_str.split(",")
        quality = []
        for i in range(1,len(quality_arr) -1):
            quality.append(int(quality_arr[i])) 

        cdn_has_frame_arr = cdn_has_frame_str.split("]")
        cdn_has_frame = []
        for i in range(0,2):
            temp = cdn_has_frame_arr[i].split(",")
            cdn_has_frame.append(int(temp[1]))
        
        rebuf_time = float(rebuf_time_str) / 1000
        cdn_flag = int(cdn_flag_str) 
        buffer_flag = int(buffer_flag_str) 
        #if hasattr(g, 'abr1'):
        #abr1 = ABR.Algorithm()
        #abr1.Initial()
        bit_rate = 0
        target_buffer = 1.0
        print("------",teamid, time1.time())
        abr1.Initial()
        bit_rate, target_buffer = abr1.run(time_interval, send_data_size,frame_time_len,frame_type,quality,buffer_size,end_delay,\
                                      rebuf_time, cdn_has_frame, cdn_flag, buffer_flag) 
        if abr1  in locals() or abr1 in globals():
           bit_rate, target_buffer = abr1.run(time_interval, send_data_size,frame_time_len,frame_type,quality,buffer_size,end_delay,\
                                      rebuf_time, cdn_has_frame, cdn_flag, buffer_flag) 
        else:
           print("budui----------------------------------------------")
           abr1 = ABR.Algorithm()
           abr1.Initial()
           bit_rate, target_buffer = g.abr1.run(time_interval, send_data_size,frame_time_len,frame_type,quality,buffer_size,end_delay,\
                                      rebuf_time, cdn_has_frame, cdn_flag, buffer_flag) 
        print("time ",timestamp,
              "time_interval ", time_interval,
              "size " ,send_data_size, 
              "frame_time_len ",frame_time_len, 
              "rebuf ", rebuf_time_str,
              "buffer size ", buffer_size, 
              "end delay ",end_delay,
              "buffer falg ",buffer_flag,
              "cdn_flag ",cdn_flag,
              "cdn_has_frame ",cdn_has_frame,
              "bit_rate ", bit_rate,
               "target_buffer ",  target_buffer)
        #bit_rate = 500
        #target_buffer = 1000
        #bit_rate = 1
        result = str(int(BIT_RATE[bit_rate])) + " " + str(target_buffer * 1000)
        print(result)
        return result
'''

@app.route('/hello/')
def hello():
    #import sys 
    #reload(sys) 
    #sys.setdefaultencoding('utf8') 
    name = request.args.get('name',None)
    #name_decode=urllib.parse.unquote(name)
    #name_decode = name.encode('utf-8')
    #print(type(name))
    path =u"/root/mmgc/team/" + name
    #print(path)
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
        shutil.copyfile("/root/mmgc/team/online.py",path +u"/online.py")   
        return "{'result':'1'}"
    else:
        return "{'result':'0'}"
    #db = pymysql.connect("localhost","root","sayd199511","user_info")

@app.route('/call_run/')
def call_run():
     user_id_encode = request.args.get('id')
     file_name_encode = request.args.get('fname')
     old_name_encode = request.args.get('old_fname')
     user_id = urllib.parse.unquote(user_id_encode)
     file_name = urllib.parse.unquote(file_name_encode)
     old_fname = urllib.parse.unquote(old_name_encode)
     print(file_name_encode, file_name, old_fname)
     try:
        _thread.start_new_thread( run, (user_id, file_name, old_fname) )
     except:
        print("Error: unable to start thread")
     return  "已开始运行"
     '''time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
     db = pymysql.connect(
                           host='107.182.182.18',
                           port= 3306 ,
                           user= 'root',
                           passwd='pwd_aitrans',
                           db='user_info')
     cursor = db.cursor()
     #print("/home/team/" +user_id + "/" + file_name)
     z = zipfile.ZipFile( u"/home/team/" +user_id + u"/" + file_name, 'r')
     z.extractall(path= u'/home/team/'+ user_id + u"/" )
     z.close()
     try:
         sys.path.append(u"/home/team/" + user_id + u"/") 
         import online
         result =  online.test(user_id) 
         sys.path.remove(u"/home/team/" + user_id + u"/") 
     except ImportError:
         sql = "INSERT INTO pre_result  VALUES ('%s' , 'ABR.py','%s', %s,'import file error');"%(user_id, time, 0)
         try:
             cursor.execute(sql)
             print("Import Error")
             db.commit()
             db.close()
         except:
             traceback.print_exc()
             db.rollback()
             db.close()          
         return "0"
     except SyntaxError:
         sql = "INSERT INTO pre_result  VALUES ('%s' , 'ABR.py','%s', %s,'run programmer Syntax error');"%(user_id, time, 0)
         try:
             cursor.execute(sql)
             print("Synatax Error")
             db.commit()
             db.close()
         except:
             traceback.print_exc()
             db.rollback()
             db.close()          
         return "0"
     except:
         sql = "INSERT INTO pre_result  VALUES ('%s' , 'ABR.py','%s', %s,' unkown error');"%(user_id, time, 0)
         try:
             cursor.execute(sql)
             print("Unkown Error")
             db.commit()
             db.close()
         except:
             traceback.print_exc()
             db.rollback()
             db.close()          
         return "0"
     else:
         sql = "INSERT INTO pre_result  VALUES ('%s' , 'ABR.py','%s', %s,'NULL ');"%(user_id, time, result)
         try:
             cursor.execute(sql)
             db.commit()
             print("success")
             db.close()
         except:
             traceback.print_exc()
             db.rollback()
             db.close()          
         return str(result)'''

@app.route('/ID_INFO/',methods=["GET","POST"],strict_slashes=False)
def id_upload():
    error=None
    ID_number=request.form["ID_number"]
    print(ID_number)
    file_dir = os.path.join(basedir, app.config['ID_UPLOAD_FOLDER']) 
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)  
    f1=request.files['ID_Card_Front'] 
    if f1 and id_allowed_file(f1.filename):  
        fname=f1.filename
        ext = fname.rsplit('.', 1)[1] 
        new_filename =ID_number+'_front'+'.'+ext   
        f1.save(os.path.join(file_dir, new_filename))  
        f2=request.files['ID_Card_Back'] 
        if f2 and id_allowed_file(f2.filename):  
            fname=f2.filename
            ext = fname.rsplit('.', 1)[1] 
            new_filename =ID_number+'_back'+'.'+ext   
            f2.save(os.path.join(file_dir, new_filename)) 
        else:
            error= "Please upload a png image"          
    else:
        error="Please upload a png image"
    #response.addHeader("Access-Control-Allow-Origin", "*")
    data={}
    data['error']=error
    resp  = jsonify(data)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    #return json.dumps(data,ensure_ascii=False)
    return resp
@app.route("/")
def root():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("index.html",login_name=username)
@app.route('/home')
def base():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("index.html",login_name=username)

@app.route('/index/lan=en')
def base_en():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("index_en.html",login_name=username)

@app.route("/logout")
def logout():
    session.pop('login_name',None)
    return redirect(url_for("base"))

@app.route('/competition_list/')
def com_list():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("competition_list.html",login_name=username)

@app.route('/competition_list/lan=en')
def com_list_en():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("competition_list_en.html",login_name=username)

@app.route('/competition_detail/competition_id=2')
def com_id_2():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("competition_id=2.html",login_name=username)

@app.route('/competition_detail/competition_id=2/lan=en')
def com_id_2_en():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("competition_id=2_lan=en.html",login_name=username)

@app.route('/competition_detail/competition_id=1')
def com_id_1():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("competition_id=2.html",login_name=username)

@app.route('/competition_detail/competition_id=1/lan=en')
def com_id_1_en():
    username=None
    if 'login_name' in session:
        username=session['login_name']
    return render_template("competition_id=1_lan=en.html",login_name=username)

@app.route('/iaccount/reg_user/',methods=["GET","POST"])
def getRigistRequest():
    error=''
    db = pymysql.connect("localhost","root","pwd_aitrans","user_info" )

    cursor = db.cursor()

    print(request.form)
    email=request.form['email']
    password=request.form['password']
    school=request.form['school']
    name=request.form['username']

    sql = "select * from info where email="+"'"+email+"'"
    cursor.execute(sql)
    results=cursor.fetchall()
    if len(results)==1:
        print("youxiang")
        db.close()
        error="This email has been registered!"
    else:
        sql="select * from info where email="+"'"+name+"'"
        cursor.execute(sql)
        results=cursor.fetchall()
        if len(results)==1:
            print("sssss")
            db.close()
            error="This nickname already exists."
        else:           
            sql = "INSERT INTO info(email, password, school, name) VALUES ("+"'"+email+"',"+"'"+password+"',"+"'"+school+"',"+"'"+name+"')"
            print(sql)
            try:
                cursor.execute(sql)
                db.commit()
                print("success") 
                db.close()
            except:
                traceback.print_exc()
                db.rollback()
                db.close()
    data={}
    data['error']=error
    return json.dumps(data,ensure_ascii=False)
        

@app.route('/iaccount/login/',methods=["GET","POST"])
def getLoginRequest():
    username=None
    error=None
    db = pymysql.connect("localhost","root","pwd_aitrans","user_info" )
    cursor = db.cursor()
    sql = "select * from info where email="+"'"+request.form['email']+"'"+" and password="+"'"+request.form['password']+"'"+""
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        if len(results)==1:
            db.close()
            username=results[0][3]
            session['login_name']=username
              
            #return redirect(url_for("base_en"))    
        else:
            error="Invalid email or password"
            db.close()
        data={}
        data['username']=username
        data['error']=error
        print(data)
        return json.dumps(data,ensure_ascii=False)
    except:
        traceback.print_exc()
        db.rollback()
        db.close()
        return redirect(url_for("base",login_name=None))

@app.route('/upload/',methods=["GET","POST"],strict_slashes=False)
def upload():
    error=None
    username=None
    if 'login_name' in session:
        username=session['login_name']
        print("uploading")
        print(request.files)
        file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER']) 
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)  
        f=request.files['code']  
        if f and allowed_file(f.filename):  
            fname=f.filename
            ext = fname.rsplit('.', 1)[1] 
            unix_time=int(time.time())
            new_filename = username+'_'+str(unix_time)+'.'+ext   
            f.save(os.path.join(file_dir, new_filename))
        else:
            error="Wrong Sytax"
    else:
        error="Please login"
    data={}
    data['error']=error
    return json.dumps(data,ensure_ascii=False)



    


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
if __name__ == '__main__':
    app.run(debug=False)


