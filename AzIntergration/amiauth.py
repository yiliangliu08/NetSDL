import requests
import json
import time
import datetime
from time import gmtime, strftime
from Crypto.Cipher import AES
import base64
from hashlib import md5
import os
from Crypto.Util.Padding import pad


class AuthContent:
    def __init__(self, errCode=0, errMsg=""):
        self.ErrorCode = errCode
        self.ErrorMsg = errMsg
        self.AuthCloud = {}
        self.AuthToken = {}
        self.AuthSession = {}


class AuthCloud:
    def __init__(self, cloud):
        self.__dict__.update(cloud)


class AuthToken:
    def __init__(self, cloudToken):
        self.__dict__.update(cloudToken)


class AuthSession:
    def __init__(self, cloudSession):
        self.__dict__.update(cloudSession)


def md5Encoding(text):
    hash = md5()
    hash.update(text)
    return hash.hexdigest()


def aes_cipher(key, aes_str):
    aes = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    pad_pkcs7 = pad(aes_str.encode('utf-8'), AES.block_size, style='pkcs7')
    encrypt_aes = aes.encrypt(pad_pkcs7)
    encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8')
    # print(encrypted_text)
    encrypted_text_str = encrypted_text.replace("\n", "")
    # print(encrypted_text_str)
    return md5Encoding(encrypted_text_str.encode('utf-8')).upper()


# 加密秘钥需要长达16位字符，所以进行空格拼接
def pad_key(key):
    while len(key) % 16 != 0:
        key += b' '
    return key


def _getUrl():
    return os.environ.get("AMI_AUTH_URL")


def Amiauth(cloudKey, token, propListString, sign, authUrl):
    url = authUrl
    # propList = {"ISCHECKTOKEN": True, "ISCHECKSIGN": False}
    # strpropList = json.dumps(propList, separators=(',', ':'))
    # sign = aesEncoding(strpropList, "")
    headers = {"content-type": "application/json", "cache-control": "no-cache"}
    authdata = {
        "CloudKey": cloudKey,
        "Sign": sign,
        "Token": token,
        "PropListString": propListString
    }
    strAuth = json.dumps(authdata, separators=(',', ':'))
    start_time = get_time()
    response = requests.post(url, data=strAuth, headers=headers)
    # print(response.content)
    end_time = get_time()
    request_time = start_time
    duration = end_time-start_time
    jsonData = response.json()
    request_url = strAuth
    errCode = jsonData["ErrorCode"]
    errMsg = jsonData["ErrorMessage"]

    return errCode, errMsg, response.content, request_url, request_time, duration

def get_time():
    return datetime.datetime.now()
