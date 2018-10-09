from .cmscore import Cms
from rose import gb
from rose.helper import template
from aiohttp import web
import jinja2
import datetime
import asyncio

gb.plugin_alert('CMS',{'introduction': 'CMS模块', 'url_enable': True,'url':'cms','version':'1.0.0','name':'cms'})
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
        self._add_column_()
        print('cms running')
        return
    def _add_column_(self):
        columnDic = asyncio.get_event_loop().run_until_complete(Cms()._m.getAll('column'))
        def get_columnUrl(dic,content=False):
            url=f'/{dic["alias"]}'
            if content:url+='/{variable}'
            if dic['rootid']!=0:url=get_columnUrl(columnDic[str(dic['rootid'])])+url
            return url

        def column_index(temp):
            @template(temp)
            async def inner(request):return
            return inner
        def column_content(temp):
            @template(temp)
            async def inner(request):
                try:
                    article=await Cms().getarticle(id=int(request.match_info.get('variable',0)))
                    return {'ArticleNow':article}
                except:
                    return {'ArticleNow':None}
            return inner

        for i in columnDic:
            if 'indexTemplate' in i:
                url=get_columnUrl(i)
                gb.addRoute(column_index(i['indexTemplate']),url,'get','cms')
                gb.addRoute(column_index(i['indexTemplate']), url+'/', 'get', 'cms')
            if 'contentTemplate' in i:gb.addRoute(column_content(i['contentTemplate']),get_columnUrl(i,content=True),'get','cms')

    async def default_get(self,request):
        return await self.index_get(request)
    @template('/cms/index.html')
    async def index_get(self,request):
        return

#    class variable:#名字是随机
#        __variable_name__='column_name'
#        async def default_get(self,request):return await self.index_get(request)
#        async def variable_get(self,request):
#            return await self.index_get(request)
#            #return web.Response(text=f'hello,{request.match_info["column_name"]},{request.match_info["variable"]}')
#        async def index_get(self,request):
#            column_name=request.match_info["column_name"]
#            return

    class user:
        async def default_get(self,request):
            return await self.index_get(request)

        @Cms.redirect('/cms/user',denyLogin=True)
        @template('/cms/user/login.html')
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
        @template('/cms/user/index.html')
        async def index_get(self,request):
            return

        @Cms.redirect('/cms/user/login', requireLogin=True)
        async def exit_get(self,request):
            await Cms().user_exit(request)
            return web.Response(status=302, headers={'location': gb.var['global_route'].route_rewrite("/cms/user/login")})

        @Cms.redirect('',requireLogin=True,constom_JSON={'code':'100001','err_msg':'尚未登录'})
        @template('/cms/user/user_article.html')
        async def user_article_get(self,request):
            startID=request.match_info.get('startID',0)
            columnID=request.match_info.get('columnID',0)
            startPage=request.match_info.get('startPage',1)
            wantPage=request.match_info.get('wantPage',1)
            temp={}
            if columnID and columnID.isdigit():temp['rootid']=int(columnID)
            temp=await Cms()._m.getPage('article',startID=startID,startPage=startPage,wantPage=wantPage,otherCondition=temp)
            return {'article_list':temp}

        @Cms.redirect('', requireLogin=True, constom_JSON={'code': '100001', 'err_msg': '尚未登录'})
        async def column_tree_get(self,request):
            result=await Cms()._m.getAll('column')
            temp={i['id']:i for i in result}
            def getNode(nodeid):
                this={"value":nodeid,"label":temp[nodeid]["name"]} if nodeid else []
                childlist=list(filter(lambda x:x['rootid']==nodeid,result))
                child=[]
                for i in childlist:child.append(getNode(i["id"]))
                if not nodeid:this=child
                elif len(childlist):this["children"]=child
                return this
            return web.json_response(getNode(0))

        @Cms.redirect('/cms/user/login', requireLogin=True)
        @template('/cms/user/add_article.html')
        async def add_article_get(self,request):
            return
        @Cms.redirect('',requireLogin=True,constom_JSON={'code':'100001','err_msg':'尚未登录'})
        async def add_article_post(self,request):
            columnID = request.match_info['nodeID']
            try:
                columnID=int(columnID)
                if not await Cms()._m.getOne('column', 'id', columnID): return web.json_response(
                    {'code': '100002', 'err_msg': '参数不正确'})
            except:
                return web.json_response({'code':'100002','err_msg':'参数不正确'})
            data = await request.post()
            title,editor,status,content=gb.dic_multi_get(['title','editor','status','content'],data)
            if not (title and editor and status and content) or status not in ('0','1'):return web.json_response({'code':'100002','err_msg':'参数不正确'})
            user=await Cms().getUser(request)
            now=datetime.datetime.now()
            await Cms()._m.insertOne('article',{'title':title,'rootid':int(columnID),'creatorid':user['id'],'editor':editor,'creattime':now,'updatetime':now,'content':content,'othermsg':{},'status':int(status)})
            return web.json_response({'code':'0','msg':'success'})


