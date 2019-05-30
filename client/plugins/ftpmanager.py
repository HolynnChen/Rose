import asyncio,sys
import aiohttp
import psutil
import async_timeout
from threading import Thread
import uuid,hashlib,toml
import sqlite3,os,json,copy
import xml.etree.ElementTree as ET
print('FtpManager初始化中')
co=toml.load(os.path.split(os.path.realpath(__file__))[0]+'\\config.toml')['ftpmanager']
SRC=hashlib.md5(uuid.UUID(int = uuid.getnode()).hex[-12:].encode()).hexdigest()
APP_KEY=co['APP_KEY']
NAME=hashlib.sha256((SRC+APP_KEY).encode()).hexdigest()
var={}
def expect(data,target):return all([i in data for i in target])
class ftpmanager:
    ws_tool=None
    def __init__(self,loop=None):
        self.ftpmanager_tools=ftpmanager_tools(self)
        self._helper=sqlite_heler()
        self.loop=loop or asyncio.get_event_loop()
        self.xml_helper=xml_helper(co['xml_path'],co['exe_path'],self)
        print('FtpManager:已初始化')
        return
    async def connect(self):
        connect_session = aiohttp.ClientSession()
        resp=await connect_session.post(co['ws_confirm'],data={'server_id':NAME,'verify':SRC})
        result=await resp.json()
        if not result['code']==0:
            print('APP_KEY错误')
            return
        ws = await connect_session.ws_connect(co['ws_address'],heartbeat=30, receive_timeout=60,headers={'cookie':str(resp.cookies).split(':')[1]})
        self.ws_tool=ws_tool(ws,loop=loop)
        print('FtpManager:已连接服务器 '+co['ws_confirm'])
        try:
            await self.ws_tool.send({'target':'update_info','parameters':{'server_id':NAME,'disk_info':self.ftpmanager_tools.get_disk_info()}})
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.CLOSED:
                    print('FtpManager:收到关闭信息')
                    await ws.close()
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print('FtpManager:收到异常信息')
                    break
                try:
                    resp=msg.json()
                    if not expect(resp,['data','uuid']):
                        print('FtpManager:服务端发来不支持的信息',resp)
                        continue
                    if expect(resp['data'],['type','cmd']):
                        todo=resp['data']
                        if todo['type']=='ftpmanager_tools':
                            if hasattr(self.ftpmanager_tools,todo['cmd']) and callable(getattr(self.ftpmanager_tools,todo['cmd'])):
                                if asyncio.iscoroutinefunction(getattr(self.ftpmanager_tools,todo['cmd'])):
                                    async def inner():
                                        result=await getattr(self.ftpmanager_tools,todo['cmd'])(**(todo.get('data',{})))
                                        if result:await self.ws_tool.respon(resp['uuid'],result)
                                    asyncio.ensure_future(inner())
                                else:
                                    result=getattr(self.ftpmanager_tools,todo['cmd'])(**(todo.get('data',{})))
                                    if result:await self.ws_tool.respon(resp['uuid'],result)
                    else:
                        self.ws_tool.set(resp['uuid'],resp['data'])
                except:
                    continue
        except asyncio.CancelledError:
           print('FtpManager:服务器已离线')
           return ws
        except:
           print('FtpManager:服务器意外离线')
           return ws
        return

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
            return self._del.pop(key)
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

class ws_tool:
    ws_connect=None
    def __init__(self,ws,loop=None):
        self.ws_connect=ws
        self.msg_dict=async_Dict(loop or asyncio.get_event_loop())
    async def send(self,json,s=None):
        s=s or uuid.uuid1().hex
        await self.ws_connect.send_json({'data':json,'uuid':s})
        return s
    async def get(self,s,timeout=10):
        try:
            async with async_timeout.timeout(timeout):
                json=await self.msg_dict.get(s)
                return json
        except (asyncio.TimeoutError,asyncio.CancelledError):
            self.msg_dict.async_del(s)
            return None
    def set(self,s,v):self.msg_dict.set(s,v)
    async def respon(self,s,json):await self.send(json,s=s)

