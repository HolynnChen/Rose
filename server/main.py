from rose import configloader,web
if __name__ == '__main__':
    configloader.init()
    web.server_start()