import gb
from aiohttp import web
import asyncio
import aiohttp_jinja2
import configloader as co
import time
from aiohttp_session import get_session

@gb.pack('/admin','view')
class admin(web.view):
    @gb.login_required
    @aiohttp_jinja2.template('/admin/admin.html')
    async def get(self):
        return {'userdata': self.request.app.userdata if 'userdata' in self.request.app else None,'plugin_table': gb.plugin_table}