import asyncio
import os
import base64
import hashlib
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_jinja2,jinja2
from . import gb
from . import configloader as co
from aiohttp.web import middleware
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass
gb.init()
from aiohttp import web
from threading import Thread

for root, dirs, files in os.walk('plugins'):
    for i in dirs:
        if os.path.exists(f'plugins/{i}/__init__.py'):__import__(f'plugins.{i}')
    for i in files:
        if not i=='__init__.py':__import__('plugins.'+i.split('.')[0])
    break

#enable gloabl header change for cors
@middleware
async def middleware_allow(request, handler):
    if request.path=="/favicon.ico":return web.Response(status=302,headers={'location':'/static/favicon.ico'})
    resp = await handler(request)
    resp.headers['Access-Control-Allow-Origin']='*'
    return resp

def init():
    BASE_DIR = os.getcwd()      # 项目路径
    STATIC_DIR = os.path.join(BASE_DIR, 'static')       # 静态文件路径
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'template')   # 模版HTML路径
    app = web.Application(middlewares=[middleware_allow])#
    routes=gb.var['routes']
    secret_key='This is the default secret_key'
    secret_key=hashlib.md5(base64.b64encode(secret_key.encode())).hexdigest().encode()
    setup(app, EncryptedCookieStorage(secret_key))

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR),variable_start_string='{{{',variable_end_string='}}}',enable_async=True,context_processors=[aiohttp_jinja2.request_processor])
    app.router.add_static('/static/', path=STATIC_DIR, name='static')
    app.router.add_routes(routes)
    aiohttp_jinja2.get_env(app).globals.update(gb.var['templateFuncClassDic'])
    print(f"\033[1;32;40m*** creat {len(gb.var['global_route'].routes)} route ***\033[0m")
    app.add_routes(gb.var['global_route'].routes)
    return app

def keep_worker():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(gb.worker())
def server_start(devmode=False):
    Thread(target=keep_worker).start()
    app=init()
    gb.var['app']=app
    if devmode:
        import aiohttp_debugtoolbar
        aiohttp_debugtoolbar.setup(app)
    #asyncio.get_event_loop().run_until_complete(asyncio.sleep(1)) #给予初始化缓冲时间
    web.run_app(app,port=co.config['port'] if 'port' in co.config else 8080)


