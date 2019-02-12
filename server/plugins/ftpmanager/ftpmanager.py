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

gb.plugin_alert('FtpManager',{'introduction': 'Ftp远程管理模块', 'url_enable': True,'url':'ftpmanager','version':'1.0.0','name':'ftpmanager'})

def manager_required(func):  # 用户登录状态校验
    @wraps(func)
    async def inner(cls, *args, **kwargs):
        session = await get_session(cls.request)
        uid = session['uid'] if 'uid' in session else None
        if uid and uid in gb.var['user_table'] and int(time.time()) - gb.var['user_table'][uid]['pass_time'] < 3600:
            gb.var['user_table'][uid]['pass_time'] = int(time.time())
            cls.request.app.userdata = gb.var['user'][uid]
            cls.request.app.usertable = gb.var['user_table'][uid]
            return await func(cls, *args, **kwargs)
        else:
            if uid and uid in gb.var['user_table']: del gb.var['user_table'][uid]
            return web.Response(status=302, headers={'location': '/admin/login'})
    return inner

class ftpmanager:
    __instance__ = None
    __helper__=None

    def __new__(cls):
        if not cls.__instance__: cls.__instance__ = object.__new__(cls)
        return cls.__instance__
    def __init__(self):
        self.__helper__=sqlite_helper()
        print('FtpManager模块已启用')
    async def default_get(self,request):
        return await self.index_get(request)
    @template('/ftpmanager/index.html')
    async def index_get(self,request):
        return

    @template('/ftpmanager/login.html')
    async def login_get(self,request):
        return
    async def login_post(self,request):
        data = await request.post()
        if not gb.expect(data,['username''password']):return web.json_response({'code':-1,'err_msg':'参数不完整'})
        
    async def server_list_get(self,request):
        return web.json_response(self.__helper__.get_server_list())

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

    def get_server_list(self):
        cursor=self._db.cursor()
        sql='select * from server'
        return cursor.execute(sql).fetchall()
