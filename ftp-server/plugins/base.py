import gb
from aiohttp import web
import asyncio
import aiohttp_jinja2
import aiohttp
import configloader as co
import time
from aiohttp_session import get_session

routes = gb.var['routes']

@routes.get('/')
async def ret(request):
    return web.Response(status=302, headers={'location': '/index'})

@routes.view('/index')
class Index(web.View):
    @gb.login_required
    @aiohttp_jinja2.template('index.html')
    async def get(self):
        return {'userdata': self.request.app.userdata if 'userdata' in self.request.app else None, 'ftp_client': gb.var['websocket_table'],
                'plugin_table': gb.plugin_table}

@routes.view('/login')
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
            return web.Response(status=302, headers={'location': '/index'})
        else:
            return web.Response(status=302, headers={'location': '/login'})

@routes.view('/server/{name}')
class server(web.View):
    @gb.login_required
    @aiohttp_jinja2.template('server.html')
    async def get(self):
        name = self.request.match_info['name']
        if name not in gb.var['websocket_table'] or gb.var['websocket_table'][name]['status'] == 'offline':
            return web.Response(status=302, headers={'location': '/index'})
        s1=await gb.send_msg(name,{'command':'show_all_user','mod_name': 'command'})
        s2=await gb.send_msg(name,{'command':'show_all_project','mod_name': 'command'})
        json1=await gb.receive_json(s1)
        json2=await gb.receive_json(s2)
        return {'ftp_client': gb.var['websocket_table'][name], 'ftp_client_name': name,'ftp_user_list':json1['data']['data'],'ftp_project_list':[i.replace(' ','&nbsp;') for i in json2['data']['data'].splitlines()]}

@routes.post('/server/{name}/{func}')
async def server_function(request):
    name = request.match_info['name']
    func = request.match_info['func']
    data = await request.post()
    if name not in gb.var['websocket_table'] or gb.var['websocket_table'][name]['status'] == 'offline':
        return web.Response(status=302, headers={'location': '/index'})
    if func == 'add_user':
        command = None
        if data['type'] == 'user': command = 'set_user'
        if data['type'] == 'admin': command = 'set_admin'
        if not command:return web.Response(status=302, headers={'location': f'/server/{name}'})
        s=await gb.send_msg(name, {'command': command, 'mod_name': 'command', 'args': [data['username'], data['password']]})
        data=await gb.receive_json(s)
        if data:return web.Response(status=302,headers={'location':f'/server/{name}'})#return web.json_response(data)
        else:return web.Response(status=302, headers={'location': '/server/index'})
    return web.Response(status=302, headers={'location': '/index'})

@routes.get('/ws')
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


gb.update('routes', routes)
gb.plugin_table["基础"] = {'introduction': '集成首页、登陆与基本ftp-client管理功能的模块', 'url_enable': False}
