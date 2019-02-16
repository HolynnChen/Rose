import asyncio
import aiohttp
#import configloader as co
#import gb
co={
    'ws_address':'http://127.0.0.1:8123/ftpmanager/ws_keep',
    'ws_confirm':'http://127.0.0.1:8123/ftpmanager/ws_confirm'}
import uuid,hashlib
NAME=hashlib.md5(uuid.UUID(int = uuid.getnode()).hex[-12:].encode()).hexdigest()
APP_KEY='1234567890'
Encrypt=hashlib.sha256((NAME+APP_KEY).encode()).hexdigest()

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
                msg.json()
            except:
                continue
        return
temp=ftpmanager()
loop=asyncio.get_event_loop()
loop.run_until_complete(temp.connect())
