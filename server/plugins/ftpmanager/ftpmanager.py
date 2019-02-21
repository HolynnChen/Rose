from rose import gb
from rose.helper import template
from aiohttp import web
import aiohttp
import jinja2
import datetime
import asyncio
import sqlite3
from functools import wraps
from aiohttp_session import get_session
import time
import re
import hashlib
import uuid,sys,traceback
import async_timeout
import threading
import pickle

APP_KEY='1234567890'
__all__=['ftpmanager']
gb.plugin_alert('FtpManager',{'introduction': 'Ftp远程管理模块', 'url_enable': True,'url':'ftpmanager','version':'1.0.0','name':'ftpmanager'})


def manager_required(func):  # 用户登录状态校验
    @wraps(func)
    async def inner(cls, request, *args, **kwargs):
        session = await get_session(request)
        uid = session.get('uid')
        obj = ftpmanager()
        if uid and uid in obj._user_table and int(time.time()) - session['pass_time'] < 3600:
            session['pass_time'] = int(time.time())
            return await func(cls,request, *args, **kwargs)
        else:
            if uid and uid in obj._user_table: del obj._user_table[uid]
            #return web.Response(status=302, headers={'location': '/ftpmanager/login'})
            return web.HTTPFound('/ftpmanager/login')

    return inner

def expect(data,target):return all([i in data for i in target])

async def sorted_wait(tasks):
    async def index(i,task):
        result=await task
        return i,result 
    s,_=await asyncio.wait([index(i,tasks[i]) for i in range(len(tasks))])
    s=list(map(lambda x:x[1],sorted([i.result() for i in s],key=lambda x:x[0])))
    return s

