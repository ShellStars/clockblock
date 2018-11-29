import flask
import logging
import time
import datetime
import pymongo
from flask import Flask, request, session, Response
from flask import make_response
from io import BytesIO
from tool import *
from config import *
app = Flask(__name__)
app.config['SECRET_KEY'] = '123456'

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/piccode')
def get_piccode():
    image, str = validate_picture()
    buf = BytesIO()
    image.save(buf, 'jpeg')
    buf_str = buf.getvalue()
    response = make_response(buf_str)
    response.headers['Content-Type'] = 'image/gif'
    session['image'] = str
    return response


@app.route('/smscode/', methods=['POST'])
def get_smscode():
    if 'phonenum' not in request.values:
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    smscode = create_smscode()
    inset_mongo('smscode',{"_id" : phonenum, "phonenum" : phonenum, "createtime" : int(time.time()), "smscode": smscode, "expiretime" : datetime.datetime.utcnow()})
    if send_smscode(phonenum):
        return Response(response=flask.json.dumps(code_status(2003)))
    else:
        return Response(response=flask.json.dumps(code_status(4008)))


@app.route('/register/', methods=['POST'])
def register():
    if not ('phonenum' in request.values and 'smscode' in request.values and 'piccode' in request.values and 'password' in request.values):
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    usernum = find_mongo('user',{'_id':phonenum}).count()
    if usernum > 0:
        return Response(response=flask.json.dumps(code_status(4003)))
    else:
        smscode = request.values['smscode']
        smsfind = find_mongo('smscode',{'_id':phonenum})
        if smsfind.count() > 0 and smsfind[0]['smscode'] == smscode:
            piccode = request.values['piccode']
            if piccode == session.get('image'):
                password = request.values['password']
                invitationcode = ''
                if 'invitationcode' in request.values:
                    try:
                        result = find_mongo('invitationcode', {'_id': request.values['invitationcode']})
                        if result.count() == 0:
                            return Response(response=flask.json.dumps(code_status(4001)))
                        else:
                            invitationcode = request.values['invitationcode']
                            update_mongo('invitationcode', {'_id': result[0]['_id']},
                                         {'usenum': result[0]['usenum'] + 1})
                            update_mongo('invitationcode', {'_id': result[0]['_id']},
                                         {'updatetime':int(time.time())})

                            power_increment = find_mongo('power', {'userphone': phonenum})
                            update_mongo('power', {'userphone':phonenum},
                                    {'power_increment': power_increment[0]['power_increment'] + invite_friends_value})
                    except Exception as e:
                        logging.error(e)
                        return Response(response=flask.json.dumps(code_status(500)))
                idnum = create_id('user','userid',10)
                tag = []
                if int(idnum.lstrip('0')) < 2000:
                    tag.append('创世节点')

                code = calculation_invite_code()
                while(True):
                    if find_mongo('invitationcode',{'_id':code}).count() == 0:
                        break
                    code = calculation_invite_code()
                inset_mongo('invitationcode',{'_id':code, 'updatetime':int(time.time()), 'invitationcode':code, 'usenum':0, 'phonenum':phonenum,'createtime':int(time.time())})
                inset_mongo('usertag',{'_id':phonenum,'createtime':int(time.time()),'updatetime':int(time.time()),'tags':tag})
                inset_mongo('user',{'_id':phonenum,'phone':phonenum,'updatetime':int(time.time()),'password': md5encrypt(password),'certificate_type':'','certificate_number':'','invitecode':invitationcode,'nickname': '','createtime':int(time.time()),'id':idnum,'headpic':Default_headpic,'truename':'','isident':0})
                inset_mongo('power',{'_id':phonenum,'phonenum':phonenum,'total':0,'updatetime':int(time.time()),'createtime':int(time.time()),'items':[]})
                inset_mongo('asset',{'_id':phonenum,'phonenum':phonenum,'total':0,'updatetime':int(time.time()),'createtime':int(time.time()),'items':[]})
                return Response(response=flask.json.dumps(code_status(2001)))
            else:
                return Response(response=flask.json.dumps(code_status(4005)))
        else:
            return Response(response=flask.json.dumps(code_status(4004)))


