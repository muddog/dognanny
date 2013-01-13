# coding: utf-8
from weibo import APIClient
from re import split
import re
import urllib,httplib
import logging
import time
import os
import sys

CONFIG_FILE = os.environ['HOME'] + '/dognanny.rc'
INTERVAL = 60 # 30s
ADMIN = u'豆芽小约'
CMDS_PATTERN = {
    'poll' : u'豆芽怎么样了',
    'acon' : u'请开空调',
    'acoff' : u'请关空调',
    'kill' : u'你可以下岗了',
}

def read_config():

    appinfo = {'key':'', 'secret':''}
    account = {'id':'', 'passwd':''}
    callback_url = ''

    logging.info("openning the configure file: %s" % CONFIG_FILE)
    # read app key/secret and weibo account/passwd from file
    try:
        accfd = open(CONFIG_FILE, 'r')
        lines = accfd.readlines()
        if len(lines) is 5:
            appinfo['key'] = lines[0].strip('\n')
            appinfo['secret'] = lines[1].strip('\n')
            account['id'] = lines[2].strip('\n')
            account['passwd'] = lines[3].strip('\n')
            callback_url = lines[4].strip('\n')
        else:
            accfd.close()
	    logging.error("Content of config file error")
            sys.exit(1)

    except IOError as e:
        logging.error("Cannot read config file %s" % e.strerror)
        sys.exit(1)

    return (appinfo, account, callback_url)

#for getting the code contained in the callback url
def get_oauth2_code(app, acc, cb_url, au_url):

    conn = httplib.HTTPSConnection('api.weibo.com')
    postdata = urllib.urlencode     ({'client_id':app['key'],'response_type':'code','redirect_uri':cb_url,'action':'submit','userId':acc['id'],'passwd':acc['passwd'],'isLoginSina':0,'from':'','regCallback':'','state':'','ticket':'','withOfficalFlag':0})
    conn.request('POST','/oauth2/authorize',postdata,{'Referer':au_url,'Content-Type': 'application/x-www-form-urlencoded'})
    res = conn.getresponse()
    location = res.getheader('location')
    code = location.split('=')[1]
    conn.close()
    return code

# analysis the @ message
# return:
#       (time, id, sender_name, cmd)
# commands:
#       "@nanny 豆芽怎么样了" return temperature and picture
#       "@nanny 请开空调" turn on the air condition
#       "@nanny 请关空调" turn off the air condition
#       "@nanny 你可以下岗了" kill self
def msg_analysis(msg, nanny):
    date = msg['created_at']
    text = msg['text']
    name = msg['user']['name']
    msgid = msg['id']
    cmd = ''

    for key, patt in CMDS_PATTERN.items():
        m = re.match(u'@(\w+) (\w+)', text)
        if m is not None:
	    if m.group(1) != nanny:
                break
            if m.group(2) == patt:
                cmd = key
                break

    t = time.strptime(date, "%a %b %d %H:%M:%S +0800 %Y")
    logging.debug("Parser command(%s): [%s]: (%s) by %s" % (date, cmd, text, name))
    return (t, msg['id'], name, cmd)

def main():

    # read the appinfo and account info from file
    (appinfo, account, callback_url) = read_config()
    logging.info("Get app info: {0}".format(appinfo))
    logging.info("Get account info: {0}".format(account))
    logging.info("Get callback URL: {0}".format(callback_url))

    # getting the authorize url
    client = APIClient(app_key=appinfo['key'], app_secret=appinfo['secret'], redirect_uri=callback_url)
    auth_url = client.get_authorize_url()
    logging.info("OAuth authorize URL:%s" % auth_url)

    code = get_oauth2_code(appinfo, account, callback_url, auth_url)
    logging.info("Get auth code:%s" % code)
    r = client.request_access_token(code)
    logging.info("Get access token:{0} expire:{1}".format(r.access_token, r.expires_in))

    # save the access token
    client.set_access_token(r.access_token, r.expires_in)

    # get nanny user id, then the name
    msg = client.account.get_uid.get()
    nanny_uid = msg.__getattr__('uid')
    if nanny_uid == 0:
        logging.error("Cannot get the nanny account uid")
        sys.exit(1)
    msg = client.users.show.get(uid=nanny_uid)
    nanny_name = msg.__getattr__('screen_name')
    if len(nanny_name) == 0:
        logging.error("Cannot get the nanny account screen name:%d" % nanny_uid)
        sys.exit(1)

    logging.debug("Get nanny's uid:%d screen_name:%s" % (nanny_uid, nanny_name))

    # initilized the since_id
    since_id = 0

    while True:
        now = time.time()
	tmp_id = since_id
	cmd_queue = {}
        # get the lastest @ message by since_id
	logging.debug("Get mentions by since_id:%d" % since_id)
        msg = client.statuses.mentions.get(filter_by_author='1', trim_user='1', since_id=since_id)
        get_statuses = msg.__getattr__('statuses')
	for msg in get_statuses:
            # filter for commands
            # Analysis the message sender, put in list
            (t, msgid, args, cmd) = msg_analysis(msg, nanny_name)
            # if the message parsed error
	    if msgid == 0:
                continue

            delta = now - time.mktime(t)
            # should be the first time running ?
	    if delta > 2*INTERVAL:
                since_id = msg['id']
                break # should sleep and continue
            if cmd is not '':
                cmd_queue[cmd].append(args)
            else:
		logging.warning("{0} has send a wrong msg on {1}".format(args, t))
            if tmp_id < msgid:
                tmp_id = msgid

	if tmp_id == since_id or len(cmd_queue) == 0:
            logging.debug("on message handle this cycle")
            continue

        # execute commands after queueing msg
        if 'poll' in cmd_queue:
            logging.debug("sending poll response to {0}".format(cmd_queue['poll']))
        if 'acon' in cmd_queue:
            logging.debug("turn on ac for {0}".format(cmd_queue['acon']))
        if 'acoff' in cmd_queue:
            logging.debug("turn off ac for {0}".format(cmd_queue['acoff']))
        if 'kill' in cmd_queue:
            logging.debug("kill myself for {0}".format(cmd_queue['kill']))
        # if there's query command
        # take instant temperature
        # take picture from camera
        # send one weibo message with pic & @sender

        # if there's ac control command
        # send ac ctrl command
        # reply to the command weibo message
        since_id = tmp_id
	time.sleep(INTERVAL - 2)


if __name__ == '__main__':
    # setup the logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='/tmp/dognanny.log',
                        filemode='w')

    # make it daemon
    try:
        pid = os.fork()
	if pid > 0:
           sys.exit(0)
    except OSError, e:
        logging.error("fork #1 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
	if pid > 0:
           logging.info("Daemon pid: %d" % pid)
           sys.exit(0)
    except OSError, e:
        logging.error("fork #2 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)

    main()
