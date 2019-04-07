import asyncio
import async_timeout
globalfunc=[]
var={'await':[],'Timer':asyncio.Queue()}
ws=None
def add(func):
    globalfunc.append(func)

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

def Timer_add(func,time):var['Timer'].put_nowait((func,time))

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