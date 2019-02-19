import rose.gb as gb
from aiohttp import web
import asyncio
from functools import wraps
import aiohttp_jinja2
import rose.configloader as co
import time
from aiohttp_session import get_session
__all__=['admin']
gb.plugin_table["管理"] = {'introduction': '总管各类插件的应用', 'url_enable': True,'url':'admin','version':'1.0.0','name':'admin','hidden':True}

def admin_login_required(func):  # 用户登录状态校验
    @wraps(func)
    async def inner(cls,request, *args, **kwargs):
        session = await get_session(request)
        uid = session['uid'] if 'uid' in session else None
        if uid and uid in gb.var['user_table'] and int(time.time())-gb.var['user_table'][uid]['pass_time']<3600:
            gb.var['user_table'][uid]['pass_time']=int(time.time())
            request.app.userdata = gb.var['user'][uid]
            request.app.usertable=gb.var['user_table'][uid]
            return await func(cls,request, *args, **kwargs)
        else:
            if uid and uid in gb.var['user_table']:del gb.var['user_table'][uid]
            return web.Response(status=302, headers={'location': '/admin/login'})
    return inner

class admin:
    async def default_get(self,request):
        return web.Response(status=302, headers={'location': '/admin/index'})
    @admin_login_required
    @aiohttp_jinja2.template('/admin/index.html')
    async def index_get(self,request):
        temp=[]
        for i in gb.plugin_table:
            temp.append(gb.plugin_table[i]['name'])
        return {'enable_plugin':temp}
    @admin_login_required
    async def index_post(self,request):
        data=await request.post()
        if not gb.expect(data,['app','data']):return gb.efc(10000)
        app=data['app']
        if app=='plugin_table':
            temp={}
            for i in gb.plugin_table:
                if not 'hidden' in gb.plugin_table[i] or not gb.plugin_table[i]['hidden']:
                    temp[i]=gb.plugin_table[i]
            return web.json_response({'code':200,'msg':'success','data':temp})
    
    @admin_login_required
    async def app_post(self,request):
        data=await request.post()
        if not gb.expect(data,['app','data']):return gb.efc(10000)
        app=data['app']
        if app=='plugin_table':
            temp={}
            for i in gb.plugin_table:
                if not 'hidden' in gb.plugin_table[i] or not gb.plugin_table[i]['hidden']:
                    temp[i]=gb.plugin_table[i]
            return web.json_response({'code':200,'msg':'success','data':temp})
    @aiohttp_jinja2.template('login.html')
    async def login_get(self,request):
        session = await get_session(request)
        if 'uid' in session and 'uid' in gb.var['user_table'] and int(time.time()) - gb.var['user_table'][session['uid']]['pass_time'] < 3600:
            return web.Response(status=302, headers={'location': '/index'})
        else:
            return
    
    async def login_post(self,request):
        data = await request.post()
        if not gb.expect(data,['user','password']):return gb.efc(10000)
        if data['user'] == co.config['admin'] and data['password'] == co.config['password']:
            session = await get_session(request)
            session['uid'] = data['user']
            gb.var['user'][session['uid']] = {}
            gb.var['user_table'][session['uid']] = {}
            gb.var['user_table'][session['uid']]['pass_time'] = int(time.time())
            return web.json_response({'code':302,'msg':'login success','data':{'url':'/admin/index'}})
        else:
            return gb.efc(10001)