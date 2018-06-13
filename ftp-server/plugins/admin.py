import gb
from aiohttp import web
import asyncio
import aiohttp_jinja2
import configloader as co
import time
from aiohttp_session import get_session

@gb.pack('/admin','get')
async def ret(request):
    return

