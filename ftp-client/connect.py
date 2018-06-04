import aiohttp
import configloader as co
import gb
import asyncio
#co={'ws_address':'http://127.0.0.1:8080/ws','name':'test'}
connect_session=None
async def connect():
    global connect_session
    connect_session = aiohttp.ClientSession()
    ws = await connect_session.ws_connect(co.config['ws_address'],heartbeat=30, receive_timeout=60)
    gb.ws=ws
    await ws.send_json({'command': 'info', 'name': co.config['name']})
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
        json = msg.json()
        args=[]
        mod_name=json['mod_name']
        func_name=json['command']
        if 'args' in json:args=json['args']
        for i in gb.globalfunc:
            if mod_name == i.__class__.__name__:
                respone=getattr(i,func_name)(*args)
                data={'command':'response','data':respone}
                if 'identify_string' in json:
                    data['identify_string']=json['identify_string']
                print(data)
                await ws.send_json(data)
                break
    return



