import os
import gb
import time
import base64
import hashlib
from cryptography import fernet
from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_jinja2,jinja2
import configloader as co
for root, dirs, files in os.walk('plugins'):
    for i in files:
        if not i=='__init__.py':__import__('plugins.'+i.split('.')[0])
    break
def init():
    BASE_DIR = os.getcwd()      # 项目路径
    STATIC_DIR = os.path.join(BASE_DIR, 'static')       # 静态文件路径
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'template')   # 模版HTML路径
    app = web.Application()
    routes=gb.var['routes']
    secret_key='This is the default secret_key'
    secret_key=hashlib.md5(base64.b64encode(secret_key.encode())).hexdigest().encode()
    setup(app, EncryptedCookieStorage(secret_key))
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
    app.router.add_static('/static/', path=STATIC_DIR, name='static')
    app.router.add_routes(routes)
    app.add_routes([web.get('/',lambda request:web.Response(status=302, headers={'location': '/admin/login' if 'index' not in co.config else co.config['index']}))])
    return app
