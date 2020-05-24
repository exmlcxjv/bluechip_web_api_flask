import flask
from flask import request, jsonify, redirect

import os
import shutil

import os.path
from os import path

import uuid

import mysql.connector
from mysql.connector import Error

from apscheduler.schedulers.background import BackgroundScheduler


able_to_process = True

app = flask.Flask(__name__, static_url_path='/static')

app.config['APPLICATION_ROOT'] = "/abc/def"


def image_process_to_obj():
    with app.app_context():
        global able_to_process

        if able_to_process:
            print('FUNC process image : Job started...')
            # do db connections
            mydb = mysql.connector.connect(host='sgp40.siteground.asia',
                                        database='nobleide_bluechip_web_api',
                                        user='nobleide_admin',
                                        password='rootroot')
            mycursor = mydb.cursor()
            # get from model table which status pending, use limit 1
            try:
                mycursor.execute("SELECT uuid,folder_name FROM model WHERE status ='pending' LIMIT 1")
                all_res = mycursor.fetchall()
                for result in all_res:
                    uuid = result[0]
                    name = result[1]

                if not all_res:
                    # nothing to process
                    print('FUNC process image : NA task from db, all are processed')
                else:
                    # if >0 with status pending record in model
                    print('FUNC process image : Task started on : uuid : '+uuid)
                    print('FUNC process image : Task started on : model : '+name)

                    # change able_to_process to FALSE
                    able_to_process = False

                    #### pending task : start process the model
                    ############
                    ########################
                    print('FUNC process image : Start processing........')
                    mycursor.execute("UPDATE model SET status = 'processing' WHERE uuid = '"+uuid+"'")
                    mydb.commit()

                    # after process is done
                    print('FUNC process image : Processing is done........')
                    mycursor.execute("UPDATE model SET status = 'processed' WHERE uuid = '"+uuid+"'")
                    mydb.commit()

                    #### pending task : send push notification to app
                    ##########
                    ###################
                    
                    # change able_to_process to TRUE
                    able_to_process = True
            except Exception:
                print('FUNC process image : error')
            finally:
                mycursor.close()
                mydb.close()
                print('FUNC process image : Job ended')
                print('')
                


        else:
            print('FUNC process image : No available resources, another job is running')
            print('FUNC process image : Job ended')


@app.route('/', methods=['GET'])
def index():
    return '''<h1>Bluechip Web Api </h1>
    <ul>
        <li><a href="/flask/bluechip/api/users/all">Get All Registered Users<br>
        METHOD : GET <br>
        URL : '/flask/bluechip/api/users/all'</a></li></br>

        <li>Get Registered User By Provider Token <br>
        METHOD : POST <br>
        URL : '/flask/bluechip/api/users' <br>
        PARAMS : 'provider_token'</li></br>

        <li>Add New User And Create User Directory in FS<br>
        METHOD : POST <br>
        URL : '/flask/bluechip/api/users/insert'<br>
        PARAMS : 'name', 'email', 'provider_token' </li></br>

        <li>Upload Photo from App, create MySQL Record and Store in FS <br>
        METHOD : POST <br>
        URL : '/flask/bluechip/api/upload'<br>
        BODY : 'name', 'file[]', 'provider_token'</li></br>

        <li>Get Model Detail By Provider Token <br>
        METHOD : POST <br>
        URL : '/flask/bluechip/api/models' <br>
        PARAMS : 'provider_token' </li></br>


        <li>Delete Model from SQL and FS <br>
        METHOD : POST <br>
        URL : '/flask/bluechip/api/models/delete' <br>
        PARAMS : 'provider_token' , 'id' , 'name'</li></br>
    </ul>'''


@app.route('/test')
def test():
    return redirect("http://www.google.com")