@app.route('/login/',methods=['POST'])
def login():
    if not ('phonenum' in request.values and 'password' in request.values):
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user',{'_id':phonenum})
    if phone.count() > 0:
        password = request.values['password']
        if md5encrypt(password) == phone[0]['password']:
            return Response(response=flask.json.dumps(code_status(2002)))
        else:
            return Response(response=flask.json.dumps(code_status(4007)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/myinfo/',methods=['GET'])
def myinfo():
    if 'phonenum' not in request.values:
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum})
    if phone.count() > 0:
        headpic = phone[0]['headpic']
        number = phone[0]['id'].lstrip('0')
        nikename = phone[0]['nickname']
        tags = find_mongo('usertag',{'_id':phonenum})[0]['tags']
        result = {'headpic':headpic,'nikename':nikename,'number':number,'tags':tags}
        return Response(response=flask.json.dumps(code_status(200, result)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/modifymyinfo/',methods=['POST'])
def modifymyinfo():
    if not('phonenum' in request.values and 'nickname' in request.values):
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user',{'_id':phonenum}).count()
    if phone > 0:
        update_mongo('user', {'_id':phonenum}, {'nickname':request.values['nickname']})
        return Response(response=flask.json.dumps(code_status(2004)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/userident/',methods=['POST'])
def userident():
    if not('phonenum' in request.values and 'certificate_type' in request.values and 'certificate_number' in request.values and 'truename' in request.values):
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum}).count()
    if phone > 0:
        certificate_type = request.values['certificate_type']
        certificate_number = request.values['certificate_number']
        truename = request.values['truename']
        identdata = find_mongo('user',{'certificate_type':certificate_type,'certificate_number':certificate_number}).count()
        if identdata > 0:
            return Response(response=flask.json.dumps(code_status(4010)))
        else:
            update_mongo('user',{'_id':phonenum},{'isident':1,'certificate_type':certificate_type,'certificate_number':certificate_number,'truename':truename})
            return Response(response=flask.json.dumps(code_status(2006)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/isident/',methods=['GET'])
def isident():
    if 'phonenum' not in request.values:
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum})
    if phone.count() > 0:
        if phone[0]['isident'] == 1:
            return Response(response=flask.json.dumps(code_status(2005)))
        else:
            return Response(response=flask.json.dumps(code_status(4009)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/identinfo/',methods=['GET'])
def identinfo():
    if 'phonenum' not in request.values:
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum})
    if phone.count() > 0:
        truename = phone[0]['truename']
        number = phone[0]['id']
        idcard = phone[0]['certificate_number']
        result = {'truename':truename,'idcard':idcard,'number':number}
        return Response(response=flask.json.dumps(code_status(200, result)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/myassethistory/',methods=['GET'])
def myassethistory():
    if 'phonenum' not in request.values:
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum})
    if phone.count() > 0:
        assethis = sortlistofdict(find_mongo('asset',{'_id':phonenum})[0]['items'],'updatetime')
        return Response(response=flask.json.dumps(code_status(200, assethis)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/getasset/',methods=['POST'])
def getasset():
    if not('phonenum' in request.values and 'assetnum' in request.values):
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum}).count()
    if phone > 0:
        assetnum = request.values['assetnum']
        assetinfo = find_mongo('asset',{'_id':phonenum})
        if assetinfo.count() > 0:
            oritotal = assetinfo[0]['total']
            oridata = assetinfo[0]['items']
            oridata.append({'createtime':int(time.time()),'updatetime':int(time.time()),'asset_increment':assetnum})
            newtotal = oritotal + float(assetnum)
            update_mongo('asset',{'_id':phonenum},{'total':newtotal,'updatetime':int(time.time()),'items':oridata})
            return Response(response=flask.json.dumps(code_status(2007)))
        else:
            return Response(response=flask.json.dumps(code_status(500)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/mypower/',methods=['GET'])
def mypower():
    if 'phonenum' not in request.values:
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum})
    if phone.count() > 0:
        mypower = find_mongo('power',{'_id':phonenum})
        powernum = mypower[0]['total']
        powersort = find_mongo('power',{'total':{"$gt":powernum}}).count()+1
        result = {'mypower':powernum,'powerranking':powersort}
        return Response(response=flask.json.dumps(code_status(200, result)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


@app.route('/globaldata/',methods=['GET'])
def globaldata():
    if 'phonenum' not in request.values:
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum})
    if phone.count() > 0:
        globalpower = [aggregate_mongo('power', [{'$group': {'_id': '', 'total': {'$sum': "$total"}}}]).next()][0]['total']
        toptower = [{'nickname':find_mongo('user',{'_id':i['userphone']})[0]['nikename'],'power':i['total']} for i in find_mongo('power',{}).sort([("total",pymongo.DESCENDING)]).limit(10)]
        globalasset = [aggregate_mongo('asset', [{'$group': {'_id': '', 'total': {'$sum': "$total"}}}]).next()][0]['total']
        todaytimestamp = int(time.mktime((datetime.date.today()).timetuple()))
        todayasset = [aggregate_mongo('asset',[{"$match": {"items.updatetime": {"$gt":todaytimestamp}}},{"$unwind": "$items"},{"$match": {"items.updatetime": {"$gt":todaytimestamp}}},{'$group': {'_id': '', 'total': {'$sum': "$items.asset_increment"}}}]).next()][0]['total']
        result = {'globalpower':globalpower,'toptower':toptower,'globalasset':globalasset,'todayasset':todayasset}
        return Response(response=flask.json.dumps(code_status(200, result)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))

@app.route('/invitefriends/', methods=['POST'])
def invitefriends():
    if 'phonenum' not in request.values:
        return Response(response=flask.json.dumps(code_status(4001)))
    phonenum = request.values['phonenum']
    phone = find_mongo('user', {'_id': phonenum})
    if phone.count() > 0:
        invitationcode = find_mongo('invitationcode', {'phonenum': phonenum})[0]['invitationcode']
        result = {'invitationcode':invitationcode}
        return Response(response=flask.json.dumps(code_status(200, result)))
    else:
        return Response(response=flask.json.dumps(code_status(4006)))


if __name__ == '__main__':
    app.run()
