from .cmscore import Cms
import rose.gb as gb
from aiohttp import web
from pprint import pprint

gb.plugin_table['CMS']={'introduction': 'CMS模块', 'url_enable': True,'url':'cms','version':'1.0.0','name':'cms'}

class cms_service:
    def __init__(self):
        self.cmscore=Cms()
    def allroute(self):
        temp=self.cmscore.getcolumn()



class cms:
    def __init__(self):
        print('running')
        return
    async def hello_get(self,request):
        temp= request.reqDic.get('what')
        return  web.Response(text="hello "+(temp if temp else ''))
    async def saybye_get(self,request):
        return web.Response(text="Bye!")

gb.var['global_route'].add_rewrite_rule(['replace_start','/cms',''])
gb.var['global_route'].addClass(cms)