@app.route('/bluechip/api/users/all', methods=['GET'])
def api_user_all():

    mydb = mysql.connector.connect(host='sgp40.siteground.asia',
                                        database='nobleide_bluechip_web_api',
                                        user='nobleide_admin',
                                        password='rootroot')

    mycursor = mydb.cursor()

    try:
        mycursor.execute("SELECT id, name, provider_token, firebase_Token, email FROM user")
        all_res = mycursor.fetchall()
        payload = []
        content = {}

        for result in all_res:
            content = {'id': result[0], 'name': result[1], 'provider_token': result[2], 'firebase_Token': result[3], 'email': result[4]}
            payload.append(content)
            content = {}
    except Exception:
        return 'Error'
    
    finally:
        mycursor.close()
        mydb.close()

    return jsonify(payload)

@app.route('/bluechip/api/users/insert', methods=['POST'])
def api_user_insert():

    mydb = mysql.connector.connect(host='sgp40.siteground.asia',
                                        database='nobleide_bluechip_web_api',
                                        user='nobleide_admin',
                                        password='rootroot')

    mycursor = mydb.cursor()

    try:
        query_parameters = request.args
        name = query_parameters.get('name')
        provider_token = query_parameters.get('provider_token')
        #firebase_token = query_parameters.get('firebase_token')
        email = query_parameters.get('email')


        mycursor.execute("SELECT * FROM user WHERE provider_token='"+provider_token+"'")
        results = mycursor.fetchall()

        msg = ''

        if not results:
            sql = "INSERT INTO user (name, provider_token, email) VALUES (%s, %s, %s)"
            val = (name, provider_token, email)

            mycursor.execute(sql, val)
            mydb.commit()    

            ########################### start creating folder ####################################
            ########################### ONLY works at LINUX ######################################
            ######################## use THIS only in mod_wgix mode ##############################
            folder_path = ('var/www/FlaskApp/bluechipApi/static/'+provider_token)
            ####################### use THIS only in port 5000 mode ##############################
            #folder_path = ('static/'+provider_token)
            os.mkdir(folder_path)
            os.chmod(folder_path,0o777)
            ########################### end of creating folder ###################################


            ########################### start creating folder ####################################
            ########################### ONLY works in WINDOWS ####################################
            ######################## use THIS only in mod_wgix mode ##############################
            #current_directory = os.getcwd()
            #static_folder = ('static')
            #folder_path = os.path.join(current_directory,static_folder, provider_token)
            ####################### use THIS only in port 5000 mode ##############################
            #os.mkdir(path)
            ########################### end of creating folder ###################################

            msg = "success"
        else:
            msg ="user exists"
    except Exception:
        return 'error'
    
    finally:
        mycursor.close()
        mydb.close()
        
    return jsonify(msg)


@app.route('/bluechip/api/users', methods=['POST'])
def api_user_filter():

    mydb = mysql.connector.connect(host='sgp40.siteground.asia',
                                        database='nobleide_bluechip_web_api',
                                        user='nobleide_admin',
                                        password='rootroot')

    mycursor = mydb.cursor()   

    try:
        query_parameters = request.args
        provider_token = query_parameters.get('provider_token')

        mycursor.execute("SELECT * FROM user where provider_token ='"+provider_token+"'")
        all_res = mycursor.fetchall()
        payload = []
        content = {}

        for result in all_res:
            content = {'user_id': result[0], 'name': result[1], 'provider_token': result[2], 'firebase_token': result[3], 'email': result[4]}
            payload.append(content)
            content = {}
    except Exception:
        return 'error'
    finally:
        mycursor.close()
        mydb.close()
    return jsonify(payload)

