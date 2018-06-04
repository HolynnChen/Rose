import os
import gb
import time
import base64
from cryptography import fernet
from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import aiohttp_jinja2,jinja2
for root, dirs, files in os.walk('plugins'):
    for i in files:
        if not i=='__init__.py':__import__('plugins.'+i.split('.')[0])
def init():
    BASE_DIR = os.getcwd()      # 项目路径
    STATIC_DIR = os.path.join(BASE_DIR, 'static')       # 静态文件路径
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'template')   # 模版HTML路径
    app = web.Application()
    routes=gb.var['routes']
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
    app.router.add_static('/static/', path=STATIC_DIR, name='static')
    app.router.add_routes(routes)
    return app
