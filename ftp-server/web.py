#This is the main file to run
import asyncio
import gb
gb.init()
import urls
from aiohttp import web
def server_start():
    web.run_app(urls.init())