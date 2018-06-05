import asyncio
import connect
import configloader
import connect_mysql
import os
import gb
for root, dirs, files in os.walk('plugins'):
    for i in files:
        if not i=='__init__.py':__import__('plugins.'+i.split('.')[0])
configloader.init()
connect_mysql.init()
loop=asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([connect.connect()]))