@app.route("/bluechip/api/upload", methods=["POST"])
def api_upload():

    mydb = mysql.connector.connect(host='sgp40.siteground.asia',
                                        database='nobleide_bluechip_web_api',
                                        user='nobleide_admin',
                                        password='rootroot')

    mycursor = mydb.cursor() 

    try:
        # get provider_token of user
        provider_token = request.form['provider_token']
        # get object name from user
        model_name = request.form['name']

        ################################# IN LINUX ##############################
        ############################## MOD_WGI MODE #############################
        final_directory = ('var/www/FlaskApp/bluechipApi/static/'+provider_token+'/'+model_name)
        ############################# PORT 5000 MODE ############################
        #final_directory = ('static/'+provider_token+'/'+model_name)
        ################################# END ###################################


        ################################# IN WINDOWS ############################
        #current_directory = os.getcwd()
        #static_folder = ('static')
        #final_directory = os.path.join(current_directory,static_folder,provider_token, model_name)
        ################################## END ##################################

   
        if os.path.exists(final_directory):
            return "Duplicated name"
        # if object folder is not found
        else:
            # create object folder
            os.mkdir(final_directory)
            ################### ONLY in LINUX , in WINDOWS pls remove the line below ######################
            os.chmod(final_directory,0o777) 
            print('FUNC photo upload : Object Folder has been created at : '+final_directory)       

            # Insert record into db table model
            sql = "INSERT INTO model (uuid, folder_name,owner_provider_token, status) VALUES (%s, %s, %s,'pending')"
            val = (str(uuid.uuid4()), model_name, provider_token)
            mycursor.execute(sql, val)
            mydb.commit()  
            print('FUNC photo upload : MySQL record has has been inserted into Table : Model')   

            # upload pics into object folder
            uploaded_files = request.files.getlist("file[]")
            for file in uploaded_files:
                file.save(os.path.join(final_directory, file.filename))
                #### ONLY FOR LINUX #####
                os.chmod(os.path.join(final_directory, file.filename),0o777) 
                print('FUNC photo upload : File : ('+file.filename+') saved to '+final_directory)

            # done
            return "FUNC photo upload : success"
    except Exception:
        return 'error'
    finally:
        mycursor.close()
        mydb.close()

@app.route('/bluechip/api/models', methods=['POST'])
def api_model_filter():

    mydb = mysql.connector.connect(host='sgp40.siteground.asia',
                                    database='nobleide_bluechip_web_api',
                                    user='nobleide_admin',
                                    password='rootroot')
    mycursor = mydb.cursor()

    try:
        query_parameters = request.args
        token = query_parameters.get('provider_token')

        mycursor.execute("SELECT id, folder_name, status FROM model WHERE owner_provider_token = '"+token+"'")
        all_res = mycursor.fetchall()
        payload = []
        content = {}

        for result in all_res:
            content = {'id': result[0], 'folder_name': result[1], 'status': result[2]}
            payload.append(content)
            content = {}
    except Exception:
        return 'error'
    
    finally:
        mycursor.close()
        mydb.close()

    return jsonify(payload)


@app.route('/bluechip/api/models/delete', methods=['POST'])
def api_model_remove():

    mydb = mysql.connector.connect(host='sgp40.siteground.asia',
                                    database='nobleide_bluechip_web_api',
                                    user='nobleide_admin',
                                    password='rootroot')
    mycursor = mydb.cursor()

    try:
        query_parameters = request.args
        provider_token = query_parameters.get('provider_token')
        id = query_parameters.get('id')
        name = query_parameters.get('name')

        sql = "DELETE FROM model WHERE owner_provider_token = %s AND id = %s"
        val = (provider_token, id)
        mycursor.execute(sql, val)
        mydb.commit()  

        ################### LINUX ONLY ################
        ################# MOD_WSGI MODE ###############
        shutil.rmtree('var/www/FlaskApp/bluechipApi/static/'+provider_token+'/'+name+'')

        return('successful deleted')
        
    except Exception:
        return 'error'
    
    finally:
        mycursor.close()
        mydb.close()



@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


################# TASK RUNNING AT EVERY 1 MINUTE ################
scheduler = BackgroundScheduler()
job = scheduler.add_job(image_process_to_obj, 'interval', minutes=1)
scheduler.start()

#app.run()
if __name__ == "__main__":
    app.run()