class ftpmanager_tools:
    def __init__(self,super_class):
        self.super=super_class
    @staticmethod
    def get_disk_info():
        return {i:psutil.disk_usage(i) for i in [j.device for j in psutil.disk_partitions() if j.fstype]}
    
    async def async_operation(self):
        key=await self.super.ws_tool.send({'target':'async_operation','parameters':{'index_id':self.super._helper.get_id('operation')}})
        result=await self.super.ws_tool.get(key)
        if not result or not len(result):return
        for i in result:
            if i['operation']=='user_change':
                self.user_change(i['data'])
                self.super.xml_helper.user_change(i['data'])
            elif i['operation']=='user_remove':
                self.user_remove(i['data'])
                self.super.xml_helper.user_remove(i['data'])
        self.super.xml_helper.apply()
        self.super._helper.update('times',{'index_id':result[-1]['id']},{'name':'operation'})
        print('FtpManager:操作同步 id:'+str(result[-1]['id']))
    
    async def async_dbnotes(self):
        key=await self.super.ws_tool.send({'target':'async_dbnotes','parameters':{'index_id':self.super._helper.get_id('dbnotes'),'server_id':NAME}})
        result=await self.super.ws_tool.get(key)
        if not result or not len(result):return
        for i in result:
            if i['operation']=='dbnote_change':
                self.dbnote_change(i['data'])
                self.super.xml_helper.dbnote_change(i['data'])
            elif i['operation']=='dbnote_remove':
                self.dbnote_remove(i['data'])
                self.super.xml_helper.dbnote_remove(i['data'])
                pass
        self.super.xml_helper.apply()
        self.super._helper.update('times',{'index_id':result[-1]['id']},{'name':'dbnotes'})
        print('FtpManager:标签同步 id:'+str(result[-1]['id']))
    
    async def async_all(self):
        await self.async_dbnotes()
        await self.async_operation()

    def user_change(self,data):
        user_info={i:data['user_info'][i] for i in data['user_info'] if i in ['name','password','mail']}
        if len(user_info)>0:
            if data['user_id']:user_info['user_id']=data['user_id']
            sql="insert or ignore into users("+','.join(user_info)+') values (:'+',:'.join(user_info)+')'
            self.super._helper.insert('users',dicts=user_info,special_sql=sql)
            self.super._helper.update('users',user_info,filter_dict={'user_id':data['user_id']})
        change_dbnote=data['user_dbnote']
        if len(change_dbnote['removeTags'])>0:
            sql="delete from relation where user=:user_id and db_note in (:"+",".join(map(str,range(len(change_dbnote['removeTags']))))+")"
            filter_dict={str(i):change_dbnote['removeTags'][i] for i in range(len(change_dbnote['removeTags']))}
            filter_dict['user_id']=data['user_id']
            self.super._helper.delete('relation',special_sql=sql,filter_dict=filter_dict)
        if len(change_dbnote['addTags'])>0:
            sql="insert into relation (user,db_note) values (:user_id,:db_note)"
            dicts=[{'user_id':data['user_id'],"db_note":i} for i in change_dbnote['addTags']]
            self.super._helper.insert('relation',special_sql=sql,dicts=dicts)
    
    def user_remove(self,data):
        self.super._helper.delete('relation',{'user':data['user_id']})
        self.super._helper.delete('users',{'user_id':data['user_id']})
    
    def dbnote_change(self,data):
        filter_dict={'server_id':data['server_id'],'name':data['name'],'more':{'path':data['path'],'permissions':data['permissions'],'more_config':data['more_config']}}
        if data['id']:filter_dict['id']=data['id']
        sql="insert or replace into db_note("+','.join(filter_dict)+") values(:"+',:'.join(filter_dict)+")"
        self.super._helper.insert('user',filter_dict,special_sql=sql)
    
    def dbnote_remove(self,data):
        self.super._helper.delete('db_note',{'id':data['id']})

