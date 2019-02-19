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
import aiohttp.web
from threading import Thread
import importlib,gc

def load_plugin():
    enable_list=co.config.get('enable_plugin',[])
    for _, dirs, files in os.walk('plugins'):
        for i in dirs:
            if os.path.exists(f'plugins/{i}/__init__.py') and i in enable_list:
                mod=importlib.import_module('.'+i,package='plugins')
                for j in getattr(mod,'__all__',[]):
                    mini_mod=importlib.import_module(f'.{i}.{j}',package='plugins')
                    gb.var['global_route'].tempmap[mini_mod.__name__]=mini_mod.__file__
                    gb.add_mini_mod(mini_mod)
        for i in files:
            if not i=='__init__.py' and i.split('.')[0] in enable_list:
                mini_mod=importlib.import_module('.'+i.split('.')[0],package='plugins')
                gb.var['global_route'].tempmap[mini_mod.__name__]=mini_mod.__file__
                gb.add_mini_mod(mini_mod)
        break
    

#enable gloabl header change for cors
@middleware
async def middleware_allow(request, handler):
    if request.path=="/favicon.ico":return aiohttp.web.Response(status=302,headers={'location':'/static/favicon.ico'})
    resp = await handler(request)
    resp.headers['Access-Control-Allow-Origin']='*'
    return resp

def init():
    BASE_DIR = os.getcwd()      # 项目路径
    STATIC_DIR = os.path.join(BASE_DIR, 'static')       # 静态文件路径
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'template')   # 模版HTML路径
    app = aiohttp.web.Application(middlewares=[middleware_allow])#
    routes=gb.var['routes']
    secret_key='This is the default secret_key'
    secret_key=hashlib.md5(base64.b64encode(secret_key.encode())).hexdigest().encode()
    setup(app, EncryptedCookieStorage(secret_key))

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR),variable_start_string='{{{',variable_end_string='}}}',enable_async=True,context_processors=[aiohttp_jinja2.request_processor])
    app.router.add_static('/static/', path=STATIC_DIR, name='static')
    app.router.add_routes(routes)
    aiohttp_jinja2.get_env(app).globals.update(gb.var['templateFuncClassDic'])
    print(f"\033[1;32;45m*** creat {len(gb.var['global_route'].routes)} route ***\033[0m")
    app.router.add_routes(gb.var['global_route'].routes)
    return app

def keep_worker():
    loop = asyncio.new_event_loop()
    gb.var['worklist'] = asyncio.Queue(loop=loop)
    loop.run_until_complete(gb.worker())
def keep_Timer():
    loop = asyncio.new_event_loop()
    gb.var['Timer'] = asyncio.Queue(loop=loop)
    gb.Timer_add(gc.collect,600)
    loop.run_until_complete(gb.Timer())
def server_start(devmode=False):
    Thread(target=keep_worker).start()
    Thread(target=keep_Timer).start()
    load_plugin()
    loop = asyncio.get_event_loop()
    while True:
        app=init()
        if 'app' in gb.var:del gb.var['app']
        gb.var['app']=app
        gb.var['app_loop'] = loop
        if devmode:
            import aiohttp_debugtoolbar
            aiohttp_debugtoolbar.setup(app)
        runner=aiohttp.web.AppRunner(app)
        loop.run_until_complete(runner.setup())
        site = aiohttp.web.TCPSite(runner, 'localhost', co.config['port'] if 'port' in co.config else 8080)
        try:
            loop.run_until_complete(site.start())
            print(f'======== Running on {site._host}:{site._port} ========')
            loop.run_forever()
            print('应用已关闭，准备重启')
            loop.run_until_complete(runner.cleanup())
            gc.collect()
        except:
            print('未知错误')
            loop.run_until_complete(runner.cleanup())
            break


