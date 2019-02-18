import asyncio
import aiohttp
import time
import hashlib
import random
from urllib.parse import quote
from rose import gb
from rose.helper import template
from aiohttp import web

class Translate:
    tkk = '429242.2670508838'#'428194.2961085901'
    base_server = 'https://translate.google.com/'
    base_url = 'translate_a/single?client=webapp&sl=en&tl=zh-CN&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&source=btn&ssel=0&tsel=0&kc=0&tk='
    headers = {
        'refer': base_server,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
    }
    youdao_headers = {
        'Host': 'fanyi.youdao.com',
        'Origin': 'http://fanyi.youdao.com',
        'Referer': 'http://fanyi.youdao.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
    }
    youdao_url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
    base_youdao_data = {'from': 'AUTO', 'to': 'AUTO', 'smartresult': 'dict', 'client': 'fanyideskweb',
                        'doctype': 'json', 'version': '2.1', 'keyfrom': 'fanyi.web', 'action': 'FY_BY_REALTIME',
                        'typoResult': 'false'}

    async def google_translate(self, text):
        url = f'{self.base_server}{self.base_url}{self.tk(text)}&q={quote(text)}'
        async with aiohttp.ClientSession() as session:
            return ''.join(list(map(lambda x: x[0] or '', (await self.base_get(session, url))[0])))

    async def google_translate_list(self, text_list):
        temp = [f'{self.base_server}{self.base_url}{self.tk(text)}&q={quote(text)}' for text in text_list]
        async with aiohttp.ClientSession() as session:
            result, fail = await asyncio.wait([self.base_get(session, temp[i], index=i + 1) for i in range(len(temp))])
            js_result = map(lambda x: x[1], sorted([i.result() for i in result]))
            return [''.join(list(map(lambda x: x[0] or '', k[0]))) for k in js_result]

    async def base_get(self, session, url, index=None, headers=headers):
        async with session.get(url, headers=headers) as resp:
            if index: return [index, await resp.json()]
            return await resp.json()

    async def base_post(self, session, url, data, index=None, headers=youdao_headers):
        async with session.post(url, headers=headers, data=data) as resp:
            if index: return [index, await resp.json()]
            return await resp.json()

    def tk(self, text):
        b = self.tkk if self.tkk != '0' else ''
        d = b.split('.')
        b = int(d[0]) if len(d) > 1 else 0
        e = []
        g = 0
        size = len(text)
        for i, char in enumerate(text):
            l = ord(char)
            if l < 128:
                e.append(l)
            else:
                if l < 2048:
                    e.append(l >> 6 | 192)
                else:
                    if (l & 64512) == 55296 and g + 1 < size and ord(text[g + 1]) & 64512 == 56320:
                        g += 1
                        l = 65536 + ((l & 1023) << 10) + ord(text[g]) & 1023
                        e.append(l >> 18 | 240)
                        e.append(l >> 12 & 63 | 128)
                    else:
                        e.append(l >> 12 | 224)
                    e.append(l >> 6 & 63 | 128)
                e.append(l & 63 | 128)
        a = b
        for i, value in enumerate(e): a = self._xr(a + value, '+-a^+6')
        a = self._xr(a, '+-3^+b+-f')
        a ^= int(d[1]) if len(d) > 1 else 0
        if a < 0: a = (a & 2147483647) + 2147483648
        a %= 1000000
        return '{}.{}'.format(a, a ^ b)

    def _xr(self, a, b):
        size_b = len(b)
        c = 0
        while c < size_b - 2:
            d = b[c + 2]
            d = ord(d[0]) - 87 if 'a' <= d else int(d)
            d = ((a % 0x100000000) >> d) if '+' == b[c + 1] else a << d
            a = a + d & 4294967295 if '+' == b[c] else a ^ d
            c += 3
        return a

    async def youdao_translate(self, text):
        async with aiohttp.ClientSession() as session:
            await session.get('http://fanyi.youdao.com')  # 初始化一个cookie
            temp = await self.base_post(session,self.youdao_url, self.youdao_data(text))
            return self.youdao_combine(temp['translateResult'])

    async def youdao_translate_list(self, text):
        temp = [self.youdao_data(i) for i in text]
        async with aiohttp.ClientSession(cookies={'___rl__test__cookies': int(time.time() * 1000)}) as session:
            await session.get('http://fanyi.youdao.com')  # 初始化一个cookie
            result, fail = await asyncio.wait(
                [self.base_post(session, self.youdao_url, temp[i], index=i + 1) for i in range(len(temp))])
            js_result = map(lambda x: x[1]['translateResult'], sorted([i.result() for i in result]))
            return ['\n'.join([self.youdao_combine(i) for i in k]) for k in js_result]
    def youdao_combine(self,todo):
        if type(todo).__name__=='dict':return todo.get('tgt','')
        return ''.join([self.youdao_combine(i) for i in todo])

    def youdao_data(self, text):
        text = text.lstrip('\ufeff')
        temp_data = {}
        temp_data['i'] = text
        temp_data['salt'] = str(int(time.time() * 1000) + random.randint(1, 10))
        temp_data['sign'] = hashlib.md5(
            ("fanyideskweb" + text + temp_data['salt'] + "p09@Bn{h02_BIEe]$P^nG").encode('utf-8')).hexdigest()
        temp_data = {**self.base_youdao_data, **temp_data}
        return temp_data

class translate:
    def __init__(self):
        print('翻译模块初始化')

    async def default_get(self,request):
        return await self.index_get(request)

    @template('/translate/index.html')
    async def index_get(self,request):
        return

    async def default_post(self,request):
        return await self.index_post(request)

    async def index_post(self,request):
        data = await request.post()
        req=data['data'].split('\n\n')
        return web.json_response({
            'google':await Translate().google_translate_list(req),
            'youdao':await Translate().youdao_translate_list(req)
            })
    async def one_post(self,request):
        data=await request.post()
        req=data['data']
        return web.json_response({
            'google':await Translate().google_translate(req),
            'youdao':await Translate().youdao_translate(req)
            })
gb.addClass(translate)
