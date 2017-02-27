import json
import urllib2
from django.conf import settings
import copy
from collections import OrderedDict
from itertools import chain
from collections import Counter
from master.models import SURVEYTYPE_CHOICES, Survey

def survey_mapping(survey_type):
    def real_decorator(function):
        def wrapper(*args, **kwargs):
            city_id = args[0]
            try:
                survey = Survey.objects.filter(city__id=city_id, survey_type=survey_type)
            except:
                survey = None
            kwargs['kobo_survey'] = ''
            if survey:
                kwargs['kobo_survey'] =  survey[0].kobotool_survey_id
            return function(*args, **kwargs)
        return wrapper
    return real_decorator

@survey_mapping(SURVEYTYPE_CHOICES[1][0])
def get_household_analysis_data(city, slum_code, fields, kobo_survey=''):
    '''Gets the kobotoolbox RHS data for selected questions
    '''
    household_field = 'group_ce0hf58/house_no'
    output = {}

    if kobo_survey:
        #Setting up API call and header data
        url = settings.KOBOCAT_FORM_URL + 'data/'+ kobo_survey +'?query={"group_ce0hf58/slum_name":"'+slum_code+'"}&fields="'+ str(fields + [household_field] )+ '"'

        kobotoolbox_request = urllib2.Request(url)
        kobotoolbox_request.add_header('User-agent', 'Mozilla 5.10')
        kobotoolbox_request.add_header('Authorization', settings.KOBOCAT_TOKEN)

        res = urllib2.urlopen(kobotoolbox_request)
        #Read json data from kobotoolbox API
        html = res.read()
        records = json.loads(html)

        #Process received data
        for record in records:
            household_no = record[household_field]
            for field in fields:
                if field != "" and field in record:

                    data = record[field]
                    for val in data.split():
                        if field not in output:
                            output[field] = {}
                        if data not in output[field]:
                            output[field][data]=[]
                        if household_no not in output[field][data]:
                            output[field][data].append(household_no)
    return output

@survey_mapping(SURVEYTYPE_CHOICES[1][0])
def get_kobo_RHS_list(city, slum_code,house_number, kobo_survey=''):

    # url="http://kc.shelter-associates.org/api/v1/forms?format=json"
    """Method which fetches the KoboCat ID's and URL's from the Kobo Toolbox API"""
    output=OrderedDict()
    if kobo_survey:
        try:
            url = settings.KOBOCAT_FORM_URL+'data/'+kobo_survey+'?query={"group_ce0hf58/slum_name":"'+slum_code+'","group_ce0hf58/house_no":"'+house_number+'"}'
        except Exception as e:
            print e

        req = urllib2.Request(url)
        req.add_header('Authorization', settings.KOBOCAT_TOKEN)
        resp = urllib2.urlopen(req)
        content = resp.read()
        submission = json.loads(content)

        url1 = settings.KOBOCAT_FORM_URL+'forms/'+kobo_survey+'/form.json'
        req1 = urllib2.Request(url1)
        req1.add_header('Authorization', settings.KOBOCAT_TOKEN)
        resp1 = urllib2.urlopen(req1)
        content1 = resp1.read()
        data1 = json.loads(content1)

        output = OrderedDict()
        for data in data1['children']:
            if data['type'] == "group":
                sect_form_data = trav(data)
                sub_key = [ str(k) for k in submission[0].keys() if data['name'] in k]
                for sect_form in sect_form_data:
                    key = [x for x in sub_key if x.endswith(sect_form['name'])]
                    if len(key)>0 and 'label' in sect_form:
                        ans = fetch_answer(sect_form, key, submission[0])
                        output[sect_form['label']]  = ans
    return output

@survey_mapping(SURVEYTYPE_CHOICES[0][0])
def get_kobo_RIM_detail(city, slum_code, kobo_survey=''):

    output=OrderedDict()
    if kobo_survey:
        url = settings.KOBOCAT_FORM_URL+'data/'+kobo_survey+'?query={"group_zl6oo94/group_uj8eg07/slum_name":"'+slum_code+'"}'
        req = urllib2.Request(url)
        req.add_header('Authorization', settings.KOBOCAT_TOKEN)
        resp = urllib2.urlopen(req)
        content = resp.read()
        submission = json.loads(content)

        RIM_GENERAL="group_zl6oo94"
        RIM_TOILET="group_te3dx03"
        RIM_WATER="group_zj8tc43"
        RIM_WASTE="group_ks0wh10"
        RIM_DRAINAGE="group_kk5gz02"
        RIM_GUTTER="group_bv7hf31"
        RIM_ROAD="group_xy9hz30"
        section = {RIM_GENERAL:"General", RIM_TOILET:"Toilet", RIM_WATER:"Water",
                   RIM_WASTE:"Waste", RIM_DRAINAGE:"Drainage", RIM_GUTTER:"Gutter", RIM_ROAD:"Road"}

        url1 = settings.KOBOCAT_FORM_URL+'forms/'+kobo_survey+'/form.json'
        req1 = urllib2.Request(url1)
        req1.add_header('Authorization', settings.KOBOCAT_TOKEN)
        resp1 = urllib2.urlopen(req1)
        content1 = resp1.read()
        data1 = json.loads(content1)
        #To maintain the order in which questions are displayed we iterate through the form data
        for data in data1['children']:
            if data['type'] == "group" and data['name'] in section.keys():
                #Group wise get the entire list for questions
                sect_form_data = trav(data)
                #Find the list of keys available in the submission data
                toil_keys = [ str(k) for k in submission[0].keys() if data['name'] in k]
                count = 1
                sub_key = []
                sub = []
                # Needed for toilet section which has repeat section
                for sub_k in toil_keys:
                    if type(submission[0][sub_k]) == list:
                        count = len(submission[0][sub_k])
                        sub = submission[0][sub_k]
                        sub_key.extend(sum([k.keys() for k in submission[0][sub_k]], []))
                    else:
                        sub_key.append(sub_k)
                #Default values
                if data['name'] != RIM_TOILET:
                    output[section[data['name']]] = OrderedDict()
                else:
                    output[section[data['name']]] = []
                    [output[section[data['name']]].append(OrderedDict()) for i in range(count)]
                #Iterate through the list of questions for the group
                for sect_form in sect_form_data:
                    key = [x for x in sub_key if x.endswith(sect_form['name'])]
                    #Check if the question has answer in the submission then only proceed further
                    if len(key)>0 and 'label' in sect_form:
                        if data['name'] != RIM_TOILET:
                            #Fetch the answer for select one/text/select multiple type question
                            ans = fetch_answer(sect_form, key, submission[0])
                            output[section[data['name']]][sect_form['label']]  = ans
                        else:
                            #For toilet repeative section append the set of questions for all the CTB's if available
                            for ind in range(count):
                                if key[0] in sub[ind].keys():
                                    ans = fetch_answer(sect_form, key, sub[ind])
                                    output[section[data['name']]][ind][sect_form['label']] = ans
    return output

