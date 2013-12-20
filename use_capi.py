""" use_capi.py
demonstrates how to use the canvasAPI.py wrapper

This particular script creates a CSV of completion of quizzes 
by a particular set of students
"""
import urllib2
import json

import canvasAPI as capi 
reload(capi) # Make sure using current version
import os.path

def be_user():
    '''set the state of the canvasAPI to pltw, cse-plc, bennett
    '''
    # Place user's token here. Obtain a token on the user's settings page.
    capi.set_token('insert_your_own')
    print "set token"
    # for PLTW
    site = 'pltw.instructure.com'
    capi.set_site(site)
    
    pilot = ['Student 1','etc.']
    capi.set_section_roster(pilot)
    
    #CSE-PLC
    CSE = '11111'
    # this is global variable in 
    capi.set_course(CSE, pilot)
        
def run_fb(file_name):
    '''Call this function to produce a file showing all students'
    completion of quizzes in the course. Saves report.csv in the working directory.    
    '''   
    fileout=open(file_name,'w')
    titles, fb = capi.check_completion()
    fileout.write('student name,') 
    for title in titles:
        fileout.write(title+',')
    fileout.write('\n')
    for f in fb:
        fileout.write(f[f.find(' '):] + ',' + f + ',')
        for letter in fb[f]:
            fileout.write(letter + ',')
        fileout.write('\n')
    fileout.close()
    
#####
# Create a grid showing completion of quizzes
#####
if __name__ == "__main__":   
    be_user() #use my token, course, and site
    
    # Construct the filename for the output file
    directory = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(directory,'quiz_completion.csv')
    
    # Be visible. Get data.
    print "Collect all reports ('y' to continue)?"
    confirm = raw_input()
    if confirm=="y":
        print "Producing report of feedback completion. Writing results to "+ filename
        run_fb(filename)
        print "Output complete. See results in "+filename