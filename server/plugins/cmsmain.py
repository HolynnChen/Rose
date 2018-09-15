from .cmscore import Cms
import rose.gb as gb
from aiohttp import web
import aiohttp_jinja2
import time

gb.plugin_table['CMS']={'introduction': 'CMS模块', 'url_enable': True,'url':'cms','version':'1.0.0','name':'cms'}
db='mongodb'
class cms:
    #__alias__='cms'
    __instance__=None
    ColumnList=None
    def __new__(cls):
        if not cls.__instance__:cls.__instance__=object.__new__(cls)
        return cls.__instance__

    def __init__(self):
        self.cms_core = Cms('mongodb') #需要提前开启mongodb
        print('cms running')
        return

    async def default_get(self,request):

        #b=await self.cms_core._m.quickPage('article',20)
        return await self.index_get(request)
    @aiohttp_jinja2.template('/cms/index.html')
    async def index_get(self,request):
        return

    class variable:#名字是随机
        __variable_name__='column_name'
        async def default_get(self,request):return await self.index_get(request)
        async def variable_get(self,request):
            return await self.index_get(request)
            #return web.Response(text=f'hello,{request.match_info["column_name"]},{request.match_info["variable"]}')
        async def index_get(self,request):
            column_name=request.match_info["column_name"]
            return


    class user:
        async def default_get(self,request):
            return await self.index_get(request)

        @Cms.redirect('/cms/user',denyLogin=True)
        @aiohttp_jinja2.template('/cms/user/login.html')
        async def login_get(self,request):
            return

        async def login_post(self,request):
            data=await request.post()
            user_name=data.get('user',None)
            password=data.get('password',None)
            if not user_name or not password:return web.json_response({'code':-1,'err_msg':'参数不完整'})
            value=await Cms()._m.getOne('user','name',user_name,{'password':password})
            if not value:return web.json_response({'code':10002,'err_msg':'用户名或密码错误'})
            await Cms().user_login(request,user_name,value)
            return web.json_response({'code':0,'msg':'Login Success'})

        @Cms.redirect('/cms/user/login',requireLogin=True)
        @aiohttp_jinja2.template('/cms/user/index.html')
        async def index_get(self,request):
            return


class cmstool_mysql:
    __alias__='cmstool'
    def __init__(self):
        self.mysql=gb.var['application']['cms'].cms_core._m
        self.redis=gb.var['application']['cms'].cms_core._r
        self.__temp__={}
    async def getColumnName(self,ColumnID):
        if not 'ColumnList' in self.__temp__:await self.updateTempColumn()
        return self.__temp__['ColumnList'][str(ColumnID)]['name']
    async def getUserName(self,UserID):
        result= await self.mysql.getOne('user','id',UserID)
        return result['name']
    async def updateTempColumn(self):
        self.__temp__['ColumnList'] = {str(i['id']):i for i in await self.mysql.getAll('column')}
    async def getLastArticle(self,ColumnID):
        return await self.mysql.getPage('article',20,c_ColumnName='rootid',c_Value=ColumnID)

class cmstool_mongo:
    __alias__='cmstool'
    def __init__(self):
        self.mongo=gb.var['application']['cms'].cms_core._m
        self.redis=gb.var['application']['cms'].cms_core._r
        self.__temp__={}
    async def getColumnName(self,ColumnID):
        if not 'ColumnList' in self.__temp__:await self.updateTempColumn()
        return self.__temp__['ColumnList'][str(ColumnID)]['name']
    async def getUserName(self,UserID):
        result=await self.mongo.getOne('user','id',UserID)
        return result['name']
    async def updateTempColumn(self):
        self.__temp__['ColumnList']={str(i['id']):i for i in await self.mongo.getAll('column')}
    async def getLastArticle(self,ColumnID):
        return await self.mongo.getPage('article',limit=20,otherCondition={'rootid':ColumnID})
gb.add_rewrite_rule(['replace_start','/cms',''])
gb.addClass(cms)
gb.addTemplateFuncClass(cmstool_mysql if db=='mysql' else cmstool_mongo)