# coding: utf-8
import qrcode
from pyqrcode import QRCode
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import http.cookiejar
import requests
import xml.dom.minidom
import json
import time
import ssl
import re
import sys
import os
import subprocess
import random
import logging
import http.client
import pymysql
from socket import timeout as timeout_error

# for media upload
import mimetypes
from requests_toolbelt.multipart.encoder import MultipartEncoder


def catch_keyboard_interrupt(fn):
    def wrapper(*args):
        try:
            return fn(*args)
        except KeyboardInterrupt:
            print('\n[*] 强制退出程序')
            logging.debug('[*] 强制退出程序')

    return wrapper


def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, str):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


def _decode_dict(data):
    rv = {}
    for key, value in data.items():
        if isinstance(key, str):
            key = key.encode('utf-8')
        if isinstance(value, str):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv


class web_weixin(object):

    def __str__(self):
        description = \
            "=========================\n" + \
            "[#] Web Weixin\n" + \
            "[#] Debug Mode: " + str(self.DEBUG) + "\n" + \
            "[#] Uuid: " + self.uuid + "\n" + \
            "[#] Uin: " + str(self.uin) + "\n" + \
            "[#] Sid: " + self.sid + "\n" + \
            "[#] Skey: " + self.skey + "\n" + \
            "[#] DeviceId: " + self.deviceId + "\n" + \
            "[#] PassTicket: " + self.pass_ticket + "\n" + \
            "========================="
        return description

    # 初始化变量
    def __init__(self):
        self.DEBUG = False
        self.commandLineQRCode = False
        self.uuid = ''
        self.base_uri = ''
        self.redirect_uri = ''
        self.uin = ''
        self.sid = ''
        self.skey = ''
        self.pass_ticket = ''
        self.deviceId = 'e' + repr(random.random())[2:17]
        self.BaseRequest = {}
        self.synckey = ''
        self.SyncKey = []
        self.User = []
        self.DBContact = [] # 数据库中的联系人
        self.MemberList = []
        self.ContactList = []  # 好友
        self.GroupList = []  # 群
        self.GroupMemeberList = []  # 群友
        self.PublicUsersList = []  # 公众号／服务号
        self.SpecialUsersList = []  # 特殊账号
        self.autoReplyMode = True
        self.syncHost = ''
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36'
        self.interactive = False
        self.autoOpen = False
        self.groupSend = True
        self.saveFolder = os.path.join(os.getcwd(), 'saved')
        self.saveSubFolders = {'webwxgeticon': 'icons', 'webwxgetheadimg': 'headimgs', 'webwxgetmsgimg': 'msgimgs',
                               'webwxgetvideo': 'videos', 'webwxgetvoice': 'voices', '_showQRCodeImg': 'qrcodes'}
        self.appid = 'wx782c26e4c19acffb'
        self.lang = 'zh_CN'
        self.lastCheckTs = time.time()
        self.memberCount = 0
        self.SpecialUsers = ['newsapp', 'fmessage', 'filehelper', 'weibo', 'qqmail', 'fmessage', 'tmessage', 'qmessage',
                             'qqsync', 'floatbottle', 'lbsapp', 'shakeapp', 'medianote', 'qqfriend', 'readerapp',
                             'blogapp', 'facebookapp', 'masssendapp', 'meishiapp', 'feedsapp',
                             'voip', 'blogappweixin', 'weixin', 'brandsessionholder', 'weixinreminder',
                             'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'officialaccounts', 'notification_messages',
                             'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'wxitil', 'userexperience_alarm',
                             'notification_messages']
        self.TimeOut = 20  # 同步最短时间间隔（单位：秒）
        self.media_count = -1

        self.cookie = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie))
        opener.addheaders = [('User-agent', self.user_agent)]
        urllib.request.install_opener(opener)

    def load_config(self, config):
        if config['DEBUG']:
            self.DEBUG = config['DEBUG']
        if config['autoReplyMode']:
            self.autoReplyMode = config['autoReplyMode']
        if config['user_agent']:
            self.user_agent = config['user_agent']
        if config['interactive']:
            self.interactive = config['interactive']
        if config['autoOpen']:
            self.autoOpen = config['autoOpen']

    def get_uuid(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': self.appid,
            'fun': 'new',
            'lang': self.lang,
            '_': int(time.time()),
        }
        # r = requests.get(url=url, params=params)
        # r.encoding = 'utf-8'
        # data = r.text
        data = self._post(url, params, False).decode("utf-8")
        if data == '':
            return False
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        # 正则表达式
        pm = re.search(regx, data)
        if pm:
            # 状态码
            code = pm.group(1)
            # 设置 UUID
            self.uuid = pm.group(2)
            return code == '200'
        return False

    # 设置当前系统
    def gen_qrcode(self):
        # return self._showQRCodeImg()
        # 判断 sys.platform(系统类型二进制数据)是否以指定字符开头
        if sys.platform.startswith('win'):
            self._show_qrcode_img('win')
        elif sys.platform.find('darwin') >= 0:
            self._show_qrcode_img('macos')
        else:
            self._str2qr('https://login.weixin.qq.com/l/' + self.uuid)

    # 获取并显示二维码
    def _show_qrcode_img(self, str):
        if self.commandLineQRCode:
            qrCode = QRCode('https://login.weixin.qq.com/l/' + self.uuid)
            self._show_command_line_qrcode(qrCode.text(1))
        else:
            url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
            params = {
                't': 'webwx',
                '_': int(time.time())
            }

            data = self._post(url, params, False)
            if data == '':
                return
            QRCODE_PATH = self._save_file('qrcode.jpg', data, '_showQRCodeImg')
            if str == 'win':
                os.startfile(QRCODE_PATH)
            elif str == 'macos':
                # 调用命令行——打开图片
                subprocess.call(["open", QRCODE_PATH])
            else:
                return

    def _show_command_line_qrcode(self, qr_data, enableCmdQR=2):
        try:
            b = u'\u2588'
            sys.stdout.write(b + '\r')
            sys.stdout.flush()
        except UnicodeEncodeError:
            white = 'MM'
        else:
            white = b
        black = '  '
        block_count = int(enableCmdQR)
        if abs(block_count) == 0:
            block_count = 1
        white *= abs(block_count)
        if block_count < 0:
            white, black = black, white
        sys.stdout.write(' ' * 50 + '\r')
        sys.stdout.flush()
        qr = qr_data.replace('0', white).replace('1', black)
        sys.stdout.write(qr)
        sys.stdout.flush()

    # 等待登陆，tip: 1:未扫描; 0:已扫描
    def wait_for_login(self, tip=1):
        # 延迟
        time.sleep(tip)
        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
            tip, self.uuid, int(time.time()))
        data = self._get(url)
        if data == '':
            return False
        pm = re.search(r"window.code=(\d+);", data)
        code = pm.group(1)

        if code == '201':
            return True
        elif code == '200':
            pm = re.search(r'window.redirect_uri="(\S+?)";', data)
            r_uri = pm.group(1) + '&fun=new'
            self.redirect_uri = r_uri
            self.base_uri = r_uri[:r_uri.rfind('/')]
            return True
        elif code == '408':
            self._echo('[登陆超时] \n')
        else:
            self._echo('[登陆异常] \n')
        return False

    def login(self):
        data = self._get(self.redirect_uri)
        if data == '':
            return False
        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.sid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.uin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data

        if '' in (self.skey, self.sid, self.uin, self.pass_ticket):
            return False

        self.BaseRequest = {
            'Uin': int(self.uin),
            'Sid': self.sid,
            'Skey': self.skey,
            'DeviceID': self.deviceId,
        }
        return True

    def webwx_init(self):
        url = self.base_uri + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
            self.pass_ticket, self.skey, int(time.time()))
        params = {
            'BaseRequest': self.BaseRequest
        }
        dic = self._post(url, params)
        if dic == '':
            return False
        self.SyncKey = dic['SyncKey']
        self.User = dic['User']
        # synckey for synccheck
        self.synckey = '|'.join(
            [str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.SyncKey['List']])

        return dic['BaseResponse']['Ret'] == 0

    def webwx_status_notify(self):
        url = self.base_uri + \
              '/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % (self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            "Code": 3,
            "FromUserName": self.User['UserName'],
            "ToUserName": self.User['UserName'],
            "ClientMsgId": int(time.time())
        }
        dic = self._post(url, params)
        if dic == '':
            return False

        return dic['BaseResponse']['Ret'] == 0

    # 获取数据库联系人
    def get_db_contact(self):
        db_connect=pymysql.connect(host="localhost", user="root", passwd="toor", db="CrazyChat", charset="utf8")
        cursor = db_connect.cursor()
        sql = "SELECT t.RemarkName FROM Contact t"
        cursor.execute(sql)
        contact = []
        result = cursor.fetchall()
        db_connect.close()
        for row in result:
            contact.append(row[0])
        return contact

    # 添加联系人到数据库
    def update_db_contact(self, ct):
        db_connect=pymysql.connect(host="localhost", user="root", passwd="toor", db="CrazyChat", charset="utf8")
        cursor = db_connect.cursor()
        sql = "INSERT INTO Contact (NickName, RemarkName, Sex, Province, City, Alias, IsOwner) VALUES ('" + ct[
            'NickName'].replace("'", "\\'") + "', '" + ct['RemarkName'] + "', '" + str(ct['Sex']) + "', '" + ct['Province'] + "', '" + ct[
                   'City'] + "', '" + ct['Alias'] + "', '" + str(ct['IsOwner']) + "')"
        try:
            cursor.execute(sql)
            db_connect.commit()
            print("添加联系人 " + ct['RemarkName'] + " 成功")
        except:
            db_connect.rollback()
            print("添加联系人 " + ct['RemarkName'] + " 失败，回滚数据：")
            print("添加联系人：" + sql)
        db_connect.close()

    # 获取联系人
    def webwx_get_contact(self):
        self.DBContact = self.get_db_contact()
        special_users = self.SpecialUsers
        url = self.base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            self.pass_ticket, self.skey, int(time.time()))
        dic = self._post(url, {})
        if dic == '':
            return False

        self.MemberCount = dic['MemberCount']
        self.MemberList = dic['MemberList']
        contact_list = self.MemberList[:]

        for i in range(len(contact_list) - 1, -1, -1):
            contact = contact_list[i]
            if contact['RemarkName'] not in self.DBContact and contact['RemarkName'] != '':
                self.update_db_contact(contact)
            if contact['VerifyFlag'] & 8 != 0:  # 公众号/服务号
                contact_list.remove(contact)
                self.PublicUsersList.append(contact)
            elif contact['UserName'] in special_users:  # 特殊账号
                contact_list.remove(contact)
                self.SpecialUsersList.append(contact)
            elif '@@' in contact['UserName']:  # 群聊
                contact_list.remove(contact)
                self.GroupList.append(contact)
            elif contact['UserName'] == self.User['UserName']:  # 自己
                contact_list.remove(contact)
        self.ContactList = contact_list
        self.DBContact = self.get_db_contact()

        return True

    def webwx_batch_get_contact(self):
        url = self.base_uri + \
              '/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (
                  int(time.time()), self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            "Count": len(self.GroupList),
            "List": [{"UserName": g['UserName'], "EncryChatRoomId": ""} for g in self.GroupList]
        }
        dic = self._post(url, params)
        if dic == '':
            return False

        # blabla ...
        contact_list = dic['ContactList']
        self.GroupList = contact_list

        for i in range(len(contact_list) - 1, -1, -1):
            contact = contact_list[i]
            member_list = contact['MemberList']
            for member in member_list:
                self.GroupMemeberList.append(member)
        return True

    def webwx_send_msg(self, word, to='filehelper'):
        url = self.base_uri + \
              '/webwxsendmsg?pass_ticket=%s' % (self.pass_ticket)
        client_msg_id = str(int(time.time() * 1000)) + \
                      str(random.random())[:5].replace('.', '')
        params = {
            'BaseRequest': self.BaseRequest,
            'Msg': {
                "Type": 1,
                "Content": self._trans_coding(word),
                "FromUserName": self.User['UserName'],
                "ToUserName": to,
                "LocalID": client_msg_id,
                "ClientMsgId": client_msg_id
            }
        }
        headers = {'content-type': 'application/json; charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf8')
        r = requests.post(url, data=data, headers=headers)
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def webwx_upload_media(self, image_name):
        url = 'https://file2.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        # 计数器
        self.media_count = self.media_count + 1
        # 文件名
        file_name = image_name
        # MIME格式
        # mime_type = application/pdf, image/jpeg, image/png, etc.
        mime_type = mimetypes.guess_type(image_name, strict=False)[0]
        # 微信识别的文档格式，微信服务器应该只支持两种类型的格式。pic和doc
        # pic格式，直接显示。doc格式则显示为文件。
        media_type = 'pic' if mime_type.split('/')[0] == 'image' else 'doc'
        # 上一次修改日期
        last_modifie_date = 'Thu Mar 17 2016 00:55:10 GMT+0800 (CST)'
        # 文件大小
        file_size = os.path.getsize(file_name)
        # PassTicket
        pass_ticket = self.pass_ticket
        # clientMediaId
        client_media_id = str(int(time.time() * 1000)) + \
                          str(random.random())[:5].replace('.', '')
        # webwx_data_ticket
        webwx_data_ticket = ''
        for item in self.cookie:
            if item.name == 'webwx_data_ticket':
                webwx_data_ticket = item.value
                break
        if (webwx_data_ticket == ''):
            return "None Fuck Cookie"

        upload_media_request = json.dumps({
            "BaseRequest": self.BaseRequest,
            "ClientMediaId": client_media_id,
            "TotalLen": file_size,
            "StartPos": 0,
            "DataLen": file_size,
            "MediaType": 4
        }, ensure_ascii=False).encode('utf8')

        multipart_encoder = MultipartEncoder(
            fields={
                'id': 'WU_FILE_' + str(self.media_count),
                'name': file_name,
                'type': mime_type,
                'lastModifieDate': last_modifie_date,
                'size': str(file_size),
                'mediatype': media_type,
                'uploadmediarequest': upload_media_request,
                'webwx_data_ticket': webwx_data_ticket,
                'pass_ticket': pass_ticket,
                'filename': (file_name, open(file_name, 'rb'), mime_type.split('/')[1])
            },
            boundary='-----------------------------1575017231431605357584454111'
        )

        headers = {
            'Host': 'file2.wx.qq.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:42.0) Gecko/20100101 Firefox/42.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://wx2.qq.com/',
            'Content-Type': multipart_encoder.content_type,
            'Origin': 'https://wx2.qq.com',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

        r = requests.post(url, data=multipart_encoder, headers=headers)
        response_json = r.json()
        if response_json['BaseResponse']['Ret'] == 0:
            return response_json
        return None

    def webwx_send_msg_img(self, user_id, media_id):
        url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsgimg?fun=async&f=json&pass_ticket=%s' % self.pass_ticket
        client_msg_id = str(int(time.time() * 1000)) + \
                      str(random.random())[:5].replace('.', '')
        data_json = {
            "BaseRequest": self.BaseRequest,
            "Msg": {
                "Type": 3,
                "MediaId": media_id,
                "FromUserName": self.User['UserName'],
                "ToUserName": user_id,
                "LocalID": client_msg_id,
                "ClientMsgId": client_msg_id
            }
        }
        headers = {'content-type': 'application/json; charset=UTF-8'}
        data = json.dumps(data_json, ensure_ascii=False).encode('utf8')
        r = requests.post(url, data=data, headers=headers)
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def webwx_send_msg_emotion(self, user_id, media_id):
        url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendemoticon?fun=sys&f=json&pass_ticket=%s' % self.pass_ticket
        client_msg_id = str(int(time.time() * 1000)) + \
                      str(random.random())[:5].replace('.', '')
        data_json = {
            "BaseRequest": self.BaseRequest,
            "Msg": {
                "Type": 47,
                "EmojiFlag": 2,
                "MediaId": media_id,
                "FromUserName": self.User['UserName'],
                "ToUserName": user_id,
                "LocalID": client_msg_id,
                "ClientMsgId": client_msg_id
            }
        }
        headers = {'content-type': 'application/json; charset=UTF-8'}
        data = json.dumps(data_json, ensure_ascii=False).encode('utf8')
        r = requests.post(url, data=data, headers=headers)
        dic = r.json()
        if self.DEBUG:
            print(json.dumps(dic, indent=4))
            logging.debug(json.dumps(dic, indent=4))
        return dic['BaseResponse']['Ret'] == 0

    def _save_file(self, filename, data, api=None):
        fn = filename
        if self.saveSubFolders[api]:
            dir_name = os.path.join(self.saveFolder, self.saveSubFolders[api])
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            fn = os.path.join(dir_name, filename)
            logging.debug('Saved file: %s' % fn)
            with open(fn, 'wb') as f:
                f.write(data)
                f.close()
        return fn

    def get_user_id(self, name):
        for member in self.MemberList:
            if name == member['RemarkName'] or name == member['NickName']:
                return member['UserName']
        return None

    def send_msg(self, name, word, isfile=False):
        id = self.get_user_id(name)
        if id:
            if isfile:
                with open(word, 'r') as f:
                    for line in f.readlines():
                        line = line.replace('\n', '')
                        self._echo('-> ' + name + ': ' + line)
                        if self.webwx_send_msg(line, id):
                            print(' [成功]')
                        else:
                            print(' [失败]')
                        time.sleep(1)
            else:
                if self.webwx_send_msg(word, id):
                    print('[*] 消息发送成功')
                    logging.debug('[*] 消息发送成功')
                else:
                    print('[*] 消息发送失败')
                    logging.debug('[*] 消息发送失败')
        else:
            print('[*] 此用户不存在')
            logging.debug('[*] 此用户不存在')

    def send_msg_to_all(self, word):
        for contact in self.ContactList:
            name = contact['RemarkName'] if contact[
                'RemarkName'] else contact['NickName']
            id = contact['UserName']
            self._echo('-> ' + name + ': ' + word)
            if self.webwx_send_msg(word, id):
                print(' [成功]')
            else:
                print(' [失败]')
            time.sleep(1)

    def send_img(self, name, file_name):
        response = self.webwx_upload_media(file_name)
        media_id = ""
        if response is not None:
            media_id = response['MediaId']
        user_id = self.get_user_id(name)
        self.webwx_send_msg_img(user_id, media_id)

    def send_emotion(self, name, file_name):
        response = self.webwx_upload_media(file_name)
        media_id = ""
        if response is not None:
            media_id = response['MediaId']
        user_id = self.get_user_id(name)
        self.webwx_send_msg_emotion(user_id, media_id)

    def group_send_msg(self):
        db_connect=pymysql.connect(host="localhost", user="root", passwd="toor", db="CrazyChat", charset="utf8")
        cursor = db_connect.cursor()
        # TODO 获取祝福语句

        for contact in self.ContactList:
            # TODO 随机一句
            str = "hi~"
            if contact['RemarkName'] in self.DBContact:
            # Test
            # if contact['RemarkName'] == '包子小号':
                cursor.execute("SELECT t.RemarkName, t.RealNickName FROM Contact t WHERE t.RemarkName = '" + contact['RemarkName'] + "'")
                row = cursor.fetchone()
                remark_name = row[0]
                real_name = row[1]
                if real_name != '':
                # Test
                # if realName == '':
                    self.webwx_send_msg(str + real_name, contact['UserName'])
                    print("发送消息给 " + contact['RemarkName'] + ": " + remark_name)

        db_connect.close()
        print("[*] 群发消息已完成")

    # 开始运行
    @catch_keyboard_interrupt
    def start(self):
        self._echo('[*] 微信网页版 ... 开动')
        self._echo(self.deviceId)
        print()
        logging.debug('[*] 微信网页版 ... 开动')
        while True:
            self._run('[*] 正在获取 uuid ... ', self.get_uuid)
            self._echo('[*] 正在获取二维码 ... 成功')
            print()
            logging.debug('[*] 微信网页版 ... 开动')
            self.gen_qrcode()
            print('[*] 请使用微信扫描二维码以登录 ... ')
            if not self.wait_for_login():
                continue
                print('[*] 请在手机上点击确认以登录 ... ')
            if not self.wait_for_login(0):
                continue
            break

        self._run('[*] 正在登录 ... ', self.login)
        self._run('[*] 微信初始化 ... ', self.webwx_init)
        self._run('[*] 开启状态通知 ... ', self.webwx_status_notify)
        self._run('[*] 获取联系人 ... ', self.webwx_get_contact)
        self._echo('[*] 应有 %s 个联系人，读取到联系人 %d 个' %
                   (self.MemberCount, len(self.MemberList)))
        print()
        self._echo('[*] 共有 %d 个群 | %d 个直接联系人 | %d 个特殊账号 ｜ %d 公众号或服务号' % (len(self.GroupList),
                                                                         len(self.ContactList),
                                                                         len(self.SpecialUsersList),
                                                                         len(self.PublicUsersList)))
        print()
        self._run('[*] 获取群 ... ', self.webwx_batch_get_contact)
        logging.debug('[*] 微信网页版 ... 开动')
        if self.DEBUG:
            print(self)
        logging.debug(self)

        if self.groupSend:
            print('[*] 署名群发模式 ... 开启')
            self.group_send_msg()
            print('[*] 退出微信')
            logging.debug('[*] 退出微信')
            exit()

        if self.interactive and input('[*] 是否开启自动回复模式(y/n): ') == 'y':
            self.autoReplyMode = True
            print('[*] 自动回复模式 ... 开启')
            logging.debug('[*] 自动回复模式 ... 开启')
        else:
            print('[*] 自动回复模式 ... 关闭')
            logging.debug('[*] 自动回复模式 ... 关闭')

        while True:
            text = input('')
            if text == 'quit':
                listen_process.terminate()
                print('[*] 退出微信')
                logging.debug('[*] 退出微信')
                exit()
            elif text[:2] == '->':
                [name, word] = text[2:].split(':')
                if name == 'all':
                    self.send_msg_to_all(word)
                else:
                    self.send_msg(name, word)
            elif text[:3] == 'm->':
                [name, file] = text[3:].split(':')
                self.send_msg(name, file, True)
            elif text[:3] == 'f->':
                print('发送文件')
                logging.debug('发送文件')
            elif text[:3] == 'i->':
                print('发送图片')
                [name, file_name] = text[3:].split(':')
                self.send_img(name, file_name)
                logging.debug('发送图片')
            elif text[:3] == 'e->':
                print('发送表情')
                [name, file_name] = text[3:].split(':')
                self.send_emotion(name, file_name)
                logging.debug('发送表情')

    def _run(self, str, func, *args):
        self._echo(str)
        if func(*args):
            print('成功')
            logging.debug('%s... 成功' % (str))
        else:
            print('失败\n[*] 退出程序')
            logging.debug('%s... 失败' % (str))
            logging.debug('[*] 退出程序')
            exit()

    def _echo(self, str):
        sys.stdout.write(str)
        sys.stdout.flush()

    def _str2qr(self, str):
        print(str)
        qr = qrcode.QRCode()
        qr.border = 1
        qr.add_data(str)
        qr.make()
        qr.print_ascii(invert=True)

    def _trans_coding(self, data):
        if not data:
            return data
        result = None
        if type(data) == str:
            result = data
        elif type(data) == str:
            result = data.decode('utf-8')
        return result

    def _get(self, url: object, api: object = None, timeout: object = None) -> object:
        request = urllib.request.Request(url=url)
        request.add_header('Referer', 'https://wx.qq.com/')
        if api == 'webwxgetvoice':
            request.add_header('Range', 'bytes=0-')
        if api == 'webwxgetvideo':
            request.add_header('Range', 'bytes=0-')
        try:
            response = urllib.request.urlopen(request, timeout=timeout) if timeout else urllib.request.urlopen(request)
            if api == 'webwxgetvoice' or api == 'webwxgetvideo':
                data = response.read()
            else:
                data = response.read().decode('utf-8')
            logging.debug(url)
            return data
        except urllib.error.HTTPError as e:
            logging.error('HTTPError = ' + str(e.code))
        except urllib.error.URLError as e:
            logging.error('URLError = ' + str(e.reason))
        except http.client.HTTPException as e:
            logging.error('HTTPException')
        except timeout_error as e:
            pass
        except ssl.CertificateError as e:
            pass
        except Exception:
            import traceback
            logging.error('generic exception: ' + traceback.format_exc())
        return ''

    def _post(self, url: object, params: object, jsonfmt: object = True) -> object:
        if jsonfmt:
            data = (json.dumps(params)).encode()

            request = urllib.request.Request(url=url, data=data)
            request.add_header(
                'ContentType', 'application/json; charset=UTF-8')
        else:
            request = urllib.request.Request(url=url, data=urllib.parse.urlencode(params).encode(encoding='utf-8'))

        try:
            response = urllib.request.urlopen(request)
            data = response.read()
            if jsonfmt:
                return json.loads(data.decode('utf-8'))  # object_hook=_decode_dict)
            return data
        except urllib.error.HTTPError as e:
            logging.error('HTTPError = ' + str(e.code))
        except urllib.error.URLError as e:
            logging.error('URLError = ' + str(e.reason))
        except http.client.HTTPException as e:
            logging.error('HTTPException')
        except Exception:
            import traceback
            logging.error('generic exception: ' + traceback.format_exc())

        return ''

class UnicodeStreamFilter:

    def __init__(self, target):
        self.target = target
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.encode_to = self.target.encoding

    def write(self, s):
        if type(s) == str:
            s = s.encode().decode('utf-8')
        s = s.encode(self.encode_to, self.errors).decode(self.encode_to)
        self.target.write(s)

    def flush(self):
        self.target.flush()


if sys.stdout.encoding == 'cp936':
    sys.stdout = UnicodeStreamFilter(sys.stdout)

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    if not sys.platform.startswith('win'):
        import coloredlogs

        coloredlogs.install(level='DEBUG')

    webwx = web_weixin()
    webwx.start()
