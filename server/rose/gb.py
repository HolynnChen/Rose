import time
from aiohttp import web
from aiohttp_session import get_session, new_session
from functools import wraps
from functools import update_wrapper
import asyncio
import async_timeout
import random,string,uuid
import sys,os

var={}
plugin_table={}
def init():
    global var
    var['routes']=web.RouteTableDef()
    var['routes_temp']=[]
    var['websocket_table']={}
    var['user']={}
    var['user_table']={}
    var['websocket_respone_table']={}
    var['global_route']=route()
    var['templateFuncClassDic']={}
    var['init']=[]
    var['application']={}
    #__add_class_func_to_local__(var["global_route"], ['addClass', 'add_rewrite_rule','route_rewrite','addRoute'])

def update(key,value):
    var[key]=value
'''
暴露函数声明区
'''
#global addClass,add_rewrite_rule,route_rewrite,addRoute
def addClass(*arg,**krgs):return var['global_route'].addClass(*arg,**krgs)
def add_rewrite_rule(*arg,**krgs):return var['global_route'].add_rewrite_rule(*arg,**krgs)
def route_rewrite(*arg,**krgs):return var['global_route'].route_rewrite(*arg,**krgs)
def addRoute(*arg,**krgs):return var['global_route'].addRoute(*arg,**krgs)
def delClass(*arg,**krgs):return var['global_route'].delClass(*arg,**krgs)

async def worker():
    print('start worker list')
    getType=lambda x:type(x).__name__
    while True:
        work=None
        try:
            async with async_timeout.timeout(1):
                work = await var['worklist'].get()
        except (asyncio.TimeoutError, asyncio.CancelledError):
            continue
        t=getType(work)
        if t=='function':
            await work()
            return
        elif t in ('tuple','list'):
            if len(work)==2:
                await work[0](work[1])
            elif len(work)==3:
                assert getType(work[2])=='function'
                await work[2](await work[0](work[1]))
            else:raise ValueError
        elif t=='dict':
            temp=None
            assert 'func' not in work
            if 'args' in work:
                if 'unpack_params' in work and work['unpack_params']==True:
                    if getType(work['arg']) in ('tuple','list'):temp= await work['func'](*work['args'])
                    elif getType(work['arg'])=='dict':temp= await work['func'](**work['args'])
                    else: temp= await work['func'](work['args'])
                else:temp= await work['func'](work['args'])
            if 'recv' in work:
                if 'unpack_output' in work and work['unpack_output']==True:
                    if getType(temp) in ('tuple','list'):await work['recv'](*temp)
                    elif getType(temp)=='dict':temp= await work['recv'](**temp)
                    return
                await work['recv'](temp)


def put_work(func):
    if isinstance(func,list):
        for i in func:
            var['worklist'].put_nowait(i)
        return
    var['worklist'].put_nowait(func)
    print(var['worklist'])

def admin_login_required(func):  # 用户登录状态校验 该子程序仅用于示例，若您需要使用用户登录校验请自行复制到模块开头或进行修改
    @wraps(func)
    async def inner(cls, *args, **kwargs):
        session = await get_session(cls.request)
        uid = session['uid'] if 'uid' in session else None
        if uid and uid in var['user_table'] and int(time.time())-var['user_table'][uid]['pass_time']<3600:
            var['user_table'][uid]['pass_time']=int(time.time())
            cls.request.app.userdata = var['user'][uid]
            cls.request.app.usertable=var['user_table'][uid]
            return await func(cls, *args, **kwargs)
        else:
            if uid and uid in var['user_table']:del var['user_table'][uid]
            return web.Response(status=302, headers={'location': '/admin/login'})

    return inner
async def send_msg(name,json):
    if name in var['websocket_table']:
        s=str(uuid.uuid1())
        json['identify_string']=s
        await var['websocket_table'][name]['ws'].send_json(json)
        var['websocket_respone_table'][s]=asyncio.Queue()
        return s
    else:
        return False