class sqlite_heler:
    def __init__(self):
        self._directory,_=os.path.split(os.path.realpath(__file__))
        sqlite3.register_adapter(dict,json.dumps)
        sqlite3.register_converter('dict',json.loads)
        if not os.path.isfile(self._directory+'\\ftpmanager.db'):
            print('FtpManager:数据库文件不存在，尝试创建并初始化')
            self._db=sqlite3.connect(self._directory+'\\ftpmanager.db',check_same_thread=False,detect_types=sqlite3.PARSE_DECLTYPES)
            cursor=self._db.cursor()
            sql_init=[
                'create table users (user_id integer primary key autoincrement not null, name text not null, password text not null, mail text not null)',
                'create table db_note (id integer primary key autoincrement not null, name text not null, server_id text not null, more dict)',
                'create table relation (id integer primary key autoincrement not null, user integer not null, db_note integer not null)',
                'create unique index only on relation (user,db_note)',
                'create table times (name text primary key not null,index_id integer not null)',
                'insert into times (name,index_id) values ("operation",0)',
                'insert into times (name,index_id) values ("dbnotes",0)'
            ]
            for i in sql_init:cursor.execute(i)
            self._db.commit()
            print('FtpManager:数据库初始化完毕')
        else:
            self._db=sqlite3.connect(self._directory+'\\ftpmanager.db',check_same_thread=False,detect_types=sqlite3.PARSE_DECLTYPES)
        print('FtpManager:数据库已连接')
    @staticmethod
    def _warp(data,cursor_description):
        column=[i[0] for i in cursor_description]
        if not data:return None
        if isinstance(data,tuple):
            return dict(zip(column,data))
        else:
            return list(map(lambda x:dict(zip(column,x)),data))
    def search(self,table,filter_dict={},column_filter=None,fetchlimit=0,special_sql=None):
        cursor = self._db.cursor()
        sql = special_sql or f'select {column_filter or "*"} from {table}'
        if len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=:'+i for i in filter_dict.keys()])
        cursor.execute(sql,filter_dict)
        if fetchlimit<0:return self._warp(cursor.fetchall(),cursor.description)
        elif fetchlimit==0:return self._warp(cursor.fetchone(),cursor.description)
        else: return self._warp(cursor.fetchmany(fetchlimit),cursor.description)
    def insert(self,table,dicts,special_sql=None):
        cursor=self._db.cursor()
        if isinstance(dicts,dict):
            sql=special_sql or f'insert into {table} ({",".join(dicts.keys())}) values ({",".join([":"+i for i in dicts.keys()])})'
            cursor.execute(sql,dicts)
        else:
            sql=special_sql or f'insert into {table} ({",".join(dicts[0].keys())}) values ({",".join([":"+i for i in dicts[0].keys()])})'
            cursor.executemany(sql,dicts)
        self._db.commit()
    def update(self,table,value_dict,filter_dict={},special_sql=None):
        cursor = self._db.cursor()
        temp=",".join([i+'=?' for i in value_dict.keys()])
        sql = special_sql or f'update {table} set {temp}'
        if filter_dict and len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=?' for i in filter_dict.keys()])
        cursor.execute(sql,tuple(list(value_dict.values())+list(filter_dict.values())))
        self._db.commit()
    def delete(self,table,filter_dict={},special_sql=None):
        cursor=self._db.cursor()
        sql = special_sql or f'delete from {table}'
        if len(filter_dict) and not special_sql:
            sql+=' where '
            sql+=' and '.join([i+'=:'+i for i in filter_dict.keys()])
        cursor.execute(sql,filter_dict)
        self._db.commit()
    def get_id(self,name):
        cursor=self._db.cursor()
        cursor.execute(f'select index_id from times where name=:name',{'name':name})
        return cursor.fetchone()[0]

