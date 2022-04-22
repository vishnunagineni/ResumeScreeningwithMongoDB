import re
import nltk
#os.environ['TIKA_SERVER_JAR'] = 'E:\tika\tika-server-1.27.jar'
import tika
tika.TikaClientOnly = True
from tika import parser
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('stopwords')
sw=stopwords.words("english")
from pymongo import MongoClient
mongo=MongoClient("mongodb://localhost:27017")
db=mongo.resume_screening
def extractdata(path):
    data=parser.from_file(path,'http://localhost:9998/')
    data=data['content']
    data=" ".join(data.split())
    return data

def generatengrams(data,n):
    data=re.sub(r'[^a-zA-Z0-9\s]',' ',data)
    tokens=[token for token in data.split(" ") if token!=""]
    ngrams=zip(*[tokens[i:] for i in range(n)])
    return [" ".join(ngram) for ngram in ngrams]

def cleaning(data):
    data=data.lower()
    words=word_tokenize(data)
    words_wo_stopwords=[word for word in words if not word in sw]
    d=" ".join(words_wo_stopwords)
    return d

def generaterandomjobs():
    # jobid=['JD101','JD102','JD103','JD104','JD105','JD106','JD107','JD108','JD109','JD110']
    # location=['Pune','Hyderabad','Pune','Bangalore','Hyderabad','Bangalore','Pune','Hyderabad','Pune','Bangalore']
    # titles=['Solution Architect','Fullstack Developer','Java Developer','AI Developer','Python Developer','Frontend Developer','Devops Engineer','Cloud Architect','Data Analyst','Programmer Analyst']
    listofjobs=[]
    res=db.job_description.find()
    try:
        for i in res:
            d={}
            d["jobCode"]=i["id"]
            d["designationTitle"]=i["title"]
            d["location"]=i["location"]
            d["totalUploadedResumes"]=len(i["uploaded_resumes"])
            listofjobs.append(d)
        return listofjobs
    except:
        print('Database Error')


def measure_similarity(x,y):
    common=set.intersection(set(x),set(y))
    union=set.union(set(x),set(y))
    sim=len(common)/len(y)
    return sim

def update_humanreview(jid,rid,value):
    try:  
        if jid:
            #print(jid)
            jd=db.job_description.find_one({"id":jid})
            res=jd["uploaded_resumes"]
            for i in res:
                for key in i.keys():
                    if key==rid:
                        i.update({key:value})
                        break
            db.job_description.update({"id":jid},{"$set":{"uploaded_resumes":res}})
    except:
        print('Error Encountered!!!')

def getjodId(id):
    #conn=conn=mysql.connector.connect(**config)
    try:
        if True:
            print(False)
    except:
        print('Error Encountered!!!')

