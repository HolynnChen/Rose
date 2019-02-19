from rose import configloader,web
import asyncio
if __name__ == '__main__':
    configloader.init()
    web.server_start(devmode=False)