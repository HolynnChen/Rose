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