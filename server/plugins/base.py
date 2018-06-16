import gb
from aiohttp import web
import asyncio
import aiohttp_jinja2
import aiohttp
from functools import wraps
import configloader as co
import time
from aiohttp_session import get_session

gb.plugin_table["基础"] = {'introduction': '集成首页、登陆与基本ftp-client管理功能的模块', 'url_enable': True,'url':'../base','version':'1.0.0'}

def login_required(func):
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
            return web.Response(status=302, headers={'location': '/base/login'})
    return inner

@gb.pack('/base','get')
async def ret(request):
    return web.Response(status=302, headers={'location': '/base/index'})

@gb.pack('/base/index','view')
class Index(web.View):
    @login_required
    @aiohttp_jinja2.template('index.html')
    async def get(self):
        return {'userdata': self.request.app.userdata if 'userdata' in self.request.app else None, 'ftp_client': gb.var['websocket_table'],
                'plugin_table': gb.plugin_table}

@gb.pack('/base/login','view')
class Login(web.View):
    @aiohttp_jinja2.template('login.html')
    async def get(self):
        session = await get_session(self.request)
        if 'uid' in session and 'uid' in gb.var['user_table'] and int(time.time()) - gb.var['user_table'][session['uid']]['pass_time'] < 3600:
            return web.Response(status=302, headers={'location': '/base/index'})
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
            return web.Response(status=302, headers={'location': '/base/index'})
        else:
            return web.Response(status=302, headers={'location': '/base/login'})

@gb.pack('/base/server/{name}','view')
class server(web.View):
    @login_required
    @aiohttp_jinja2.template('server.html')
    async def get(self):
        name = self.request.match_info['name']
        if name not in gb.var['websocket_table'] or gb.var['websocket_table'][name]['status'] == 'offline':
            return web.Response(status=302, headers={'location': '/base/index'})
        s1=await gb.send_msg(name,{'command':'show_all_user','mod_name': 'command'})
        s2=await gb.send_msg(name,{'command':'show_all_project','mod_name': 'command'})
        json1=await gb.receive_json(s1)
        json2=await gb.receive_json(s2)
        return {'ftp_client': gb.var['websocket_table'][name], 'ftp_client_name': name,'ftp_user_list':json1['data']['data'],'ftp_project_list':[i.replace(' ','&nbsp;') for i in json2['data']['data'].splitlines()]}

@gb.pack('/base/server/{name}/{func}','post')
@login_required
async def server_function(request):
    name = request.match_info['name']
    func = request.match_info['func']
    data = await request.post()
    if name not in gb.var['websocket_table'] or gb.var['websocket_table'][name]['status'] == 'offline':
        return web.Response(status=302, headers={'location': '/base/index'})
    if func == 'add_user':
        command = None
        if data['type'] == 'user': command = 'set_user'
        if data['type'] == 'admin': command = 'set_admin'
        if not command:return web.Response(status=302, headers={'location': f'/base/server/{name}'})
        s=await gb.send_msg(name, {'command': command, 'mod_name': 'command', 'args': [data['username'], data['password']]})
        data=await gb.receive_json(s)
        if data:return web.Response(status=302,headers={'location':f'/base/server/{name}'})#return web.json_response(data)
        else:return web.Response(status=302, headers={'location': '/base/server/index'})
    elif func=='change_quota':
        command,args=None,None
        if data['type']=='add' and 'name' in data and 'id' in data:
            command='add_project'
            args=[data['name'],data['id']]
        if data['type']=='change' and 'size' in data and 'id' in data:
            command='change_limit'
            args=[data['size'],data['id']]
        if not command: return web.Response(status=302, headers={'location': f'/base/server/{name}'})
        s=await gb.send_msg(name,{'command':command,'mod_name':'command','args':args})
        data=await gb.receive_json(s)
        if data:return web.Response(status=302,headers={'location':f'/base/server/{name}'})#return web.json_response(data)
        else:return web.Response(status=302, headers={'location': '/base/server/index'})

    return web.Response(status=302, headers={'location': '/base/index'})

@gb.pack('/ws','get')
async def webscoket(request):
    ws = web.WebSocketResponse(heartbeat=30, receive_timeout=60)
    await ws.prepare(request)
    name = None
    try:
        async for msg in ws:
            json = msg.json()
            print(json)
            if (json['command'] == 'info'):
                name = json['name']
                if name not in gb.var['websocket_table']: gb.var['websocket_table'][name] = {}
                gb.var['websocket_table'][name]['ws'] = ws
                gb.var['websocket_table'][name]['status'] = 'online'
                await gb.send_msg(name,{'command': 'test', 'mod_name': 'command'})
            elif 'identify_string' in json:
                await gb.var['websocket_respone_table'][json['identify_string']].put(json)
        return ws
    except asyncio.CancelledError:
        gb.var['websocket_table'][name]['status'] = 'offline'
        gb.var['websocket_table'][name]['ws'] = None
        print('offline', name)
        return ws
    except:
        gb.var['websocket_table'][name]['status'] = 'error'
        gb.var['websocket_table'][name]['ws'] = None
        print('error', name)
        return ws
