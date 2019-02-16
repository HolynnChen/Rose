import asyncio
import aiohttp
import psutil
import async_timeout
#import configloader as co
#import gb
co={
    'ws_address':'http://127.0.0.1:8123/ftpmanager/ws_keep',
    'ws_confirm':'http://127.0.0.1:8123/ftpmanager/ws_confirm'}
import uuid,hashlib
NAME=hashlib.md5(uuid.UUID(int = uuid.getnode()).hex[-12:].encode()).hexdigest()
APP_KEY='1234567890'
Encrypt=hashlib.sha256((NAME+APP_KEY).encode()).hexdigest()
def expect(data,target):return all([i in data for i in target])
class ftpmanager:
    __ws_tool=None
    def __init__(self):
        return
    async def connect(self):
        connect_session = aiohttp.ClientSession()
        resp=await connect_session.post(co['ws_confirm'],data={'server_id':NAME,'verify':Encrypt})
        result=await resp.json()
        if not result['code']==0:
            print('APP_KEY错误')
            return
        ws = await connect_session.ws_connect(co['ws_address'],heartbeat=30, receive_timeout=60,headers={'cookie':str(resp.cookies).split(':')[1]})
        self.__ws_tool=ws_tool(ws)
        #try:
        print({'uuid':uuid.uuid1().hex,'data':{'msg':'hello'}})
        await ws.send_json({'msg':'hello'})
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.CLOSED:
                await ws.close()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break
            try:
                resp=msg.json()
                if not expect(resp,['data','uuid']):
                    print('服务端发来不支持的信息',resp)
                    continue
                todo=resp['data']
                if not expect(todo,['type','cmd']):
                    print('服务端发来不支持的指令',resp)
                    continue
                if todo['type']=='ftpmanager_tools':
                    if hasattr(ftpmanager_tools,todo['cmd']) and callable(getattr(ftpmanager_tools,todo['cmd'])):
                        await self.__ws_tool.respon(resp['uuid'],getattr(ftpmanager_tools,todo['cmd'])(**(todo.get('data',{}))))
            except:
                continue
        #except asyncio.CancelledError:
        #    print('服务器已离线')
        #    return ws
        #except:
        #    print('服务器意外离线')
        #    return ws
        return

class ws_tool:
    ws_connect=None
    __Queue={}
    def __init__(self,ws):
        self.ws_connect=ws
    async def send(self,json,s=None):
        s=s or uuid.uuid1().hex
        self.__Queue[s]=asyncio.Queue(maxsize=1)
        await self.ws_connect.send_json({'data':json,'uuid':s})
        return s
    async def get(self,s,timeout=5):
        try:
            async with async_timeout.timeout(timeout):
                json=await self.__Queue[s].get()
                return json
        except (asyncio.TimeoutError,asyncio.CancelledError):
            return None
        finally:
            del self.__Queue[s]
    async def respon(self,s,json):
        await self.ws_connect.send_json({'data':json,'uuid':s})

class ftpmanager_tools:
    @staticmethod
    def get_disk_info():
        return {i:psutil.disk_usage(i) for i in [j.device for j in psutil.disk_partitions()]}
temp=ftpmanager()
loop=asyncio.get_event_loop()
loop.run_until_complete(temp.connect())