async def receive_json(s,timeout=5):
    try:
        async with async_timeout.timeout(timeout):
            json=await var['websocket_respone_table'][s].get()
            return json
    except (asyncio.TimeoutError,asyncio.CancelledError):
        return False

def pack(url,method):
    routes = var['routes']
    if url in var['routes_temp']:raise ValueError
    else:var['routes_temp'].append(url)
    method=getattr(routes,method)
    def pack_get(func):
        @wraps(func)
        @method(url)
        async def inner(cls, *args, **kwargs): return await func(cls, *args, **kwargs)
        update('routes', routes)
        return inner
    return pack_get

def expect(json,keyword):
    return all([json.get(i) for i in keyword])

errorcode={
    10000:{'code':10000,'msg':'login fail','data':''},
    10001:{'code':10001,'msg':'login fail','data':''},
    12000:{'code':12000,'msg':'decrypt error','data':''}
}

def efc(code):
    return web.json_response(errorcode[code])#error from code

class route:
    def __init__(self):
        self.ic=0
        self.routes=[]
        self.rule=[]
        self.__routeDic=['get','post']
        self.__rewriteMethods=['replace_start',]
        self.variableRoutes={}
        self.regUrls=[]
        self.getRandom=lambda :str(uuid.uuid4())
        self.templist=[]
        self.mapping={}
    def addClass(self,controllerClass,parentClassName='',ApplicationName=None)->None:#应当能够匹配多层嵌套的class
        ApplicationName=ApplicationName or controllerClass.__name__
        if not controllerClass.__name__ in self.mapping:
            for i in self.templist:
                if sys._getframe(2).f_code.co_filename.startswith(i):
                    self.mapping[controllerClass.__name__]=i
                    self.templist.remove(i)
                    break
        if len(self.regUrls)==0:self.regUrls=list(map(lambda x:(x.path,x.method,None),var['routes']._items))
        className=str(getattr(controllerClass,'__alias__',controllerClass.__name__))
        if className=="variable":
            route_variable_name=getattr(controllerClass,'__variable_name__',self.getRandom())
            className='{'+route_variable_name+'}'
        #theRandom=self.getRandom()
        shortName=f'{(parentClassName.replace("/",".")+"."+className) if parentClassName!="" else className}'
        if ApplicationName not in var['application']:var['application'][ApplicationName]={}
        var['application'][ApplicationName][shortName]=controllerClass()
        easy=var['application'][ApplicationName][shortName]
        for i in filter(lambda x:not x.startswith('_'),dir(easy)):
            theType=type(getattr(easy,i)).__name__
            if theType=='type':
                self.addClass(getattr(easy,i),f'/{className}' if not parentClassName else f'{parentClassName}/{className}',ApplicationName=ApplicationName)
                continue
            elif not theType in ["function","method"]:
                continue
            for j in self.__routeDic:
                if i.endswith(f'_{j}'):
                    name=i[:-len(f'_{j}')]
                    if name=='variable':name='{variable}'
                    elif name=="default":name=''
                    url=self.route_rewrite(name,className,parentClassName)
                    if len(list(filter(lambda m:m[0]==url and (m[1]==j or m[1]=='*'),self.regUrls))):raise ValueError
                    self.regUrls.append((url,j,ApplicationName))
                    self.routes.append(getattr(web,j)(url,self.wrap(getattr(easy,i),easy,ApplicationName=ApplicationName)))
                    if not name and url[:-1]:
                        url=url[:-1]
                        if len(list(filter(lambda m: m[0] == url and (m[1] == j or m[1] == '*'),self.regUrls))): break
                        self.regUrls.append((url, j,ApplicationName))
                        self.routes.append(getattr(web, j)(url, self.wrap(getattr(easy, i), easy,ApplicationName=ApplicationName)))
        return
    def delClass(self,ApplicationName):
        if len(self.routes):self.routes=list(filter(lambda x:not x.handler.__doc__==ApplicationName,self.routes))
        if len(self.regUrls):
            print(self.regUrls)
            self.regUrls=list(filter(lambda x:not x[2]==ApplicationName,self.regUrls))
        if ApplicationName in var['application']:del var['application'][ApplicationName]
    def addRoute(self,func,url,method,prefix=""):
        name=func.__name__
        if name.startswith('_'):raise NameError("don't start with '_' in the func name")
        if method in self.__routeDic:
            url=("/"+prefix+url) if prefix else url
            url=self.route_rewrite(url)
            self.regUrls.append((url,method))
            self.routes.append(getattr(web, method)(url, self.wrap(func)))
            #var['app'].add_routes([getattr(web, method)(url, self.wrap(func))])
            return
        name="{variable}"
        return
    def route_rewrite(self,string,className=None,parentClassName=None):
        temp=f'{parentClassName}/{className}/{string}'if className or parentClassName else string
        for tmp in self.rule:
            if tmp[0] not in self.__rewriteMethods:continue
            if tmp[0]=='replace_start'and temp.startswith(tmp[1]):temp=temp.replace(tmp[1],tmp[2],1)
        return temp
    def add_rewrite_rule(self,tmp):
        for i in tmp:
            if not type(i).__name__== 'str' or not len(tmp)==3:
                raise ValueError
        if tmp[0] not in self.__rewriteMethods:
            raise ValueError
        self.rule.append(tmp)
        return True
    def wrap(self,func,itclass=None,ApplicationName=None):#修复继承关系
        async def inner(request):
            url=str(request._rel_url)
            temp={}
            if '?' in url:
                url=url.split('?')[1]
                url_list=url.split('&')
                for i in url_list:
                    k=i.split('=')
                    if len(k)==2:temp[k[0]]=k[1]
            request.reqDic=temp
            request.match_info.update(temp)
            if func.__name__=='variable':request.variable=request.match_info['variable']
            #try:
            #    return await func(request)
            #except Exception as e:
            #    print(e)
            #    return web.Response(text="抱歉，您所访问的应用出错了")
            return await func(request)
        inner.__doc__=ApplicationName
        inner.__name__=func.__name__#进行名字修复
        return inner
