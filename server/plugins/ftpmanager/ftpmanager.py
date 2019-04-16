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
#import pickle
import json

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
def asyncfunc(func):return lambda *args,**kwargs:asyncio.get_event_loop().run_in_executor(None,lambda:func(*args,**kwargs))

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
        gb.var['app.on_shutdown'].append(self._wst.close())
        print('FtpManager模块已启用')
        self._server_table=self._helper.get_server_list() or {}

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
        user=await self._helper.check_manager(data['username'],data['password'])
        if user:
            self._user_table[user['id']]=user
            session = await get_session(request)
            session['uid']=user['id']
            session['pass_time'] = int(time.time())
            return web.json_response({'code':302,'redirect':'/ftpmanager/index'})
        else:
            return web.json_response({'code':10001,'msg':'账号或密码错误'})
    async def logout_get(self,request):
        session=await get_session(request)
        uid=session.get('uid')
        if not uid:return web.HTTPFound('/ftpmanager/login')
        del session['uid']
        del self._user_table[uid]
        return web.HTTPFound('/ftpmanager/login')
        
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
                await self.super._helper.update('server',{'name':name},{'server_id':data['server_id']})
            return web.json_response({'code':0,'msg':'success'})
        @manager_required
        async def del_server_post(self,request):
            data=await request.post()
            if not expect(data,['server_id']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            if not data['server_id'] in self.super._server_table:return web.json_response({'code':-1,'err_msg':'参数错误'})
            if self.super._server_table[data['server_id']]['status']==1:return web.json_response({'code':-1,'err_msg':'已连接的服务器不可删除，请尝试断开连接后再进行操作'})
            del self.super._server_table[data['server_id']]
            await self.super._helper.delete('server',{'server_id':data['server_id']})
            return web.json_response({'code':0,'msg':'success'})
        
        @manager_required
        async def get_base_user_info_get(self,request):
            temp=await self.super._helper.search('relation',fetchlimit=-1,special_sql="select db_note.server_id, count() as num from relation inner join db_note on relation.db_note=db_note.id group by db_note.server_id") or []
            return web.json_response({'all':(await self.super._helper.search('users',column_filter='count() as number'))['number'],'servers':{i['server_id']:i['num'] for i in temp}})
        
        @manager_required
        async def get_server_notes_post(self,request):
            data=await request.post()
            if not expect(data,['server_id']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            if not data['server_id'] in self.super._server_table:return web.json_response({'code':-1,'err_msg':'参数错误'})
            return web.json_response({'code':0,'data':(await self.super._helper.search('db_note',fetchlimit=-1,filter_dict={'server_id':data['server_id']})) or []})

        @manager_required
        async def get_users_post(self,request):
            data=await request.post()
            if not expect(data,['server_id','db_note','user_keyword']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            #if not data['server_id'] in self.super._server_table:return web.json_response({'code':-1,'err_msg':'参数错误'})
            sql="select distinct users.user_id,users.name,users.mail from (users left join relation on users.user_id=relation.user) left join db_note on relation.db_note=db_note.id"
            want_filt=[]
            if data['server_id']:
                want_filt.append("db_note.server_id=:server_id")
            if data['db_note']:
                want_filt.append("relation.db_note=:db_note")
            if data['user_keyword']:
                want_filt.append("instr(users.name,:user_keyword)>0 or instr(users.mail,:user_keyword)>0")
            if len(want_filt):sql+=' where '+' and '.join(want_filt)
            filter_dict={i:data[i] for i in ['server_id','db_note','user_keyword']}
            return web.json_response({'code':0,'data':await self.super._helper.search('relation',fetchlimit=-1,special_sql=sql,filter_dict=filter_dict) or []})
        
        @manager_required
        async def get_user_post(self,request):
            data=await request.post()
            if not expect(data,['user_id']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            user_info=await self.super._helper.search('users',filter_dict={'user_id':data['user_id']},column_filter="name,user_id,mail")
            sql="select db_note.* from relation inner join db_note on relation.db_note=db_note.id where relation.user=:user_id"
            user_dbnote=await self.super._helper.search('db_note',fetchlimit=-1,special_sql=sql,filter_dict={'user_id':data['user_id']})
            return web.json_response({'code':0,'data':{"user_info":user_info,"user_dbnote":user_dbnote}})

        @manager_required
        async def user_change_post(self,request):
            data=await request.json()
            if not expect(data,['user_id','user_info','user_dbnote']) or not expect(data['user_dbnote'],['addTags','removeTags']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            user_info={i:data['user_info'][i] for i in data['user_info'] if i in ['name','password','mail']}
            if len(user_info)>0:
                if data['user_id']:user_info['user_id']=data['user_id']
                sql="insert or ignore into users("+','.join(user_info)+') values (:'+',:'.join(user_info)+')'
                user_id=await self.super._helper.insert('users',dicts=user_info,special_sql=sql,get_id=True)
                if not data['user_id']:data['user_id']=user_id
                await self.super._helper.update('users',user_info,filter_dict={'user_id':data['user_id']})
            change_dbnote=data['user_dbnote']
            if len(change_dbnote['removeTags'])>0:
                sql="delete from relation where user=:user_id and db_note in (:"+",".join(map(str,range(len(change_dbnote['removeTags']))))+")"
                filter_dict={str(i):change_dbnote['removeTags'][i] for i in range(len(change_dbnote['removeTags']))}
                filter_dict['user_id']=data['user_id']
                await self.super._helper.delete('relation',special_sql=sql,filter_dict=filter_dict)
            if len(change_dbnote['addTags'])>0:
                sql="insert into relation (user,db_note) values (:user_id,:db_note)"
                dicts=[{'user_id':data['user_id'],"db_note":i} for i in change_dbnote['addTags']]
                try:
                    await self.super._helper.insert('relation',special_sql=sql,dicts=dicts)
                except:
                    return web.json_response({'code':-1,'err_msg':'写入异常，即将刷新'})
            await self.super._helper.insert('operation_log',{'operation':'user_change','data':data})
            await self.super._wst.async_operation()
            return web.json_response({'code':0,'msg':'success'})
        @manager_required
        async def user_remove_post(self,request):
            data=await request.post()
            if not expect(data,['user_id']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            await self.super._helper.delete('relation',{'user':data['user_id']})
            await self.super._helper.delete('users',{'user_id':data['user_id']})
            await self.super._helper.insert('operation_log',{'operation':'user_remove','data':data})
            await self.super._wst.async_operation()
            return web.json_response({'code':0,'msg':'删除成功'})

        @manager_required
        async def get_dbnotes_post(self,request):
            data=await request.post()
            if not expect(data,['server_id','dbnote_keyword']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            sql="select id,name,server_id from db_note"
            want_filt=[]
            if data['server_id']:
                want_filt.append("server_id=:server_id")
            if data['dbnote_keyword']:
                want_filt.append("instr(name,:dbnote_keyword)>0")
            if len(want_filt)>0:
                sql+=' where '+' and '.join(want_filt)
            filter_dict={i:data[i] for i in ['server_id','dbnote_keyword']}
            return web.json_response({'code':0,'data':await self.super._helper.search('db_note',special_sql=sql,fetchlimit=-1,filter_dict=filter_dict)})

        @manager_required
        async def get_dbnote_post(self,request):
            data=await request.post()
            if not expect(data,['id']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            result=await self.super._helper.search('db_note',filter_dict={'id':data['id']})
            if not result:return web.json_response({'code':-1,'err_msg':'找不到相应标签'})
            result['more']=result.get('more',{})
            result['path']=result['more'].get('path','')
            result['permissions']=result['more'].get('permissions',[])
            result['more_config']=result['more'].get('more_config',[])
            del result['more']
            return web.json_response({'code':0,'data':result})
        
        @manager_required
        async def dbnote_change_post(self,request):
            data=await request.json()
            if not expect(data,['id','server_id','name','path','permissions','more_config']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
            filter_dict={'server_id':data['server_id'],'name':data['name'],'more':{'path':data['path'],'permissions':data['permissions'],'more_config':data['more_config']}}
            if data['id']:filter_dict['id']=data['id']
            sql="insert or replace into db_note("+','.join(filter_dict)+") values(:"+',:'.join(filter_dict)+")"
            await self.super._helper.insert('user',filter_dict,special_sql=sql)
            await self.super._helper.insert('dbnote_log',{'server_id':data['server_id'],'operation':'dbnote_change','data':data})
            await self.super._wst.async_dbnotes()
            return web.json_response({'code':0,'msg':'success'})

    
    async def ws_confirm_post(self,request):
        data = await request.post()
        if not expect(data,['server_id','verify']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
        if hashlib.sha256((data['verify']+APP_KEY).encode()).hexdigest()==data['server_id']:
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
        await self._helper.active_server(server_id)
        self._server_table[server_id]=await self._helper.search('server',{'server_id':server_id})
        try:
            print('online',server_id)
            asyncio.ensure_future(self._wst.async_all(key=server_id))
            async for msg in ws:
                json = msg.json()
                if expect(json,['data','uuid']):
                    if expect(json['data'],['target','parameters']):
                        if hasattr(self.__tools,json['data']['target']):
                            if asyncio.iscoroutinefunction(getattr(self.__tools,json['data']['target'])):
                                async def inner():
                                    result=await getattr(self.__tools,json['data']['target'])(json['data']['parameters'])
                                    if not result==None:await self._wst.respon(server_id,json['uuid'],result)
                                asyncio.ensure_future(inner())
                            else:
                                result=getattr(self.__tools,json['data']['target'])(json['data']['parameters'])
                                if not result==None:await self._wst.respon(server_id,json['uuid'],result)
                        pass
                    else:
                        self._wst.set(json['uuid'],json['data'])
                    
            return ws
        except asyncio.CancelledError:
            self._server_table[server_id]['status']=0
            await self._helper.change_server_status(server_id,0)
            await self._wst.remove(server_id)
            print('offline', server_id)
            return ws
        except Exception as e:
            print(e)
            self._server_table[server_id]['status']=2
            await self._helper.change_server_status(server_id,2)
            await self._wst.remove(server_id)
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
        self._db=sqlite3.connect(self._directory+'\\ftpmanager.db',check_same_thread=False,detect_types=sqlite3.PARSE_DECLTYPES)
        cursor=self._db.cursor()
        sql_init=[
            'create table users (user_id integer primary key autoincrement not null, name text not null, password text not null, mail text not null)',
            'create table manager (id integer primary key autoincrement not null, name text not null, password text not null, mail text not null, permissions text)',
            'create table server (id integer primary key autoincrement not null, name text not null, server_id text not null, status int not null, more dict)',
            'create table db_note (id integer primary key autoincrement not null, name text not null, server_id text not null, more dict)',
            'create table relation (id integer primary key autoincrement not null, user integer not null, db_note integer not null)',
            'create unique index only on relation (user,db_note)',
            'create table operation_log (id integer primary key autoincrement not null,operation text not null, data dict)',
            'create table dbnote_log (id integer primary key autoincrement not null,server_id text not null,operation text not null, data dict)'
        ]
        for i in sql_init:cursor.execute(i)
        self._db.commit()
        self._add_manager('admin','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918','admin@admin.com')
        self._db.close()
        print('FtpManager:初始化完毕，默认管理员账号admin，默认密码admin')

    def __init__(self):
        import os
        sqlite3.register_adapter(dict,json.dumps)
        sqlite3.register_converter('dict',json.loads)
        self._directory,_=os.path.split(os.path.realpath(__file__))
        if not os.path.isfile(self._directory+'\\ftpmanager.db'):
            print('FtpManager:数据库文件不存在，尝试创建并初始化')
            self.__new_init__()
        self._db = sqlite3.connect(self._directory + '\\ftpmanager.db',check_same_thread=False,detect_types=sqlite3.PARSE_DECLTYPES)
        cursor=self._db.cursor()
        cursor.execute('update server set status=0')#设置所有服务器状态为离线
        self._db.commit()

    def _add_manager(self,name,password,mail,permissions=None):
        cursor=self._db.cursor()
        sql='insert into manager (name, password, mail, permissions) values (?,?,?,?)'
        cursor.execute(sql,(name,password,mail,permissions))
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
    @asyncfunc
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
    @asyncfunc
    def insert(self,table,dicts,special_sql=None,get_id=False):
        cursor=self._db.cursor()
        if isinstance(dicts,dict):
            sql=special_sql or f'insert into {table} ({",".join(dicts.keys())}) values ({",".join([":"+i for i in dicts.keys()])})'
            cursor.execute(sql,dicts)
        else:
            sql=special_sql or f'insert into {table} ({",".join(dicts[0].keys())}) values ({",".join([":"+i for i in dicts[0].keys()])})'
            cursor.executemany(sql,dicts)
        if get_id:
            cursor.execute(f'select last_insert_rowid() as id from {table}')
            result=self._warp(cursor.fetchone(),cursor.description)['id']
            self._db.commit()
            return result
        self._db.commit()
    @asyncfunc
    def update(self,table,value_dict,filter_dict={},special_sql=None):
        cursor = self._db.cursor()
        temp=",".join([i+'=?' for i in value_dict.keys()])
        sql = special_sql or f'update {table} set {temp}'
        if filter_dict and len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=?' for i in filter_dict.keys()])
        cursor.execute(sql,tuple(list(value_dict.values())+list(filter_dict.values())))
        self._db.commit()
    @asyncfunc
    def delete(self,table,filter_dict={},special_sql=None):
        cursor=self._db.cursor()
        sql = special_sql or f'delete from {table}'
        if len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=:'+i for i in filter_dict.keys()])
        cursor.execute(sql,filter_dict)
        self._db.commit()

    async def check_manager(self,username,password):
        key='mail' if re.match(r'^[\w]+[\w._]*@\w+\.[a-zA-Z]+$', username) else 'name'
        return await self.search('manager',{key:username,'password':password})
    
    async def active_server(self,server_id):
        if not await self.search('server',{'server_id':server_id}):
            await self.insert('server',{'server_id':server_id,'status':1,'name':server_id,'more':{}})
            return
        await self.change_server_status(server_id,1)
    async def change_server_status(self,server_id,status):
        await self.update('server',{'status':status},{'server_id':server_id})

class ws_tool:
    wss={}
    ws_msg_dict=gb.async_Dict()
    def __init__(self):self.wss={}
    def add(self,key,ws):self.wss[key]=ws
    async def remove(self,key):
        await self.wss[key].close()
        del self.wss[key]
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
    async def close(self):
        todo=[i.close() for i in self.wss.values()]
        if not len(todo):return
        await asyncio.wait(todo)

    '''以下是ws功能区'''
    async def async_operation(self,key=None):
        data={'type':'ftpmanager_tools','cmd':'async_operation'}
        if not key:await self.send_all(data)
        else:await self.send(key,data)

    async def async_dbnotes(self,key=None):
        data={'type':'ftpmanager_tools','cmd':'async_dbnotes'}
        if not key:await self.send_all(data)
        else:await self.send(key,data)
    async def async_all(self,key=None):
        data={'type':'ftpmanager_tools','cmd':'async_all'}
        if not key:await self.send_all(data)
        else:await self.send(key,data)
    
class ftp_tools:
    def __init__(self,master,helper):
        self._master=master
        self._helper=helper
    async def update_info(self,params):
        if expect(params,['server_id','disk_info']) and params['server_id'] in self._master._server_table:
            self._master._server_table[params['server_id']]['more']['disk_info']=params['disk_info']
            more=await self._helper.search('server',{'server_id':params['server_id']})['more']
            more['disk_info']=params['disk_info']
            await self._helper.update('server',{'more':more},{'server_id':params['server_id']})
    
    async def async_operation(self,params):
        index_id=params['index_id']
        sql="select * from operation_log where id>:id"
        return await self._helper.search('operation_log',fetchlimit=-1,special_sql=sql,filter_dict={'id':index_id})  or []
    
    async def async_dbnotes(self,params):
        server_id,index_id=params['server_id'],params['index_id']
        if server_id not in self._master._server_table:
            return None
        sql=f"select * from dbnote_log where server_id=:server_id and id>:id"
        return await self._helper.search(f'dbnote_log',fetchlimit=-1,special_sql=sql,filter_dict={'server_id':server_id,'id':index_id}) or []

