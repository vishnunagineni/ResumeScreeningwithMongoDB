from array import array
from flask import Flask,render_template,request,jsonify
from flask_cors import CORS
import os
#os.environ['TIKA_SERVER_JAR'] = 'E:\PYTHON\tika\tika-server-1.27.jar'
import json
import zipfile
from flask_pymongo import PyMongo
from tika import parser
from datetime import datetime
from models import generatengrams,generaterandomjobs,extractdata,cleaning, measure_similarity,update_humanreview,getjodId
from werkzeug.utils import redirect, secure_filename

app=Flask(__name__)
app.config['DEBUG']=True


#database configuration
fd=open('./dbconfig.json')
conf=json.load(fd)
config=conf["dbcon"]
host=conf["host"]
fd.close()

#local storage configuration
UPLOAD_FOLDER = './static'
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

CORS(app)
#connecting mongodb 
app.config["MONGO_URI"]="mongodb://localhost:27017/resume_screening"
mongo=PyMongo(app)
db=mongo.db
n_grams=[1,2,3]
tper=50

#<--------------------Home------------------------>
@app.route('/')
def home():
    return render_template('upload.html')

#<--------------Get list of job openings-------------->
@app.route('/getlistofjobs',methods=['GET'])
def getlistofjobs():
    try:
        data=generaterandomjobs()
        return jsonify(data)
    except:
        return jsonify('Error Encountered!!')

#<--------------Getting Job Details....--------------->

@app.route('/getjobdetails/<id>',methods=['GET'])
def getjobdetails(id):    
    try:
        if id:
            data={}
            job_details=db.job_description.find_one({"id":id})
            data["id"]=job_details["id"]
            data["role"]=job_details["role"]
            data["title"]=job_details["title"]
            data["experience"]=job_details["experience"]
            data["location"]=job_details["location"]
            data["job_type"]=job_details["job_type"]
            data["job_keywords"]=job_details["job_keywords"]
            data["responsibilities"]=job_details["responsibilities"]
        return data
    except:
        return jsonify('Something Went Wrong!!!')
#<------------------uploading Resumes---------------------->
@app.route('/uploadresumes/<id>',methods=['POST'])
def resumesupload(id):
    try:
        path=os.path.join(UPLOAD_FOLDER,'uploadedresumes')
        ct=datetime.now().date()
        if os.path.exists(path):
            pass
        else:
            os.mkdir(path)
        if path:
            if request.method=='POST':
                jd=db.job_description.find_one({"id":id})
                print(jd["resumes"])
                dbreslist=jd["resumes"]
                #print(dbreslist)
                if request.files.getlist("folder"):
                    rlist=[]
                    files=request.files.getlist('folder')
                    for file in files:    
                        fname=os.path.basename(file.filename)
                        print(fname)
                        fs=os.path.join(path,secure_filename(fname))
                        if os.path.exists(fs):
                            d={}
                            d[fname]='NULL'
                            rlist.append(d)
                        else:
                            file.save(fs)
                            d={}
                            d[fname]='NULL'
                            rlist.append(d)
                    print(rlist)
                    new_reslist=dbreslist                   
                    new_reslist.extend(res for res in rlist if res not in new_reslist)
                else:
                    files=request.files.getlist("file")
                    rlist=[]
                    for file in files:
                        print(file.filename)
                        if file.filename.endswith('.zip'):
                            temppath=os.path.join(path,secure_filename(file.filename))
                            file.save(temppath)
                            zip=zipfile.ZipFile(temppath)
                            zipfiles=zip.namelist()
                            with zipfile.ZipFile(temppath,'r') as z:
                                z.extractall(path)
                            for f in zipfiles:
                                print(f)
                                d={}
                                d[f]="NULL"
                                rlist.append(d)
                        else:
                            fname=secure_filename(file.filename)
                            fs=os.path.join(path,secure_filename(file.filename))
                            if os.path.exists(fs):
                                d={}
                                d[fname]='NULL'
                                rlist.append(d)
                            else:
                                file.save(fs)
                                d={}
                                d[fname]='NULL'
                                rlist.append(d)
                        new_reslist=dbreslist                   
                        new_reslist.extend(res for res in rlist if res not in new_reslist)
                    print(new_reslist)
                db.job_description.update({"id":id},{"$set":{"uploaded_resumes":new_reslist}})
        return jsonify('Inserted!!!')
    except:
        return jsonify('Something Went Wrong!!!')
        
#<-----------------Screening Resumes-------------------->

