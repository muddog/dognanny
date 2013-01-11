# coding: utf-8
from weibo import APIClient
from re import split
import urllib,httplib
import webbrowser
import time

APP_KEY = '' # app key
APP_SECRET = '' # app secret
CALLBACK_URL = 'http://www.baidu.com'
ACCOUNT = '' # weibo accout
PASSWORD = '' # weibo passwd

#for getting the authorize url
client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
url = client.get_authorize_url()
print url

#for getting the code contained in the callback url
def get_code():
    conn = httplib.HTTPSConnection('api.weibo.com')
    postdata = urllib.urlencode     ({'client_id':APP_KEY,'response_type':'code','redirect_uri':CALLBACK_URL,'action':'submit','userId':ACCOUNT,'passwd':PASSWORD,'isLoginSina':0,'from':'','regCallback':'','state':'','ticket':'','withOfficalFlag':0})
    conn.request('POST','/oauth2/authorize',postdata,{'Referer':url,'Content-Type': 'application/x-www-form-urlencoded'})
    res = conn.getresponse()
    location = res.getheader('location')
    print location
    code = location.split('=')[1]
    conn.close()
    return code

code = get_code()
r = client.request_access_token(code)
access_token = r.access_token # The token return by sina
expires_in = r.expires_in

print "access_token=" ,access_token, "expires_in=" ,expires_in

#save the access token
client.set_access_token(access_token, expires_in)
msg = client.statuses.friends_timeline.get()
#get_statuses = msg.__getattr__('statuses')
#for line in get_statuses:
#    print line['text']

# get the last handled message by since_id
msg = client.statuses.mentions.get(filter_by_author='1', trim_user='1', count='1')
get_statuses = msg.__getattr__('statuses')
last_date = get_statuses[0]['created_at']
print "%s: %s" % (last_date, get_statuses[0]['text'])
t = time.strptime(last_date, "%a %b %d %H:%M:%S +0800 %Y")
print time.mktime(t)
print "expiring: %ds" % (time.time() - time.mktime(t))

# filter for commands
# * query for temperature and screenshot
# * air condition control
# Analysis the message sender, put in list


# if there's query command
# take instant temperature
# take picture from camera
# send one weibo message with pic & @sender

# if there's ac control command
# send ac ctrl command
# reply to the command weibo message
