# coding: utf-8
from weibo import APIClient
from re import split
import re
import urllib,httplib
import logging
import time
import os
import sys
import string

CONFIG_FILE = os.environ['HOME'] + '/dognanny.rc'
INTERVAL = 30 # 30s
ADMIN = u'豆芽小约'

# read app key/secret and weibo account/passwd from file
def read_config():

    appinfo = {'key':'', 'secret':''}
    account = {'id':'', 'passwd':''}
    callback_url = ''

    logging.info("openning the configure file: %s" % CONFIG_FILE)
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
# return: (id, sender_name, cmd)
def msg_analysis(msg, nanny):
    date = msg['created_at']
    text = msg['text']
    name = msg['user']['name']
    msgid = msg['id']
    cmd = ''

    pair = re.compile(r"@(\w+) (\w+)", re.U)

    for key, desc in cmds_desc.items():
        m = pair.match(text)
        if m is not None:
	    if m.group(1) != nanny:
                logging.warning("%s has send a wrong msg on %s" % (m.group(1), date))
                return (t, 0, '', '')
            idx = string.find(m.group(2), desc['pattern'])
            if idx == 0:
                cmd = key
                break

    logging.debug("return command(%s): [%s]: (%s) by %s" % (date, cmd, text, name))
    return (msg['id'], name, cmd)

def cmd_poll(client, executor, msgid):
    # take instant temperature
    # take picture from camera
    # send one weibo message with pic & @sender

    return 'ok'

def cmd_ac(on):
    # if there's ac control command
    # send ac ctrl command
    # reply to the command weibo message
    return 'ok'

def cmd_acon(client, executor, msgid):
    ret = cmd_ac(True)
    return ret

def cmd_acoff(client, executor, msgid):
    ret = cmd_ac(False)
    return ret

def cmd_kill(client, executor, msgid):
    logging.info("kill myself on order of {0}".format(*executor))
    return 'ok'

# commands description and handler
cmds_desc = {
    'poll' : {
             'pattern': u'豆芽怎么样了',
             'desc': u'poll the status',
             'handler': cmd_poll },
    'acon' : {
             'pattern': u'请开空调',
             'desc': u'turn on ac',
             'handler': cmd_acon },
    'acoff': {
             'pattern': u'请关空调',
             'desc': u'turn off ac',
             'handler': cmd_acoff },
    'kill' : {
             'pattern': u'你可以下岗了',
             'desc': u'kill myself',
             'handler': cmd_kill },
}

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

    # get emotions
    emotions = []
    emotion_id = 0
    get_emotions = client.emotions.get()
    for emotion in get_emotions:
        emotions.append(emotion['phrase'])
    logging.debug("Get emotions {0}".format(emotions))

    # update last id, drop the expired command message
    msg = client.statuses.mentions.get(filter_by_author='1', trim_user='1', since_id=since_id)
    get_statuses = msg.__getattr__('statuses')
    if (len(get_statuses) > 0) and get_statuses[0].has_key('id'):
        since_id = get_statuses[0]['id']
    logging.debug("Start to get command message from id:%s" % since_id)

    # main loop
    while True:
        now = time.time()
	tmp_id = since_id
	cmd_queue = {}

        # debug to get rate limit status
        msg = client.account.rate_limit_status.get()
        if msg.has_key('api_rate_limits'):
            del msg['api_rate_limits']
        logging.debug("Get rate limit:{0}".format(msg))

        # get the lastest @ message by since_id
	logging.debug("Get mentions by since_id:%d" % since_id)
        msg = client.statuses.mentions.get(filter_by_author='1', trim_user='1', since_id=since_id)
        get_statuses = msg.__getattr__('statuses')
	for msg in get_statuses:
            # filter for commands
            # Analysis the message sender, put in list
            (msgid, args, cmd) = msg_analysis(msg, nanny_name)

            if tmp_id < msgid:
                tmp_id = msgid
            # if the message parsed error
	    if msgid == 0 or cmd == '':
                continue

            # filter the commands sent by non admin
            if (cmd is not 'poll') and (args != ADMIN):
                # comment the message
                deny_comment = u"貌似您不是豆芽主人唉%s" % (emotions[emotion_id])
                client.comments.create.post(id=msgid, comment=deny_comment)
                emotion_id = (emotion_id + 1) % len(emotions)
                logging.debug("no prividge for %s to do %s" % (args, cmd))
                continue

            if cmd_queue.has_key(cmd):
                if not args in cmd_queue[cmd]:
                    cmd_queue[cmd].append(u'@' + args)
            else:
                cmd_queue[cmd] = [u'@' + args, ]

	if tmp_id == since_id or len(cmd_queue) == 0:
            logging.debug("on message handle this cycle")
            time.sleep(INTERVAL)
            continue

        # TODO: save the acon/off, kill lastest message id for response
        # execute commands after queueing msg
        if len(cmd_queue) > 0:
            for key, value in cmd_queue.items():
                logging.debug(u"execute cmd:{0} for {1}".format(key, *value))
                ret = cmds_desc[key]['handler'](client, value, msgid)

        cmd_queue.clear()
        since_id = tmp_id
        time.sleep(INTERVAL)


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
