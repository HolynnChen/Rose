# 目标
# 1.完成信息储存，信息删除，信息读取api，尽量做到字典结构体储存
# 2.完成路由处理，请求响应文件
# 3.完成动态处理，返回响应结果，全json执行，vue前端
# 4.完成基础管理后台搭建
# 5.技术储备:aiohttp+mongodb+redis+vue+
# 6.设计原则:要一定程度上确保原子操作
import rose.gb as gb
from functools import wraps
from aiohttp_session import get_session
import time
from aiohttp import web
import aredis
import asyncio
import json
import motor
import motor.motor_asyncio
import aiomysql
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP
import base64
from pymongo import ReturnDocument,ASCENDING,DESCENDING

#-----BEGIN PUBLIC KEY-----
#MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDTHDl9GNx0l1qOiNQQDXvwk2dY
#pZK5OLgXblLl72fiosHzqO/gQq7g6ETkB5WWv9zaumMdGmnwdGuF3yzRstmfYne3
#cBwGalvkU//DihAf64jrwRA197w27jRCPl9XarR3tRvEs9EaF7kz+OZpdBzdm9/0
#I9RXrDPvN3zRrbZ2FQIDAQAB
#-----END PUBLIC KEY-----

key='''-----BEGIN PRIVATE KEY-----
MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBANMcOX0Y3HSXWo6I
1BANe/CTZ1ilkrk4uBduUuXvZ+KiwfOo7+BCruDoROQHlZa/3Nq6Yx0aafB0a4Xf
LNGy2Z9id7dwHAZqW+RT/8OKEB/riOvBEDX3vDbuNEI+X1dqtHe1G8Sz0RoXuTP4
5ml0HN2b3/Qj1FesM+83fNGttnYVAgMBAAECgYAVxbhsHW9HGwD86EGusiVRJ3Km
ItViAuaBjCBClJFLP2vvXEH5CAePLIVGWz3jQUBe0pA8RSgd43PfZ6fwrJhi9r1n
4nXu7TlHbI0Nf8Z3kR0uEYVJujYlrnLYc+VR68tDs8pTNuIkJTKwzcBDS/OVtzCU
xf3WsGPeZ1ys3iszlQJBAPNI2QLujGt+QAsaNLkP1Uo/OWAFRJKDrE7YJ9pKxIvY
33C30pRsKlw3s1j8TfI4EW+8xAiVQLUIhPVN/wof7BcCQQDeJOJLebSB1MrPfOf7
TyxOxFScYUoeXFZ7vKa6rBUU+YkTuC45GSWKYz1qvB/39LfEHsu3AUBRGkPre6nQ
se6zAkEAnDr90VorpqQOsJKFpQo76FAtojH/1S7lqkQ5Y398NGpzIsmJW3MSyOGk
NNLho1jKKb1JDlH6mcb8yyLpUzEoxQJBAIPjpi9lfNQwgJEb+adtZEMHsax+3sCT
1gz0/pCKJqIjXU1F5rujwHQfY5GBTAGtW4WnOw/WQFdmnriq3TG40p0CQQCgzeIZ
dLpsPCmZFHuuWmNPm61lNPu9l6JSC7tUaOmkMdCQo4rKyo/e/2wDk+kDKJkdc88y
DNwOSAgk7ZNzQ+NB
-----END PRIVATE KEY-----'''
ukey=PKCS1_OAEP.new(RSA.import_key(key))

def decrypt(str,isbase64=True):
    try:
        if isbase64:
            str=base64.b64decode(str)
        return ukey.decrypt(str).decode()
    except:
        return None


def login_required(func):  # 用户登录状态校验
    @wraps(func)
    async def inner(cls, *args, **kwargs):
        session = await get_session(cls.request)
        uid = session['uid'] if 'uid' in session else None
        if uid and uid in gb.var['user_table'] and int(time.time()) - gb.var['user_table'][uid]['pass_time'] < 3600:
            gb.var['user_table'][uid]['pass_time'] = int(time.time())
            cls.request.app.userdata = gb.var['user'][uid]
            cls.request.app.usertable = gb.var['user_table'][uid]
            return await func(cls, *args, **kwargs)
        else:
            if uid and uid in gb.var['user_table']: del gb.var['user_table'][uid]
            return web.Response(status=302, headers={'location': '/admin/login'})
    return inner

