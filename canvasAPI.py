""" canvasAPI.py
Defines several functions that wrap a small portion of the web-based
Instructure Canvas API
"""
import urllib2
import json

####
# The state object retains the API user's information to reduce the arguments
# that must be sent to functions in this library with each call.
# These global variables can be set with set_<API-global>(state_value)
####
class State(object):
    def __init__(self):
        return
        
state = State()
state.SITE=''
state.COURSE=''
state.TOKEN=''
state.SECTION=[] 

def set_token(token):
    """sets the state of canvasAPI functions to use token
    """
    state.TOKEN = token
    return

def set_site(site):
    """sets the state of canvasAPI functions to use site
    """
    state.SITE = site
    return

def set_course(course, students=None):
    """sets the state of canvasAPI functions to use course
    """
    state.COURSE = course
    if students==None:
        state.SECTION = get_students()
    return      

def set_section_roster(students):
    """sets the state of canvasAPI functions to use section
    """
    state.SECTION = students    
    return    

#####
# The get_all() function is used across the rest of the functions in this
# library 
####
    
def get_all(api_call):
    """Aggregates several pages because Canvas only returns 10 results per page.
    
    Although this pagination can be set, this approach avoids an upper limit
    api_call should be a string that follows /api/v1/
    Example: get_all('courses/10101/quizzes')
    """
    #open an http stream
    #print 'getting: '+'https://'+state.SITE+'/api/v1/'+       api_call+'?access_token='+state.TOKEN
    result_of_get = urllib2.urlopen('https://'+state.SITE+'/api/v1/'+\
        api_call+'?per_page=50&access_token='+state.TOKEN)
    # fetch all content as a string
    content = result_of_get.read()
    # convert to a JSON object
    content_list=json.loads(content)
    
    #There may be more content; get the rest
    
    #Find out if there are more, using the header
    info=dict(result_of_get.info())
    try:
        pages = info['link'].split(',') #current,next,first,last 
    except KeyError: #if this was the only page
        return content_list
    
    #get the next page and append to content_list
    while True: #repeat until there isn't another page
        # Parse the links from the header
        links = {} #initialize an empty dictionary to store the header's link element data
        for link in pages: # pages is comma-separated info from the link element of the header
            url, rel = link.split(';') # URL link and its relation to current page
            rel = rel[6:-1] # strip ' rel="' and closing '"'
            url = url[1:-1] #strips '<' and '>' from url
            links[rel]=url # build a dictionary so that link['next'] will have the desired URL
        # 
        try:
            result_of_get = urllib2.urlopen(links['next']+'&access_token='+state.TOKEN)
        except KeyError: # Done since there is no 'next' 
            return content_list
        content = result_of_get.read()
        content_list += json.loads(content) #append the new page's content
        #refresh pages variable with the link element of the new page's header for the next iteration
        info=dict(result_of_get.info())
        pages = info['link'].split(',') #current,next,first,last 
        
    
####
# These functions return lists of information for a course.
####

def get_students():
    '''returns a list of the name fields of each person in Student role
    '''
    
    people = get_all('courses/'+state.COURSE+'/enrollments')
    names=[]
    for person in people:
        if person['role'] == 'StudentEnrollment':
            names += [person['user']['name']]
    return names
                                                                            
def get_quiz_list():
    ''' returns a list of 2-tuples of all quizzes in a course
    
    Each 2-tuple is (Canvas quiz ID, quiz title)
    which are (int, string)
    '''
    
    #use get_all because of Canvas pagination
    quizlist = get_all('courses/'+state.COURSE+'/quizzes')
    ids = []
    for quiz in quizlist:
        qid = quiz['id']
        qtitle=quiz['title']            
        ids += [(qid, qtitle)]
    return ids
    
def get_files():
    '''Get file names. Returns [(id,filename),...] 
    '''
    files = get_all('courses/'+state.COURSE+'/files')
    #reduce to a list of (id, filename) tuples
    file_tuples = []
    for filedict in files:
        file_tuples.append((filedict['id'],filedict['filename']))
    return file_tuples
    
#####
# These functions deal with quiz reports
#####
             
