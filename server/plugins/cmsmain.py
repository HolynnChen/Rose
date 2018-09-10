from .cmscore import Cms
import rose.gb as gb
from aiohttp import web
import aiohttp_jinja2
import jinja2

gb.plugin_table['CMS']={'introduction': 'CMS模块', 'url_enable': True,'url':'cms','version':'1.0.0','name':'cms'}

class cms:
    #__alias__='cms'
    def __init__(self):
        self.cms_core = Cms() #需要提前开启mongodb
        print('cms running')
        return

    async def default_get(self,request):

        #b=await self.cms_core._m.quickPage('article',20)
        return await self.index_get(request)
    @aiohttp_jinja2.template('/cms/index.html')
    async def index_get(self,request):
        a = await self.cms_core._m.quickPage('article', 20, c_ColumnName='rootid',c_Value='1',ColumnName='article.*,model_article.name as rootname',join=('model_article', 'article.rootid', 'model_article.id'))
        b = await self.cms_core._m.quickPage('article', 20, c_ColumnName='rootid', c_Value='2',ColumnName='article.*,model_article.name as rootname',join=('model_article', 'article.rootid', 'model_article.id'))
        c = await self.cms_core._m.quickPage('article', 20, c_ColumnName='rootid', c_Value='3', ColumnName='article.*,model_article.name as rootname',join=('model_article', 'article.rootid', 'model_article.id'))
        return {'article_study':a,'article_summary':b,'article_diary':c}

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
    async def a(self):return 1
    def b(self):return 2
gb.add_rewrite_rule(['replace_start','/cms',''])
gb.addClass(cms)
gb.addTemplateFuncClass(test)