@app.route('/screenresumes/<id>',methods=['GET'])
def resumescreening(id):
    try:
        if os.path.exists(copy_path):
            jd=db.job_description.find_one({"id":id})
            res=jd["uploaded_resumes"]
            rnames=list(res[0].keys())
            rname=str(rnames[0])
            folder=rname.split('/')
            if len(folder)>1:
                foldername=folder[0]
            else:
                foldername=""
            screen_data={}
            screen_data["totalUploadedResumes"]=len(res)
            keywords=jd["job_keywords"]
            screen_data["JD Keywords"]=keywords
            shortlisted=[]
            rejected=[]
            keywords=keywords.split(',')
            keywords=" ".join(keywords)
            #keywords=cleaning(keywords)
            path=os.path.join(copy_path,foldername)
            if len(foldername)>0:
                for file in os.scandir(path):
                    for i in res:
                        rnames=list(i.keys())
                        #rnames=rnames[0]
                        rname=str(rnames[0]).split('/')[1]
                        if file.name==rname:
                            d={}
                            if len(res)>0:
                                cname=file.name.split('.')[0]
                            else:
                                cname=""
                            d["candidateName"]=cname
                            d["uploadedOn"]=jd["created_on"]
                            data=extractdata(file.path)
                            cleaned_data=data
                            #cleaned_data=cleaning(data)
                            #entities=extract_entities(cleaned_data)
                            #print(entities)
                            sl=[]
                            for j in n_grams:
                                resume_ngrams=generatengrams(cleaned_data,j)
                                keywords_ngrams=generatengrams(keywords,j)
                                sim=measure_similarity(resume_ngrams,keywords_ngrams)
                                sl.append(sim*j)
                            similarity=max(sl)
                            similarity=similarity*100
                            d["resumedId"]=rnames[0]
                            d["keywordsMatch"]=similarity
                            d["isHumanReviewed"]=i[rnames[0]]
                            d["resumePath"]='static'+'/'+'uploadedresumes'+'/'+foldername+'/'+file.name
                            if i[rnames[0]]=='Y':
                                #update_humanreview(i[0],'N')
                                shortlisted.append(d)
                            elif similarity>tper and i[rnames[0]]=='N':
                                rejected.append(d)
                                #update_humanreview(i[0],'N')
                            elif similarity>tper:
                                shortlisted.append(d)
                            else:
                                rejected.append(d)
            else:
                for file in os.scandir(path):
                    for i in res:
                        rnames=list(i.keys())
                        rname=str(rnames[0])
                        if file.name==rname:
                            d={}
                            if len(res)>0:
                                cname=file.name.split('.')[0]
                            else:
                                cname=""
                            d["resumeName"]=cname
                            d["candidateName"]=cname
                            d["uploadedOn"]=jd["created_on"]
                            data=extractdata(file.path)
                            #cleaned_data=cleaning(data)
                            cleaned_data=data
                            sl=[]
                            for j in n_grams:
                                resume_ngrams=generatengrams(cleaned_data,j)
                                keywords_ngrams=generatengrams(keywords,j)
                                sim=measure_similarity(resume_ngrams,keywords_ngrams)
                                sl.append(sim*j)
                            similarity=max(sl)
                            similarity=similarity*100
                            print(similarity)
                            d["resumeId"]=rname
                            #s=s+similarity
                            d["keywordsMatch"]=similarity
                            d["isHumanReviewed"]=i[rname]
                            d["resumePath"]='static'+'/'+'uploadedresumes'+foldername+'/'+file.name
                            if i[rname]=='Y':
                                #update_humanreview(i[0],'N')
                                shortlisted.append(d)
                            elif similarity>tper and i[rname]=='N':
                                rejected.append(d)
                                #update_humanreview(i[0],'N')
                            elif similarity>tper:
                                shortlisted.append(d)
                            else:
                                rejected.append(d)
            screen_data["shortlisted"]=shortlisted
            screen_data["rejected"]=rejected
        return screen_data
    except:
        return jsonify('ERROR Encountered!!!!')
    

#<-----------------Human Review------------------->
# Please Enter URL like this http://localhost:5000/humanreview?resumeId=1193&humanreview=false   

@app.route('/humanreview',methods=['GET','POST'])
def human_review():
    try:
        arguments=request.args.to_dict()
        jobid=arguments["jobId"]
        rid=arguments["resumeId"]
        ishumanreviewed=arguments["humanreview"]
        if jobid:
            if ishumanreviewed=='false':
                update_humanreview(jobid,rid,'N') 
            if ishumanreviewed=='true':
                update_humanreview(jobid,rid,'Y')
        return jsonify('Completed!!!!')
    except:
        return jsonify('Error Encountered!!')


if __name__ == '__main__':
    #creating example folder to store the data
    copy_path=os.path.join(UPLOAD_FOLDER,'uploadedresumes')
    jsonpath=os.path.join(UPLOAD_FOLDER,'json')
    app.run(host=host)