from rose import gb
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler
from rose import configloader as co
import asyncio
import os,importlib,sys

class hot_reload(RegexMatchingEventHandler):
    def __init__(self,regs=[r".*.py"]):
        RegexMatchingEventHandler.__init__(self,regexes=regs)
        self.reload_set=set()
    def on_modified(self, event):
        if event.src_path in self.reload_set:return
        print("file modified:{0}".format(event.src_path))
        self.reload_set.add(event.src_path)
    def reload_module(self):
        temp_set=set()
        mapp=gb.var['global_route'].mapping
        for i in self.reload_set:
            the_path=os.path.abspath(i)
            for j in mapp:
                if the_path.startswith(mapp[j]):
                    temp_set.add(j)
                    break
        if not len(temp_set):return
        print(f'已清除，准备热加载')
        for i in temp_set:
            gb.var['global_route'].delClass(i)
            if f'plugins.{i}' not in sys.modules:
                print(f'热加载{i}发生意外')
                return
            print(f'热加载{i}中')
            importlib.reload(sys.modules[f'plugins.{i}'])
        gb.var['app_loop'].call_soon_threadsafe(gb.var['app_loop'].stop)
        print(f'热加载完毕，重启应用中')
        pass
async def obs():
    observer = Observer()
    event_handler = hot_reload()
    observer.schedule(event_handler, './plugins', True)
    print('启用热加载')
    observer.start()
    try:
        while True: 
            await asyncio.sleep(1)
            if len(event_handler.reload_set):
                event_handler.reload_module()
                event_handler.reload_set.clear()
    except KeyboardInterrupt:
        observer.stop() 
    observer.join()
gb.put_work(obs)