def __add_class_func_to_local__(obj,func_list):
    temp=dir(obj)
    for i in func_list:
        if i in temp and type(getattr(obj,i)).__name__ in ["function","method"]:
            if i in globals():raise NameError
            globals()[i]=getattr(obj,i)

def addTemplateFuncClass(obj,static=False):
    if not type(obj).__name__ == "type":raise ValueError
    name=getattr(obj,'__alias__',obj.__name__)
    if name in var['templateFuncClassDic']:raise NameError
    var['templateFuncClassDic'][name]=(obj() if not static else obj)

def dic_multi_get(key_list,dic,default_value=None):return list(map(lambda x:dic.get(x,default_value),key_list))

def plugin_alert(Name,object):
    plugin_table[Name] = object

class async_Dict():
    '''使用该类可作为异步字典。写入是实时的，获取是异步的。支持异步del，可用于超时删除。'''
    def __init__(self,loop=None):
        self._loop=loop or asyncio.get_event_loop()
        self._getters={}
        self._dict={}
        self._del={}
    def set(self,key,value):
        '''实时写入
        :param key:字典的key
        :param value: 字典的value
        :return: None
        '''
        if key in self._del:
            return self._dict.pop(key)
        self._dict[key]=value
        self._wakeup(key)
    @asyncio.coroutine
    def get(self,key):
        '''异步写入
        :param key: 字典的key
        :return: None
        '''
        while key not in self._dict:
            getter=self._loop.create_future()
            self._getters[key]=getter
            try:
                yield from getter
            except:
                getter.cancel()
                try:
                    del self._getters[key]
                except KeyError:
                    pass
                raise
        return self._dict.pop(key)
    
    def async_del(self,key):
        if key in self._dict:del self._dict[key]
        else:self._del[key]=True
    def _wakeup(self,key):
        if key in self._getters:
            getter=self._getters.pop(key)
            if not getter.done():
                getter.set_result(None)
