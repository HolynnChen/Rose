import asyncio
import gb
import configloader as co
gb.init()
import urls
from aiohttp import web
def server_start():
    web.run_app(urls.init(),port=co.config['port'] if 'port' in co.config else 8080)