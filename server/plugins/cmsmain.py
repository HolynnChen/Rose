from .cmscore import Cms
import rose.gb as gb
from aiohttp import web
import aiohttp_jinja2

gb.plugin_table['CMS']={'introduction': 'CMS模块', 'url_enable': True,'url':'cms','version':'1.0.0','name':'cms'}

class cms:
    #__alias__='cms'
    def __init__(self):
        #self.cms_core = Cms() #需要提前开启mongodb
        print('cms running')
        return

    async def default_get(self,request):
        return await self.index_get(request)
    @aiohttp_jinja2.template('/cms/index.html')
    async def index_get(self,request):
        return

    #class variable:#名字是随机
    #    __variable_name__='tool'
    #    async def variable_get(self,request):
    #        return web.Response(text=f'hello,{request.match_info["tool"]},{request.match_info["variable"]}')
    @aiohttp_jinja2.template('/cms/login.html')
    async def login_get(self,request):
        return

    async def login_post(self,requset):
        return web.json_response({})

    class user:
        async def login_get(self,request):
            data=request.getsession()
        async def login_post(self,requset):
            name=await requset.post()
            return web.json_response({})

class test:
    def a(self):return 1
gb.add_rewrite_rule(['replace_start','/cms',''])
gb.addClass(cms)
gb.addTemplateFuncClass(test)