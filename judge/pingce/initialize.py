import pymysql
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

def hello():
    #import sys 
    #reload(sys) 
    #sys.setdefaultencoding('utf8') 
    db = pymysql.connect(
                        host='107.182.182.18',
                        port= 3306 ,
                        user= 'root',
                        passwd='pwd_aitrans',
                        db='user_info')
    cursor = db.cursor()
    sql = "select teamname from mmgc;"
    cursor.execute(sql)
    name_list = cursor.fetchall()
    #name_decode=urllib.parse.unquote(name)
    #name_decode = name.encode('utf-8')
    #print(type(name))
    for name in name_list:
        print(name)
        path =u"/root/mmgc/team/" + name[0]
        #print(path)
        folder = os.path.exists(path)
        if folder:
            shutil.rmtree(path)
        
        os.makedirs(path)
        shutil.copyfile("/root/mmgc/team/run.py",path +u"/run.py")
        shutil.copyfile("/root/mmgc/team/fixed_env.py",path +u"/fixed_env.py")
        shutil.copyfile("/root/mmgc/team/load_trace.py",path +u"/load_trace.py")
        os.makedirs(path+u"/submit")
        shutil.copyfile("/root/mmgc/master/submit/submit/ABR.py",path+u"/submit/ABR.py")

    #db = pymysql.connect("localhost","root","sayd199511","user_info")

hello()