class Cms:
    def __init__(self):
        #self._m=MongoConnect()
        self._m=MysqlConnect()
        self._r=RedisConnect()
    async def getuser(self,id=None,name=None,special_rule=None):
        if id:
            return await self._m.d.user.find_one({'id':id})
        elif name:
            return await self._m.d.user.find({'name':name})
        else:
            return await self._m.d.user.find(special_rule)

    async def getarticle(self,id=None,special_rule=None):
        if id :
            return await self._m.d.article.find_one({'id':id})
        else:
            return await self._m.d.article.find(special_rule)

    async def getcolumn(self,id=None,special_rule=None):
        if id :
            return await self._m.d.column.find_one({'id':id})
        else:
            return await self._m.d.column.find(special_rule)

    async def makesure(self,_session_id,_auth):
        temp=decrypt(_auth)
        if temp:return False
        salt=temp[-8:]
        isexit=await self._r.c.exists(_session_id)
        if not isexit:
            await self._r.c.setex(f'user:{_session_id}:salt',salt,3600)
            return True
        if salt == await self._r.get(f'user:{_session_id}:salt'):
            await self._r.c.expire(f'user:{_session_id}:salt',3600)
            return True
        return False

    def login(self,func):
        @wraps(func)
        async def inner(cls,*args,**kwargs):
            session =await get_session(cls.request)
            uid = session['uid'] if 'uid' in session else None
            if uid and await self._r.c.exists(uid):
                temp=await cls.request.post()
                if '_auth' in  temp and not await self.makesure(uid,temp['_auth']):return gb.efc(12000)
                return await func(cls,*args,**kwargs)
            return web.Response(status=302, headers={'location': '/login'})
        return inner


class RedisConnect:
    def __init__(self, host='localhost', port=6379, decode_responses=True):
        self.host=host
        self.port=port
        self.decode_response=decode_responses
        self.c=aredis.StrictRedis(host=self.host, port=self.port)

    def __len__(self):
        return

    async def set(self, key, value):
        t = self.type(value)
        if t == "str" or t == "int":
            await self.c.mset(key, value)
        if t == "list":
            await self.c.lset(key, value)
        if t == "dict":
            await self.c.hmset(key, value)

    async def get(self, key):
        #尝试进行自动解析
        temp=await self.c.get(key)
        return json.loads(temp.decode())

    @staticmethod
    def type(obj):#可以返回的类型有str int list dict
        return str(type(obj)).split("'")[1]

    @staticmethod
    def change(obj):#进行编码修正，在确定没有二次的情况下进行解析，对元素解析至int/string/bool
        #第一步，进行快速decode
        return
    @staticmethod
    def decode(obj):
        return  json.loads(f'"{obj.decode()}"')

class MongoConnect:
    def __init__(self,host='localhost',port=27017):
        self.c=motor.motor_asyncio.AsyncIOMotorClient('localhost', 27017)
        #if 'cmsmongo' not in self.c.list_database_names():
        #    self._newinit_()
        #else:
        #    self.d=self.c['cmsmongo']
        self.d=self.c['cmsmongo']

    def _newinit_(self):
        #创建表,默认取cmsmongo，后加个vue来改初始化内容
        self.d=self.c['cmsmongo']
        self.d.insert_one({'config':{},'model':{}})
        #之后这里是各种初始化、环境配置等

    async def getNextID(self,name):
        counter=await self.d['counter'].find_one_and_update({'_id':name},{'$inc':{'seq':1}},projection={'seq':True,'_id':False},upsert=True,return_document=ReturnDocument.AFTER)
        return counter['seq']
    async def getCount(self,CollectionName,filter={}):
        return await self.d[CollectionName].count_documents(filter=filter)
    async def getPage(self,CollectionName,startID=0,startPage=1,wantPage=1,limit=20,otherCondition={}):
        next=wantPage>=startPage
        query='$gte' if next else '$lt'
        cusor=self.d[CollectionName].find({'ID':{query:startID}}.update(otherCondition),sort=[("ID",DESCENDING if next else ASCENDING)],skip=(wantPage-startPage)*limit if startPage-wantPage>=0 else (startPage-wantPage-1)*limit)
        result=await cusor.to_list(length=limit)
        if next:return result
        else:return result[::-1]
    async def getLast(self,CollectionName,limit=20):
        cusor=self.d[CollectionName].find(sort=[{"ID":DESCENDING}],limit=limit)
        return await cusor.to_list(length=limit)