class xml_helper:
    ServerBaseDir=co['base_dir']#空文件夹
    BaseXML=f'<FileZillaServer><Groups><Group Name="BaseGroup"><Option Name="Bypass server userlimit">0</Option><Option Name="User Limit">0</Option><Option Name="IP Limit">0</Option><Option Name="Enabled">1</Option><Option Name="Comments"></Option><Option Name="ForceSsl">0</Option><Permissions><Permission Dir="{ServerBaseDir}"></Permission></Permissions></Group></Groups><Users></Users></FileZillaServer>'
    DefaultUser='<User><Option Name="Pass"></Option><Option Name="Group">BaseGroup</Option><Option Name="Bypass server userlimit">0</Option><Option Name="User Limit">0</Option><Option Name="IP Limit">0</Option><Option Name="Enabled">1</Option><Option Name="Comments"></Option><Option Name="ForceSsl">0</Option><Permissions></Permissions></User>'
    ServerBaseDirAttr={'FileRead':0,'FileWrite':0,'FileDelete':0,'FileAppend':0,'DirCreate':0,'DirDelete':0,'DirList':1,'DirSubdirs':1,'IsHome':1}
    baseOptions=['FileRead','FileWrite','FileDelete','FileAppend','DirCreate','DirDelete','DirList','DirSubdirs','IsHome','AutoCreate']
    def __init__(self,xml_path,exe_path,super_class):
        if not os.path.isfile(xml_path):
            self.new_init(xml_path)
        self.xml_path=xml_path
        self.exe_path=exe_path
        self.super=super_class
        self.xml=ET.parse(xml_path)
        self.root=self.xml.getroot()
        self.Users=self.root.find('Users')
    def new_init(self,xml_path):
        base=ET.fromstring(self.BaseXML)
        basePermission=base.find('./Groups/Group/Permissions/Permission')
        for i in self.ServerBaseDirAttr:
            temp=ET.SubElement(basePermission,'Option',{'Name':i})
            temp.text=str(self.ServerBaseDirAttr[i])
        ET.ElementTree(base).write(xml_path,encoding="UTF-8")
        os.system(f'"{self.exe_path}" /reload-config')
        return
    def apply(self):
        self.xml.write(self.xml_path,encoding="UTF-8")
        os.system(f'"{self.exe_path}" /reload-config')
    def user_change(self,data):
        user=self.Users.find('./User[@user_id="'+str(data['user_id'])+'"]')
        if not user:
            user=ET.fromstring(self.DefaultUser)
            user.set('Name',data['user_info']['name'])
            user.set('user_id',str(data['user_id']))
            user.find('./Option[@Name="Pass"]').text=hashlib.md5(data['user_info']['password'].encode()).hexdigest()
            self.Users.append(user)
        user_info={i:data['user_info'][i] for i in data['user_info'] if i in ['name','password']}
        if len(user_info)>0:
            for i in user_info:
                if i=='name':user.set('Name',user_info['name'])
                if i=='password':user.find('./Option[@Name="Pass"]').text=hashlib.md5(user_info['password'].encode()).hexdigest()
        if len(data['user_dbnote']['removeTags'])>0:
            for i in data['user_dbnote']['removeTags']:
                dbnote=user.find(f'./Permissions/Permission[@id="{i}"]')
                if dbnote:user.find('./Permissions').remove(dbnote)
        if len(data['user_dbnote']['addTags'])>0:
            user_permissions=user.find('Permissions')
            result=self.super._helper.search('db_note',special_sql=f'select * from db_note where id in ({",".join(map(str,data["user_dbnote"]["addTags"]))})',fetchlimit=-1)
            for i in result:
                user_permission=ET.SubElement(user_permissions,'Permission',{'Dir':i['more']['path'],'id':str(i['id'])})
                baseOptions=copy.deepcopy(self.baseOptions)
                ET.SubElement(ET.SubElement(user_permission,'Aliases'),'Alias').text='/'+i['name']
                for j in i['more']['permissions']:
                    if j in baseOptions:
                        baseOptions.remove(j)
                        temp=ET.SubElement(user_permission,'Option',{'Name':j})
                        temp.text='1'
                for j in baseOptions:
                    temp=ET.SubElement(user_permission,'Option',{'Name':j})
                    temp.text='0'
    def user_remove(self,data):
        user=self.Users.find('./User[@user_id='+str(data['user_id'])+']')
        if user:self.Users.remove(user)
    def dbnote_change(self,data):
        if not data['id']:return
        permissions=self.Users.findall('.//Permission[@id="'+str(data['id'])+'"]')
        baseOptions=copy.deepcopy(self.baseOptions)
        if not permissions:return
        for i in data['permissions']:baseOptions.remove(i)
        for i in permissions:
            i.set('Dir',data['path'])
            for j in data['permissions']:
                temp=i.find('Option[@Name="'+j+'"]')
                temp.text='1'
            for j in baseOptions:
                temp=i.find('Option[@Name="'+j+'"]')
                temp.text='0'
            i.find('.//Alias').text='/'+data['name']
    def dbnote_remove(self,data):
        users=self.Users.findall('.//Permission[@id="'+str(data['id'])+'"]/..')
        for i in users:
            users.find('./Permissions').remove(i.find('./Permission[@id="'+str(data['id'])+'"]/..'))
async def Timer():
    loop=asyncio.get_event_loop()
    while True:
        try:
            async with async_timeout.timeout(1):
                func,time = await var['Timer'].get()
                loop.call_later(time,Timer_add,func,time)
                if asyncio.iscoroutinefunction(func):
                    loop.call_later(time,asyncio.ensure_future,func)
                else:
                    loop.call_later(time,func)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            continue

async def init():
    await ftpmanager().connect()

def Timer_add(func,time):var['Timer'].put_nowait((func,time))
def keep_Timer():
    loop = asyncio.new_event_loop()
    var['Timer'] = asyncio.Queue(loop=loop)
    loop.run_until_complete(Timer())

Thread(target=keep_Timer).start()
loop=None
if sys.platform=="win32":
    loop=asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop=asyncio.get_event_loop()
temp=ftpmanager(loop=loop)
loop.run_until_complete(temp.connect())
