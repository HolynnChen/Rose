from aiohttp.abc import AbstractView
import functools
import warnings
import asyncio,aiohttp_jinja2
from aiohttp import web

async def render_string(template_name, request, context, *, app_key=aiohttp_jinja2.APP_KEY):
    env = request.app.get(app_key)
    if request.get(aiohttp_jinja2.REQUEST_CONTEXT_KEY):
        context = dict(request[aiohttp_jinja2.REQUEST_CONTEXT_KEY], **context)
    return await env.get_template(template_name).render_async(context)


async def render_template(template_name, request, context, *, app_key=aiohttp_jinja2.APP_KEY, encoding='utf-8',
                          status=200):
    response = web.Response(status=status)
    if context is None:
        context = {}
    text = await render_string(template_name, request, context, app_key=app_key)
    response.content_type = 'text/html'
    response.charset = encoding
    response.text = text
    return response


def template(template_name, *, app_key=aiohttp_jinja2.APP_KEY, encoding='utf-8', status=200):
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args):
            if asyncio.iscoroutinefunction(func):
                coro = func
            else:
                warnings.warn("Bare functions are deprecated, "
                              "use async ones", DeprecationWarning)
                coro = asyncio.coroutine(func)
            context = await coro(*args)
            if isinstance(context, web.StreamResponse): return context
            if isinstance(args[0], AbstractView):
                request = args[0].request
            else:
                request = args[-1]
            response = await render_template(template_name, request, context, app_key=app_key,
                                             encoding=encoding)  # change
            response.set_status(status)
            return response

        return wrapped

    return wrapper