class MysqlConnect:
    def __init__(self,host='localhost',port=3306,user='root',password='123456',db='RoseCMS'):
        self.p=aiomysql.create_pool(host=host,port=port,user=user,password=password,db=db)
        asyncio.ensure_future(self.init())
    async def init(self):
        self.p=await self.p
    async def getCount(self,TableName):
        return
    async def quickIDlist(self,TableName,limit,ColumnName=None,Value=None,offset=0):
        sql=SQL().Select(TableName,'id')
        if ColumnName and Value:sql.Where().Eq(ColumnName,Value)
        sql.Orderby('id').Limit(limit,offset)
        async with self.p.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql.text)
                temp=await cur.fetchall()
                return list(map(lambda x:str(x[0]),temp))
    async def quickPage(self,TableName,limit,ColumnName='*',c_ColumnName=None,c_Value=None,c_offset=0,dic=True,join=None):
        csql = SQL().Select(TableName, 'id')
        if c_ColumnName and c_Value: csql.Where().Eq(c_ColumnName, c_Value)
        csql.Orderby('id').Limit(limit, c_offset)
        ssql= SQL().Select(f'({csql.text})').As()
        sql=SQL().Select(TableName if not join else SQL().Innerjoin(TableName,*join).text,ColumnName).Where().In(f'{TableName}.id',ssql.text,raw=True)
        print(sql.text)
        async with self.p.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql.text)
                result=await cur.fetchall()
                if dic:result=self.TupleToDic(cur.description,result)
                return result
    @staticmethod
    def TupleToDic(description,valueTupleList):
        description=list(map(lambda x:x[0],description))
        temp=[]
        for i in valueTupleList:
            temp.append(dict(zip(description,i)))
        return temp

class SQL:
    def __init__(self):
        self.text=''
        self.safetext=''
        self.safevalues=[]
    def Select(self,TableName,ColumnName='*'):
        self.text+= f' select {ColumnName if type(ColumnName).__name__=="str" else ",".join(ColumnName)} from {TableName}'
        if ColumnName!='*':
            if type(ColumnName).__name__=='str':ColumnName=f'`{ColumnName}`'
            else:ColumnName=map(lambda x:f'`{x}`',ColumnName)
        self.safetext+=f' select {ColumnName if type(ColumnName).__name__=="str" else ",".join(ColumnName)} from `{TableName}`'
        return self
    def Where(self):
        self.text+=' where'
        self.safetext+=' where'
        return self
    def Eq(self,ColumnName,Value):
        self.text+=f' {ColumnName}={Value}'
        self.safetext+=f' `{ColumnName}`=%s'
        self.safevalues.append(Value)
        return self
    def Neq(self,ColumnName,Value):
        self.text+=f' {ColumnName}!={Value}'
        self.safetext += f' `{ColumnName}`!=%s'
        self.safevalues.append(Value)
        return self
    def In(self,ColumnName,Value,raw=False):
        self.text+=f' {ColumnName} in ({",".join(Value) if not raw else Value})'
        self.safetext += f' `{ColumnName}` in ({",".join(["%s"]*len(Value)) if not raw else Value})'
        self.safevalues+=Value
        return self
    def Notin(self,ColumnName,Value):
        self.text+=f' {ColumnName} not in ({",".join(Value)})'
        self.safetext += f' `{ColumnName}` not in ({",".join(["%s"]*len(Value))})'
        self.safevalues+=Value
        return self
    def Limit(self,limit,offset=0):
        self.text+=f' limit {str(offset)+"," if offset else ""}{limit}'
        if type(limit).__name__!='int' and type(offset).__name__!='int':raise ValueError
        self.safetext+=f' limit {str(offset)+"," if offset else ""}{limit}'
        return self
    def Orderby(self,ColumnName,ASC=True):
        temp='asc' if ASC else 'desc'
        self.text+=f' order by {ColumnName} {temp}'
        self.safetext += f' order by `{ColumnName}` {temp}'
        return self
    def As(self,alias='temp'):
        self.text+=f' as {alias}'
        self.safetext+=f' as `{alias}`'
        return self
    def Innerjoin(self,TableName,JoinTableName,Key,Value):
        self.text+=f' ({TableName} join {JoinTableName} on {Key}={Value})'
        return self