def get_quiz_report(quiz):
    '''Returns a Canvas quiz report    
    quiz is an int, a Canvas quiz number
    '''    
    # POST quizzes/:quiz_id/report       student_analysis
    f=urllib2.urlopen('https://'+state.SITE+'/api/v1/courses/'+\
        state.COURSE+'/quizzes/'+str(quiz)+'/reports?access_token='+\
        state.TOKEN,'quiz_report[report_type]=student_analysis')
    output = f.read()
    nice_output = json.loads(output)
    report_number = nice_output['id']
    
    # get (with POST) the quiz report csv file
    finished = False
    while not finished:
        try:
            report_meta_file=urllib2.urlopen(\
                'https://'+state.SITE+'/api/v1/courses/'+\
                state.COURSE+'/quizzes/'+str(quiz)+'/reports/'+str(report_number)+\
                '?access_token='+state.TOKEN) 
            report_meta = json.loads(report_meta_file.read())
            report_contents = urllib2.urlopen( report_meta['file']['url']).read()
            finished = True
        except: # Keep trying. Canvas API offers progress_URL. except KeyError didn't catch
            print "waiting on report"
    # Be visible
    print quiz
              
    return report_meta, report_contents

def get_all_quiz_reports():    
    """ returns three lists: 
    one contains titles of the quizzes, 
    the second list's elements are quiz reports, each a list of lists
    the third list's elements are meta data about each quiz"""
   
    # Get information about all quizzes in the course
    print "getting list of quizzes"
    quiz_metas = get_all('courses/'+state.COURSE+'/quizzes')
    
    # Build a list of the APB number and Canvas-quiz-ID for each APB survey
    titles = []
    quiz_ids = []
    for quiz_meta in quiz_metas:
        title = quiz_meta['title']
        titles.append(title)
        quiz_ids.append(quiz_meta['id'])
        
    # Get the actual reports
    reports=[]
    print "getting quiz reports"
    for quiz_id in quiz_ids:
         print "getting report for "+str(quiz_id)
         f = urllib2.urlopen('https://'+state.SITE+'/api/v1/courses/'+\
            state.COURSE+'/quizzes/'+str(quiz_id)+'/reports?access_token='+\
            state.TOKEN,'quiz_report[report_type]=student_analysis')
         output = f.read()
         nice_output = json.loads(output)
         report_number = nice_output['id']
         
         # Keep trying until the report is actually generated and returned
         finished = False
         while not finished:
                try:
                    report=urllib2.urlopen(\
                       'https://'+state.SITE+'/api/v1/courses/'+\
                       state.COURSE+'/quizzes/'+str(quiz_id)+'/reports/'+\
                       str(report_number)+'?access_token='+state.TOKEN) 
                    r = json.loads(report.read())
                    report_contents = urllib2.urlopen( r['file']['url']).read()
                    finished = True
                except:
                     print "waiting on quiz report"
         reports.append(csv_records(report_contents))
    return titles, reports, quiz_metas

def csv_records(report):
    """ Splits on \n characters that are outside " " 
    Returns a list of records that are each a list of fields
    """
    lines = [] # Aggregator for entire report
    line = [] # Aggregator for one record
    field = '' # Aggregator for one field
    inquote = False # Initialize a toggle for the " mark that quotes commas
    for char in report:
        if char=='"':
            inquote = not inquote # Toggle            
        elif char=='\n' and not inquote:
            #print "appending ",line
            # End of record. Add current field to the record and reset field aggregator
            line.append(field)
            field=''
            # Add current record to file and reset record aggregator
            lines.append(line) 
            line=[]
        elif len(char) != 1:
            print "Bad assumption in canvasAPI.csv_records() passed ", char#,report
        elif char==',' and not inquote:
            # End of field
            line.append(field)
            field=''
        else:
            # Inside a field
            field+=char
            
    # Transpose if needed so that the initial field of each line is the field descriptor
    if len(lines) > 1: # If report isn't empty (otherwise next conditional produces error
        if lines[1][0] != "id": # This occurs if header fields are all in lines[0]
            lines = transpose_report(lines)

    return lines

def transpose_report(report):
    """transposes a list of lists
    """
    transposed=[]
    for field in report[0]:
        transposed.append([field])
    for question in range(0,len(report[0])):
        for teacher in report[1:]:
            transposed[question].append(teacher[question])
    return transposed  
    
def check_completion():
    '''Checks for progress completing tasks in a course.
    
    Returns a list of quiz names and
    
    Returns a dictionary of {studentname:'010111'}
    where each 0/1 indicates non-completion/completion of a quiz
    '''
            
    # Create a dictionary with all people to store results
    if state.SECTION==[]:
        print "Error in check_completion: Use set_section() first."
    completion={}
    for person in state.SECTION:
        completion[person]=''
        
    # Get a list of all quizzes
    quizzes = get_all('courses/'+state.COURSE+'/quizzes')
    
    titles=[]
    for quiz in quizzes:
        # Aggregate quiz names
        titles += [quiz['title']]
        qid = quiz['id']
        report_meta, report = get_quiz_report(str(qid))
        for person in state.SECTION:
            if person in report:
                completion[person] += '1'
            else:
                completion[person] += '0'
    return titles, completion