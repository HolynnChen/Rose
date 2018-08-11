import asyncio
import os
import base64
import hashlib
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_jinja2,jinja2
import rose.gb as gb
import rose.configloader as co
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass
gb.init()
from aiohttp import web
from aiohttp.web import middleware
from threading import Thread

for root, dirs, files in os.walk('plugins'):
    for i in files:
        if not i=='__init__.py':__import__('plugins.'+i.split('.')[0])
    break

#enable gloabl header change for cors
@middleware
async def middleware(request, handler):
    resp = await handler(request)
    resp.headers['Access-Control-Allow-Origin']='*'
    return resp

def init():
    BASE_DIR = os.getcwd()      # 项目路径
    STATIC_DIR = os.path.join(BASE_DIR, 'static')       # 静态文件路径
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'template')   # 模版HTML路径
    app = web.Application(middlewares=[middleware])
    routes=gb.var['routes']
    secret_key='This is the default secret_key'
    secret_key=hashlib.md5(base64.b64encode(secret_key.encode())).hexdigest().encode()
    setup(app, EncryptedCookieStorage(secret_key))
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR),variable_start_string='{{{',variable_end_string='}}}')
    app.router.add_static('/static/', path=STATIC_DIR, name='static')
    app.router.add_routes(routes)
    app.add_routes([web.get('/',lambda request:web.Response(status=302, headers={'location': '/admin/login' if 'index' not in co.config else co.config['index']}))])
    return app

def keep_worker():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(gb.worker())
def server_start():
    Thread(target=keep_worker).start()
    web.run_app(init(),port=co.config['port'] if 'port' in co.config else 8080)