@survey_mapping(SURVEYTYPE_CHOICES[0][0])
def get_kobo_RIM_report_detail(city, slum_code, kobo_survey=''):

    output=OrderedDict()
    RIM_TOILET="group_te3dx03"
    if kobo_survey:
        url = settings.KOBOCAT_FORM_URL+'data/'+kobo_survey+'?query={"group_zl6oo94/group_uj8eg07/slum_name":"'+slum_code+'"}'
        req = urllib2.Request(url)
        req.add_header('Authorization', settings.KOBOCAT_TOKEN)
        resp = urllib2.urlopen(req)
        content = resp.read()
        submission = json.loads(content)

        url1 = settings.KOBOCAT_FORM_URL+'forms/'+kobo_survey+'/form.json'
        req1 = urllib2.Request(url1)
        req1.add_header('Authorization', settings.KOBOCAT_TOKEN)
        resp1 = urllib2.urlopen(req1)
        content1 = resp1.read()
        data1 = json.loads(content1)
        #To maintain the order in which questions are displayed we iterate through the form data
        for data in data1['children']:
            if data['type'] == "group":
                #Group wise get the entire list for questions
                sect_form_data = trav(data)
                #Find the list of keys available in the submission data
                toil_keys = [ str(k) for k in submission[0].keys() if data['name'] in k]
                count = 1
                sub_key = []
                sub = []
                # Needed for toilet section which has repeat section
                for sub_k in toil_keys:
                    if type(submission[0][sub_k]) == list:
                        count = len(submission[0][sub_k])
                        sub = submission[0][sub_k]
                        sub_key.extend(sum([k.keys() for k in submission[0][sub_k]], []))
                    else:
                        sub_key.append(sub_k)

                #Iterate through the list of questions for the group
                for sect_form in sect_form_data:
                    key = [x for x in sub_key if x.endswith(sect_form['name'])]
                    #Check if the question has answer in the submission then only proceed further
                    if len(key)>0 and 'label' in sect_form:
                        if data['name'] != RIM_TOILET:
                            #Fetch the answer for select one/text/select multiple type question
                            ans = fetch_answer(sect_form, key, submission[0])
                            output[sect_form['name']]  = ans
                        else:
                            #For toilet repeative section append the set of questions for all the CTB's if available
                            if key[0] in submission[0].keys():
                                ans = fetch_answer(sect_form, key, submission[0])
                                output[sect_form['name']]  = ans
                            else:
                                arr_ans = []
                                for ind in range(count):
                                    if key[0] in sub[ind].keys():
                                        ans = fetch_answer(sect_form, key, sub[ind])
                                        if ans:
                                            arr_ans.append(ans)

                                ans = ""
                                if 'integer' in sect_form['type']:
                                    ans = sum(map(int, arr_ans))
                                else:
                                    c = Counter(arr_ans)
                                    ans = ', '.join([ "{}({})".format(x,y) for x,y in c.items()])
                                output[sect_form['name']] = ans
    return output

def fetch_answer(sect_form, key, submission):
    #Fetch answer and convert it to label
    val = ""
    if 'select' in sect_form['type'] and type(key[0]) != list and 'children' in sect_form:
        options = dict((str(opt['name']), str(opt['label'])) for opt in sect_form['children'])
        sub_option = submission[key[0]].split(' ')
        val = '  '#options[sub_option[0]]
        if len(sub_option) > 0:
            for sub in sub_option:
		if sub in options:
                   val += options[sub] + ', '
            val = val[:-2]
            val = val.strip()
            #val = reduce(lambda x,y: options[x] +',' + options[y], sub_option)
    else:
        val = submission[key[0]]
    return val

def trav(node):
    #Traverse uptill the child node and add to list
    if 'type' in node and node['type'] == "group" or node['type'] == "repeat":
        return list(chain.from_iterable([trav(child) for child in node['children']]))
    else:
        return [node]

def dictdata(data):
    #convert childrens to dictionary for parsing
    data['children'] = dict((str(topic['name']), topic) for topic in data['children'])

    for k,v in data['children'].items():
        if 'children' in v:
            if isinstance(v['children'], list):
                v = dictdata(v)
    return data
