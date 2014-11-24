#!/usr/bin/env python
__author__ = 'greghines'
import numpy as np
import os
import pymongo
import sys
import cPickle as pickle
import bisect

if os.path.exists("/home/ggdhines"):
    base_directory = "/home/ggdhines"
else:
    base_directory = "/home/greg"

def index(a, x):
    'Locate the leftmost value exactly equal to x'
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    raise ValueError

sys.path.append(base_directory+"/github/pyIBCC/python")
import ibcc

if os.path.exists("/home/ggdhines"):
    sys.path.append("/home/ggdhines/PycharmProjects/reduction/experimental/clusteringAlg")
else:
    sys.path.append("/home/greg/github/reduction/experimental/clusteringAlg")
#from divisiveDBSCAN import DivisiveDBSCAN
from divisiveDBSCAN_multi import DivisiveDBSCAN
from divisiveKmeans import DivisiveKmeans

if os.path.exists("/home/ggdhines"):
    base_directory = "/home/ggdhines"
else:
    base_directory = "/home/greg"

client = pymongo.MongoClient()
db = client['condor_2014-11-20']
classification_collection = db["condor_classifications"]
subject_collection = db["condor_subjects"]




big_userList = []
big_subjectList = []
animal_count = 0

f = open(base_directory+"/Databases/condor_ibcc.csv","wb")
f.write("a,b,c\n")
alreadyDone = []

for ii,classification in enumerate(classification_collection.find()):
    print ii
    if classification["subjects"] == []:
        continue
    zooniverse_id = classification["subjects"][0]["zooniverse_id"]



    if "user_name" in classification:
        user = classification["user_name"]
    else:
        user = classification["user_ip"]

    if not(user in big_userList):
        big_userList.append(user)
    if not(zooniverse_id in big_subjectList):
        big_subjectList.append(zooniverse_id)

    user_index = big_userList.index(user)
    subject_index = big_subjectList.index(zooniverse_id)

    try:
        user_index = index(alreadyDone,(user_index,subject_index))
        continue
    except ValueError:
        bisect.insort(alreadyDone,(user_index,subject_index))


    try:
        mark_index = [ann.keys() for ann in classification["annotations"]].index(["marks",])
        markings = classification["annotations"][mark_index].values()[0]

        found = False
        for animal in markings.values():


            try:
                animal_type = animal["animal"]
                if animal_type in ["condor"]:
                    found = True
                    break

            except KeyError:
                pass


        if found:
            f.write(str(user_index) + ","+str(subject_index) + ",1\n")
        else:
            f.write(str(user_index) + ","+str(subject_index) + ",0\n")

    except ValueError:
        pass



f.close()
with open(base_directory+"/Databases/condor_ibcc.py","wb") as f:
    f.write("import numpy as np\n")
    f.write("scores = np.array([0,1])\n")
    f.write("nScores = len(scores)\n")
    f.write("nClasses = 2\n")
    f.write("inputFile = \""+base_directory+"/Databases/condor_ibcc.csv\"\n")
    f.write("outputFile = \""+base_directory+"/Databases/condor_ibcc.out\"\n")
    f.write("confMatFile = \""+base_directory+"/Databases/condor_ibcc.mat\"\n")
    #f.write("nu0 = np.array([30,70])\n")
    #f.write("alpha0 = np.array([[3, 1], [1,3]])\n")



#start by removing all temp files
try:
    os.remove(base_directory+"/Databases/condor_ibcc.out")
except OSError:
    pass

try:
    os.remove(base_directory+"/Databases/condor_ibcc.mat")
except OSError:
    pass

try:
    os.remove(base_directory+"/Databases/condor_ibcc.csv.dat")
except OSError:
    pass

pickle.dump((big_subjectList,big_userList),open(base_directory+"/Databases/tempOut.pickle","wb"))
ibcc.runIbcc(base_directory+"/Databases/condor_ibcc.py")


