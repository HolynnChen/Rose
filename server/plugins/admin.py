import gb
from aiohttp import web
import asyncio
from functools import wraps
import aiohttp_jinja2
import configloader as co
import time
from aiohttp_session import get_session

gb.plugin_table["管理"] = {'introduction': '总管各类插件的应用', 'url_enable': True,'url':'../admin','version':'1.0.0'}

def admin_login_required(func):  # 用户登录状态校验
    @wraps(func)
    async def inner(cls, *args, **kwargs):
        session = await get_session(cls.request)
        uid = session['uid'] if 'uid' in session else None
        if uid and uid in gb.var['user_table'] and int(time.time())-gb.var['user_table'][uid]['pass_time']<3600:
            gb.var['user_table'][uid]['pass_time']=int(time.time())
            cls.request.app.userdata = gb.var['user'][uid]
            cls.request.app.usertable=gb.var['user_table'][uid]
            return await func(cls, *args, **kwargs)
        else:
            if uid and uid in gb.var['user_table']:del gb.var['user_table'][uid]
            return web.Response(status=302, headers={'location': '/admin/login'})
    return inner

@gb.pack('/admin','get')
async def ret(request):
    return web.Response(status=302, headers={'location': '/admin/index'})

@gb.pack('/admin/index','view')
class Admin(web.View):
    @admin_login_required
    @aiohttp_jinja2.template('/admin/index.html')
    async def get(self):
        return {'userdata': self.request.app.userdata if 'userdata' in self.request.app else None,'plugin_table': gb.plugin_table}

@gb.pack('/admin/login','view')
class Login(web.View):
    @aiohttp_jinja2.template('login.html')
    async def get(self):
        session = await get_session(self.request)
        if 'uid' in session and 'uid' in gb.var['user_table'] and int(time.time()) - gb.var['user_table'][session['uid']]['pass_time'] < 3600:
            return web.Response(status=302, headers={'location': '/index'})
        else:
            return

    async def post(self):
        data = await self.request.post()
        if data['user'] == co.config['admin'] and data['password'] == co.config['password']:
            session = await get_session(self.request)
            session['uid'] = data['user']
            gb.var['user'][session['uid']] = {}
            gb.var['user_table'][session['uid']] = {}
            gb.var['user_table'][session['uid']]['pass_time'] = int(time.time())
            return web.Response(status=302, headers={'location': '/admin/index'})
        else:
            return web.Response(status=302, headers={'location': '/admin/login'})