class cmstool_mysql:
    __alias__='cmstool'
    def __init__(self):
        self.mysql=gb.var['application']['cms'].cms_core._m
        self.redis=gb.var['application']['cms'].cms_core._r
        self.__temp__={}
    async def getColumnName(self,ColumnID):
        if not 'ColumnList' in self.__temp__:await self.updateTempColumn()
        return self.__temp__['ColumnList'][str(ColumnID)]['name'] if str(ColumnID) in self.__temp__['ColumnList'] else "栏目不存在"
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
    async def getColumnName(self,ColumnID,alias=False):
        ColumnID=str(ColumnID)
        if not 'ColumnList' in self.__temp__:await self.updateTemp('ColumnList','column')
        if ColumnID not in self.__temp__['ColumnList'] :return "栏目不存在"
        return self.__temp__['ColumnList'][str(ColumnID)]['name'] if not alias else self.__temp__['ColumnList'][str(ColumnID)]['alias']
    async def getUserName(self,UserID):
        result=await self.mongo.getOne('user','id',UserID)
        return result['name'] if result else "用户不存在"
    @jinja2.contextfunction
    async def getUserFullMsg(self,context):
        request=context['request']
        result = await Cms().getUser(request)
        if not 'User_Group' in self.__temp__: await self.updateTemp('User_Group', 'user_group')
        if not 'Model_User' in self.__temp__: await self.updateTemp('Model_User', 'model_user')
        result['othermsg'] = {**self.__temp__['User_Group'][str(result['group'])]['othermsg'],
                              **self.__temp__['Model_User'][str(result['model'])]['othermsg'], **result['othermsg']}
        return result
    async def updateTemp(self,KeyName,CollectionName,tempkey="id"):
        self.__temp__[KeyName] = {str(i[tempkey]): i for i in await self.mongo.getAll(CollectionName)}
    async def getLastArticle(self,ColumnID):
        return await self.mongo.getPage('article',limit=20,otherCondition={'rootid':ColumnID})
    async def getUserArticle(self,ColumnID):
        return await self.mongo.getPage('article',limit=20)
    @staticmethod
    def statusString(status):
        statusDic={0:'正常',1:'未审核',2:'已锁定'}
        return statusDic.get(status,'未知状态')
    @staticmethod
    def timeFormat(time):
        return time.strftime('%Y-%m-%d %H:%M:%S')
    @staticmethod
    def timeFormat_Simply(time):
        return time.strftime('%Y-%m-%d')

    async def getColumnUrl(self,id):
        name=await self.getColumnName(id,alias=True)
        return gb.var['global_route'].route_rewrite(f'/cms/{name}')

    async def getArticleUrlByID(self,id,rootid=None):
        if not rootid:rootid=(await self.mongo.getOne('article','id',id))['rootid']
        name=await self.getColumnName(rootid,alias=True)
        url=f'/cms/{name}/{id}'
        return gb.var['global_route'].route_rewrite(url)

    async def getArticleUrl(self,article):
        try:
            id,rootid=gb.dic_multi_get(['id','rootid'],article)
            return await self.getArticleUrlByID(id,rootid)
        except:
            return '#'
gb.add_rewrite_rule(['replace_start','/cms',''])
gb.addClass(cms)
gb.addTemplateFuncClass(cmstool_mysql if db=='mysql' else cmstool_mongo)