class ftpmanager:
    __instance__ = None
    _helper=None
    _user_table={}
    _server_table={}
    _wst=None

    def __new__(cls):
        if not cls.__instance__: cls.__instance__ = object.__new__(cls)
        return cls.__instance__
    def __init__(self):
        if self._helper:return
        self._helper=sqlite_helper()
        self._wst=ws_tool()
        self.__tools=ftp_tools(self,self._helper)
        print('FtpManager模块已启用')
        self._server_table=self._helper.get_server_list() or {}
        for i in self._server_table:
            self._server_table[i]['more']=pickle.loads(self._server_table[i]['more'])


    async def default_get(self,request):
        return await self.index_get(request)

    @manager_required
    @template('/ftpmanager/index.html')
    async def index_get(self,request):
        return

    @template('/ftpmanager/login.html')
    async def login_get(self,request):
        session=await get_session(request)
        uid = session.get('uid')
        if uid and uid in self._user_table and int(time.time()) - session['pass_time'] < 3600:
            return web.HTTPFound('/ftpmanager/index')
        return
    async def login_post(self,request):
        data = await request.post()
        if not expect(data,['username','password']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
        user=self._helper.check_manager(data['username'],data['password'])
        if user:
            self._user_table[user['id']]=user
            session = await get_session(request)
            session['uid']=user['id']
            session['pass_time'] = int(time.time())
            return web.json_response({'code':302,'redirect':'/ftpmanager/index'})
        else:
            return web.json_response({'code':10001,'msg':'账号或密码错误'})
        
    async def test_get(self,request):
        ss=await self._wst.send_all({'type':'ftpmanager_tools','cmd':'get_disk_info'})
        if not len(ss):return web.json_response([])
        r=await sorted_wait([self._wst.get(i) for i in ss])
        return web.json_response(r)
    class api:
        def __init__(self):
            self.super=ftpmanager()
        @manager_required
        async def async_info_get(self,request):
            return web.json_response(self.super._server_table)
        @manager_required
        async def change_server_info_post(self,request):
            data=await request.post()
            if not expect(data,['server_id','target','data']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            if not data['server_id'] in self.super._server_table:return web.json_response({'code':-1,'err_msg':'参数错误'})
            if not data['target'] in ['name']:return web.json_response({'code':-1,'err_msg':'非法修改'})
            if data['target']=='name':
                name=str(data['data'])
                if len(name)<3 or len(name)>15:return web.json_response({'code':-1,'err_msg':'参数错误'})
                self.super._server_table[data['server_id']]['name']=name
                self.super._helper.update('server',{'name':name},{'server_id':data['server_id']})
            return web.json_response({'code':0,'msg':'success'})
        @manager_required
        async def del_server_post(self,request):
            data=await request.post()
            if not expect(data,['server_id']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            if not data['server_id'] in self.super._server_table:return web.json_response({'code':-1,'err_msg':'参数错误'})
            if self.super._server_table[data['server_id']]['status']==1:return web.json_response({'code':-1,'err_msg':'已连接的服务器不可删除，请尝试断开连接后再进行操作'})
            del self.super._server_table[data['server_id']]
            self.super._helper.delete('server',{'server_id':data['server_id']})
            return web.json_response({'code':0,'msg':'success'})
    
    async def ws_confirm_post(self,request):
        data = await request.post()
        if not expect(data,['server_id','verify']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
        if hashlib.sha256((data['server_id']+APP_KEY).encode()).hexdigest()==data['verify']:
            session=await get_session(request)
            session['ftpmanager_verify']=True
            session['server_id']=data['server_id']
            return web.json_response({'code':0,'msg':'success'})
        return web.json_response({'code':10001,'msg':'verify fail'})


    async def ws_keep_get(self,request):
        ws = web.WebSocketResponse(heartbeat=30, receive_timeout=60)
        await ws.prepare(request)
        session=await get_session(request)
        if not expect(session,['ftpmanager_verify','server_id']) or not session.get('ftpmanager_verify'):return web.Response(status=404,reason='非法登陆')
        server_id=session['server_id']
        self._wst.add(server_id,ws)
        self._helper.active_server(server_id)
        self._server_table[server_id]=self._helper.search('server',{'server_id':server_id})
        self._server_table[server_id]['more']=pickle.loads(self._server_table[server_id]['more'])
        try:
            print('online',server_id)
            async for msg in ws:
                json = msg.json()
                if expect(json,['data','uuid']):
                    self._wst.set(json['uuid'],json['data'])
                elif expect(json,['target','parameters','uuid']):
                    if hasattr(self.__tools,json['target']):
                        result=getattr(self.__tools,json['target'])(json['parameters'])
                        await self._wst.respon(server_id,json['uuid'],result)
                    pass
            return ws
        except asyncio.CancelledError:
            self._server_table[server_id]['status']=0
            self._helper.change_server_status(server_id,0)
            print('offline', server_id)
            return ws
        except:
            self._server_table[server_id]['status']=2
            self._helper.change_server_status(server_id,2)
            print('error', server_id)
            return ws

class sqlite_helper:
    __instance__ = None
    _db = None
    _directory=None
    def close(self):
        self._db.close()

    def __new_init__(self):
        print('FtpManager:正在初始化')
        self._db=sqlite3.connect(self._directory+'\\ftpmanager.db',check_same_thread=False)
        cursor=self._db.cursor()
        sql_init=[
            'create table users (id integer primary key autoincrement not null, name text not null, password text not null, mail text not null, db_note text)',
            'create table manager (id integer primary key autoincrement not null, name text not null, password text not null, mail text not null, permissions text)',
            'create table server (id integer primary key autoincrement not null, name text not null, server_id text not null, status int not null, more blob)',
            'create table db_note (id integer primary key autoincrement not null, name text not null, server_id text not null, more text)'
        ]
        for i in sql_init:cursor.execute(i)
        self._db.commit()
        self._add_manager('admin','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918','admin@admin.com')
        self._db.close()
        print('FtpManager:初始化完毕，默认管理员账号admin，默认密码admin')

    def __init__(self):
        import os
        self._directory,_=os.path.split(os.path.realpath(__file__))
        if not os.path.isfile(self._directory+'\\ftpmanager.db'):
            print('FtpManager:数据库文件不存在，尝试创建并初始化')
            self.__new_init__()
        self._db = sqlite3.connect(self._directory + '\\ftpmanager.db',check_same_thread=False)
        cursor=self._db.cursor()
        cursor.execute('update server set status=0')#设置所有服务器状态为离线
        self._db.commit()

    def _add_manager(self,name,password,mail,permissions=None):
        cursor=self._db.cursor()
        sql='insert into manager (name, password, mail, permissions) values (?,?,?,?)'
        cursor.execute(sql,(name,password,mail,permissions))
        self._db.commit()

    def _add_user(self,name,password,mail,db_note):
        cursor = self._db.cursor()
        sql = 'insert into users (name, password, mail, db_note) values (?,?,?,?)'
        cursor.execute(sql, (name, password, mail, db_note))
        self._db.commit()

    def _add_server(self,name,ip,status=0,more=pickle.dumps({})):
        cursor = self._db.cursor()
        sql = 'insert into servers (name, ip, status, more) values (?,?,?,?)'
        cursor.execute(sql, (name, ip,status,more))
        self._db.commit()

    def _add_db_note(self,name,server_id,more=''):
        cursor = self._db.cursor()
        sql = 'insert into db_note (name, server_id, more) values (?,?,?)'
        cursor.execute(sql, (name, server_id, more))
        self._db.commit()

    @staticmethod
    def _warp(data,cursor_description):
        column=[i[0] for i in cursor_description]
        if not data:return None
        if isinstance(data,tuple):
            return dict(zip(column,data))
        else:
            return list(map(lambda x:dict(zip(column,x)),data))


    def get_server_list(self):
        cursor=self._db.cursor()
        sql='select * from server'
        result=self._warp(cursor.execute(sql).fetchall(),cursor.description)
        if not result:return {}
        return {i['server_id']:i for i in result}
    def search(self,table,filter_dict={},column_filter=None,fetchlimit=0,special_sql=None):
        cursor = self._db.cursor()
        sql = special_sql or f'select {column_filter or "*"} from {table}'
        if len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=:'+i for i in filter_dict.keys()])
        cursor.execute(sql,filter_dict)
        if fetchlimit<0:return self._warp(cursor.fetchall(),cursor.description)
        elif fetchlimit==0:return self._warp(cursor.fetchone(),cursor.description)
        else: return self._warp(cursor.fetchmany(fetchlimit),cursor.description)
    def insert(self,table,dicts,special_sql=None):
        cursor=self._db.cursor()
        sql=special_sql or f'insert into {table} ({",".join(dicts.keys())}) values ({",".join([":"+i for i in dicts.keys()])})'
        if isinstance(dicts,list):cursor.executemany(sql,dicts)
        else:cursor.execute(sql,dicts)
        self._db.commit()
    def update(self,table,value_dict,filter_dict={},special_sql=None):
        cursor = self._db.cursor()
        temp=",".join([i+'=?' for i in value_dict.keys()])
        sql = special_sql or f'update {table} set {temp}'
        if filter_dict and len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=?' for i in filter_dict.keys()])
        cursor.execute(sql,tuple(list(value_dict.values())+list(filter_dict.values())))
        self._db.commit()
    def delete(self,table,filter_dict={},special_sql=None):
        cursor=self._db.cursor()
        sql = special_sql or f'delete from {table}'
        if len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=:'+i for i in filter_dict.keys()])
        cursor.execute(sql,filter_dict)
        self._db.commit()

    def check_manager(self,username,password):
        key='mail' if re.match(r'^[\w]+[\w._]*@\w+\.[a-zA-Z]+$', username) else 'name'
        return self.search('manager',{key:username,'password':password})
    
    def active_server(self,server_id):
        if not self.search('server',{'server_id':server_id}):
            self.insert('server',{'server_id':server_id,'status':1,'name':server_id,'more':pickle.dumps({})})
            return
        self.change_server_status(server_id,1)
    def change_server_status(self,server_id,status):self.update('server',{'status':status},{'server_id':server_id})

class ws_tool:
    wss={}
    ws_msg_dict=gb.async_Dict()
    def __init__(self):self.wss={}
    def add(self,key,ws):self.wss[key]=ws
    def server_id_list(self):return list(self.wss.keys())
    async def send(self,key,json,s=None):
        s=s or uuid.uuid1().hex
        await self.wss[key].send_json({'data':json,'uuid':s})
        return s
    async def get(self,s,timeout=5):
        try:
            async with async_timeout.timeout(timeout):
                json=await self.ws_msg_dict.get(s)
                return json
        except (asyncio.TimeoutError,asyncio.CancelledError):
            self.ws_msg_dict.async_del(s)
            return None
    def set(self,s,v):self.ws_msg_dict.set(s,v)
    async def respon(self,key,s,json):await self.send(key,json,s=s)
    async def send_all(self,json):
        if not len(self.wss):return []
        return await sorted_wait([self.send(i,json) for i in self.wss])

class ftp_tools:
    def __init__(self,master,helper):
        self._master=master
        self._helper=helper
    def update_info(self,params):
        if expect(params,['server_id','disk_info']) and params['server_id'] in self._master._server_table:
            self._master._server_table[params['server_id']]['more']['disk_info']=params['disk_info']
            more=pickle.loads(self._helper.search('server',{'server_id':params['server_id']})['more'])
            more['disk_info']=params['disk_info']
            self._helper.update('server',{'more':pickle.dumps(more)})
