import logging
import hashlib
import time
from PIL import Image, ImageFont, ImageDraw, ImageFilter
from config import *
from pymongo import MongoClient
import random
import string
def validate_picture():
    total = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012345789'
    width = 130
    heighth = 50
    im = Image.new('RGB',(width, heighth), 'white')
    font = ImageFont.truetype('fixedsys.ttf', 40)
    draw = ImageDraw.Draw(im)
    str = ''
    for item in range(5):
        text = random.choice(total)
        str += text
        draw.text((5+random.randint(4,7)+20*item,5+random.randint(3,7)), text=text, fill='black',font=font )
    for num in range(8):
        x1 = random.randint(0, width/2)
        y1 = random.randint(0, heighth/2)
        x2 = random.randint(0, width)
        y2 = random.randint(heighth/2, heighth)
        draw.line(((x1, y1),(x2,y2)), fill='black', width=1)
    im = im.filter(ImageFilter.FIND_EDGES)
    return im, str


def code_status(code, data=''):
    return {'code': code, 'message': error_message[code], 'data': data}


def find_mongo(index, params):
    client = MongoClient(Mongo_host, Mongo_port)
    db_auth = client[Mongo_db]
    db_auth.authenticate(Mongo_user, Mongo_password)
    collection = db_auth[index]
    result = collection.find(params)
    client.close()
    return result


def aggregate_mongo(index, params):
    client = MongoClient(Mongo_host, Mongo_port)
    db_auth = client[Mongo_db]
    db_auth.authenticate(Mongo_user, Mongo_password)
    collection = db_auth[index]
    result = collection.aggregate(params)
    client.close()
    return result


def inset_mongo(index, params):
    try:
        client = MongoClient(Mongo_host, Mongo_port)
        db_auth = client[Mongo_db]
        db_auth.authenticate(Mongo_user, Mongo_password)
        collection = db_auth[index]
        collection.insert(params)
        client.close()
        return True
    except Exception as e:
        logging.error(e)
        return False


def update_mongo(index, params_old, param_new):
    try:
        client = MongoClient(Mongo_host, Mongo_port)
        db_auth = client[Mongo_db]
        db_auth.authenticate(Mongo_user, Mongo_password)
        collection = db_auth[index]
        collection.update(params_old, {'$set':param_new})
        client.close()
        return True
    except Exception as e:
        logging.error(e)
        return False


def delete_mongo(index, params):
    try:
        client = MongoClient(Mongo_host, Mongo_port)
        db_auth = client[Mongo_db]
        db_auth.authenticate(Mongo_user, Mongo_password)
        collection = db_auth[index]
        collection.remove(params)
        client.close()
        return True
    except Exception as e:
        logging.error(e)
        return False


def md5encrypt(data):
    return hashlib.md5(data.encode(encoding='utf-8')).hexdigest()


def create_id(index,nodename,num):
    return str(getNextValue(index,nodename)).zfill(num)


def create_smscode():
    smscode = ''
    for i in range(6):
        smscode += str(random.randint(0, 9))
    return smscode


def getNextValue(index, nodename):
    try:
        client = MongoClient(Mongo_host, Mongo_port)
        db_auth = client[Mongo_db]
        db_auth.authenticate(Mongo_user, Mongo_password)
        collection = db_auth[index]
        ret = collection.find_and_modify({"_id": nodename}, {"$inc": {"sequence_value": 1}}, safe=True, new=True)
        newid = ret["sequence_value"]
        client.close()
        return newid
    except Exception as e:
        logging.error(e)
        return False


def sortlistofdict(listdata,keyword,order=True,transformtime=True):
    # order:True from now to old
    result = sorted(listdata, key=lambda x : x[keyword], reverse=order)
    if transformtime == True:
        result = [{'asset': i['asset_increment'], 'updatetime': unixtotime(i['updatetime'])} for i in result]
    return result


def unixtotime(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(timestamp))


def send_smscode(phonenum):
    if True:
        return True
    else:
        return False

def calculation_invite_code():
    base_string = string.digits + string.ascii_letters
    card_code = ''
    for j in range(6):
        card_code += random.choice(base_string)
    return card_code
validate_picture()