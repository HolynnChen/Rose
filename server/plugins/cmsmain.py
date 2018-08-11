from .cmscore import Cms
import rose.gb as gb
from asyncio import Queue

gb.plugin_table['CMS']={'introduction': 'CMS模块', 'url_enable': True,'url':'cms','version':'1.0.0','name':'cms'}

class cms_service:
    def __init__(self):
        self.cmdcore=Cms()
    def allroute(self):
        temp=self.cmdcore.getcolumn()



class cmd_router:
    def __init__(self):
        return