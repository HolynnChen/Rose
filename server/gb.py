import time
from aiohttp import web
from aiohttp_session import get_session, new_session
from functools import wraps
import asyncio
import async_timeout
import random,string
var={}
plugin_table={}
def init():
    global var
    var['routes']=web.RouteTableDef()
    var['routes_temp']=[]
    var['websocket_table']={}
    var['user']={}
    var['user_table']={}
    var['websocket_respone_table']={}

def update(key,value):
    var[key]=value

def admin_login_required(func):  # 用户登录状态校验 该子程序仅用于示例，若您需要使用用户登录校验请自行复制到模块开头或进行修改
    @wraps(func)
    async def inner(cls, *args, **kwargs):
        session = await get_session(cls.request)
        uid = session['uid'] if 'uid' in session else None
        if uid and uid in var['user_table'] and int(time.time())-var['user_table'][uid]['pass_time']<3600:
            var['user_table'][uid]['pass_time']=int(time.time())
            cls.request.app.userdata = var['user'][uid]
            cls.request.app.usertable=var['user_table'][uid]
            return await func(cls, *args, **kwargs)
        else:
            if uid and uid in var['user_table']:del var['user_table'][uid]
            return web.Response(status=302, headers={'location': '/admin/login'})

    return inner
def random_string():
    return ''.join(random.sample(string.ascii_letters + string.digits, 10))
async def send_msg(name,json):
    if name in var['websocket_table']:
        s=random_string()
        json['identify_string']=s
        await var['websocket_table'][name]['ws'].send_json(json)
        var['websocket_respone_table'][s]=asyncio.Queue()
        return s
    else:
        return False

async def receive_json(s,timeout=5):
    try:
        async with async_timeout.timeout(timeout):
            json=await var['websocket_respone_table'][s].get()
            return json
    except (asyncio.TimeoutError,asyncio.CancelledError):
        return False

def pack(url,method):
    routes = var['routes']
    if url in var['routes_temp']:raise ValueError
    else:var['routes_temp'].append(url)
    if method=='get':
        def pack_get(func):
            @wraps(func)
            @routes.get(url)
            async def inner(cls, *args, **kwargs):return await func(cls, *args, **kwargs)
            update('routes',routes)
            return inner
        return pack_get
    elif method=='post':
        def pack_post(func):
            @wraps(func)
            @routes.post(url)
            async def inner(cls, *args, **kwargs):return await func(cls, *args, **kwargs)
            update('routes',routes)
            return inner
        return pack_post
    elif method=='view':
        def pack_view(func):
            @wraps(func)
            @routes.view(url)
            async def inner(cls, *args, **kwargs):return await func(cls, *args, **kwargs)
            update('routes',routes)
            return inner
        return pack_view
