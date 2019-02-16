import asyncio
import aiohttp
import psutil
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
        await ws.send_json({'msg':'hello'})
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.CLOSED:
                await ws.close()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break
            try:
                resp=msg.json()
                if not expect(resp,['type','cmd','data']):
                    print('服务端发来不支持的信息',resp)
                    break
                if resp['type']=='ftpmanager_tools':
                    if hasattr(ftpmanager_tools,resp['cmd']) and callable(getattr(ftpmanager_tools,resp['cmd'])):
                        break
            except:
                continue
        return

class ftpmanager_tools:
    @staticmethod
    def get_disk_info():
        return {i:psutil.disk_usage(i) for i in [j.device for j in psutil.disk_partitions()]}
temp=ftpmanager()
loop=asyncio.get_event_loop()
loop.run_until_complete(temp.connect())
