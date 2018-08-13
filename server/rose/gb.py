import time
from aiohttp import web
from aiohttp_session import get_session, new_session
from functools import wraps
import asyncio
import async_timeout
import random,string

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

def update(key,value):
    var[key]=value
async def worker():
    var['worklist']=asyncio.Queue()
    print('start worker list')
    while True:
        work=await var['worklist'].get()
        await work()

async def put_work(func):
    if str(type(func)).split("'")[1]=='list':
        for i in func:
            await var['worklist'].put_nowait(i)
        return
    await var['worklist'].put_nowait(func)

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
def random_string():
    return ''.join(random.sample(string.ascii_letters + string.digits, 10))
async def send_msg(name,json):
    if name in var['websocket_table']:
        s=random_string()
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
    if method=='get':
        def pack_get(func):
            @wraps(func)
            @routes.get(url)
            async def inner(cls, *args, **kwargs):return await func(cls, *args, **kwargs)
            update('routes',routes)
            return inner
        return pack_get
    elif method=='post':
        def pack_post(func):
            @wraps(func)
            @routes.post(url)
            async def inner(cls, *args, **kwargs):return await func(cls, *args, **kwargs)
            update('routes',routes)
            return inner
        return pack_post
    elif method=='view':
        def pack_view(func):
            @wraps(func)
            @routes.view(url)
            async def inner(cls, *args, **kwargs):return await func(cls, *args, **kwargs)
            update('routes',routes)
            return inner
        return pack_view

def expect(json,keyword):
    for i in keyword:
        if i not in json:
            return False
    return True

errorcode={
    10000:{'code':10000,'msg':'login fail','data':''},
    10001:{'code':10001,'msg':'login fail','data':''},
    12000:{'code':12000,'msg':'decrypt error','data':''}
}

def efc(code):
    return web.json_response(errorcode[code])#error from code

class route:
    def __init__(self):
        self.routes=[]
        self.rule=[]
        self.__routeDic=['get','post']
        self.__rewriteMethods=['replace_start',]
        self.obj={}
    def addClass(self,controllerClass,parentClassName='')->None:#应当能够匹配多层嵌套的class
        className=controllerClass.__name__
        self.obj[className]=controllerClass()
        for i in filter(lambda x:not x.startswith('__') and not x.startswith('_'),dir(self.obj[className])):
            if str(type(i)).split("'")[1]=='class':
                self.addClass(i,f'/{className}' if not parentClassName else f'{parentClassName}/{className}')
                continue
            elif not not str(type(i)).split("'")[1]=="function":
                continue
            for j in self.__routeDic:
                if i.endswith(f'_{j}'):
                    self.routes.append(getattr(web,j)(self.route_rewrite(i[:-len(f'_{j}')],className,parentClassName),self.wrap(getattr(self.obj[className],i),self.obj[className])))
                    #self.routes.append(getattr(web,j)(self.route_rewrite(i[:-len(f'_{j}')],className,parentClassName),getattr(self.obj[className],i)))
                    break

        return
    def route_rewrite(self,string,className,parentClassName):
        temp=f'{parentClassName}/{className}/{string}'
        for tmp in self.rule:
            if tmp[0] not in self.__rewriteMethods:continue
            if tmp[0]=='replace_start'and temp.startswith(tmp[1]):temp=temp.replace(tmp[1],tmp[2],1)
        return temp
    def add_rewrite_rule(self,tmp):
        for i in tmp:
            if not str(type(i)).split("'")[1]== 'str' or not len(tmp)==3:
                raise ValueError
        if tmp[0] not in self.__rewriteMethods:
            raise ValueError
        self.rule.append(tmp)
        return True
    def wrap(self,func,itsclass):#修复继承关系
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
            return await func(request)
        inner.__name__=func.__name__#进行名字修复
        return inner