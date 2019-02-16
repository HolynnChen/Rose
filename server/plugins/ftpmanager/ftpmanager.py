from rose import gb
from rose.helper import template
from aiohttp import web
import jinja2
import datetime
import asyncio
import sqlite3
from functools import wraps
from aiohttp_session import get_session
import time
import re
import hashlib

APP_KEY='1234567890'

gb.plugin_alert('FtpManager',{'introduction': 'Ftp远程管理模块', 'url_enable': True,'url':'ftpmanager','version':'1.0.0','name':'ftpmanager'})

def manager_required(func):  # 用户登录状态校验
    @wraps(func)
    async def inner(cls,request, *args, **kwargs):
        session = await get_session(request)
        uid = session.get('uid')
        obj=ftpmanager()
        if uid and uid in obj.__user_table[uid] and int(time.time()) - obj.__user_table[uid] < 3600:
            obj.__user_table[uid]['pass_time'] = int(time.time())
            return await func(cls, *args, **kwargs)
        else:
            if uid and uid in obj.__user_table: del obj.__user_table[uid]
            return web.Response(status=302, headers={'location': '/ftpmanager/login'})
    return inner

def expect(data,target):return all([i in data for i in target])

class ftpmanager:
    __instance__ = None
    __helper__=None
    __user_table={}
    __server_table={}

    def __new__(cls):
        if not cls.__instance__: cls.__instance__ = object.__new__(cls)
        return cls.__instance__
    def __init__(self):
        if self.__instance__:return
        self.__helper__=sqlite_helper()
        print('FtpManager模块已启用')
    async def default_get(self,request):
        return await self.index_get(request)
    @manager_required
    @template('/ftpmanager/index.html')
    async def index_get(self,request):
        return

    @template('/ftpmanager/login.html')
    async def login_get(self,request):
        return
    async def login_post(self,request):
        data = await request.post()
        if not expect(data,['username''password']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
        user=self.__helper__.check_manager(data['username'],data['password'])
        if user:
            self.__user_table[user['id']]=user
            return web.json_response({'code':302,'redirect':'/ftpmanager/index'})
        else:
            return web.json_response({'code':10001,'msg':'账号或密码错误'})

    @manager_required    
    async def server_list_get(self,request):
        return web.json_response(self.__helper__.get_server_list())
    
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
        session=get_session(request)
        if not session.get('ftpmanager_verify'):return
        server_id=session['server_id']
        self.__server_table[server_id]={'status':1}
        self.__helper__.active_server(server_id)
        await ws.prepare(request)
        try:
            async for msg in ws:
                json = msg.json()
            return ws
        except asyncio.CancelledError:
            self.__server_table[server_id]['status']=2
            print('offline', server_id)
            return ws
        except:
            self.__server_table[server_id]['status']=3
            print('error', server_id)
            return ws

class sqlite_helper:
    __instance__ = None
    _db = None
    _directory=None
    def __new__(cls):
        if not cls.__instance__: cls.__instance__ = object.__new__(cls)
        return cls.__instance__

    def __new_init__(self):
        print('FtpManager:正在初始化')
        self._db=sqlite3.connect(self._directory+'\\ftpmanager.db')
        cursor=self._db.cursor()
        sql_init=[
            'create table users (id integer primary key autoincrement not null, name text not null, password text not null, mail text not null, db_note text)',
            'create table manager (id integer primary key autoincrement not null, name text not null, password text not null, mail text not null, permissions text)',
            'create table server (id integer primary key autoincrement not null, name text not null, ip text not null, status int not null)',
            'create table db_note (id integer primary key autoincrement not null, name text not null, server_id text not null, more text)'
        ]
        for i in sql_init:cursor.execute(i)
        self._db.commit()
        self._add_manager('admin','admin','admin@admin.com')
        self._db.close()
        print('FtpManager:初始化完毕，默认管理员账号admin，默认密码admin')

    def __init__(self):
        import os
        self._directory,_=os.path.split(os.path.realpath(__file__))
        if not os.path.isfile(self._directory+'\\ftpmanager.db'):
            print('FtpManager:数据库文件不存在，尝试创建并初始化')
            self.__new_init__()
        self._db = sqlite3.connect(self._directory + '\\ftpmanager.db')
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

    def _add_server(self,name,ip,status=0):
        cursor = self._db.cursor()
        sql = 'insert into servers (name, ip, status) values (?,?,?)'
        cursor.execute(sql, (name, ip,status))
        self._db.commit()

    def _add_db_note(self,name,server_id,more=''):
        cursor = self._db.cursor()
        sql = 'insert into db_note (name, server_id, more) values (?,?,?)'
        cursor.execute(sql, (name, server_id, more))
        self._db.commit()

    @staticmethod
    def _warp(data,cursor_description):
        column=[i[0] for i in cursor_description]
        if isinstance(data,tuple):
            return dict(zip(column,data))
        else:
            return list(map(lambda x:dict(zip(column,x)),data))


    def get_server_list(self):
        cursor=self._db.cursor()
        sql='select * from server'
        return cursor.execute(sql).fetchall()
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
        sql=special_sql or f'inser into {table} ({",".join(dicts.keys())}) values ({",".join([":"+i for i in dicts.keys()])})'
        if isinstance(dicts,list):cursor.executemany(sql,dicts)
        else:cursor.execute(sql,dicts)
        self._db.commit()
    def update(self,table,value_dict,filter_dict={},column_filter=None,special_sql=None):
        cursor = self._db.cursor()
        temp=",".join([i+'=?' for i in value_dict.keys()])
        sql = special_sql or f'update {table} at {temp}'
        if len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=?' for i in filter_dict.keys()])
        cursor.execute(sql,tuple(value_dict.values()+filter_dict.values()))
        self._db.commit()

    def check_manager(self,username,password):
        key='mail' if re.match(r'^[\w]+[\w._]*@\w+\.[a-zA-Z]+$', username) else 'name'
        return self.search('manager',{key:password})
    
    def active_server(self,server_id):
        if not self.search('server',{'server_id':server_id}):
            self.insert('server',{'server_id':server_id,'status':1})
            return
        self.update('server',{'status':1},{'server_id':server_id})
        
            
