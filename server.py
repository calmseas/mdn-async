import asyncio
import aiohttp
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFS
import config
import json
import hmac_auth
from bson import ObjectId
import io


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

encoder = JSONEncoder()

async def auth_factory(app, handler):
    async def check_auth(request):
        if await auth.check_auth(db, request):
            return await handler(request)
        return await handler(request)
        #return web.Response(content_type='application/json', body=bytes(json.dumps({'401':'Not Authorised'}),'utf-8'), status=401)
    return check_auth

async def profile_search(request):
    profiles = []
    if 'page' in request.GET and 'size' in request.GET:
        page = int(request.GET['page'])
        size = int(request.GET['size'])
        async for profile in db.profile.find().limit(size).skip(page*size):
            profiles.append(profile)
    else:
        async for profile in db.profile.find():
            profiles.append(profile)

    headers = {
        'Content-Type': 'application/json'
    }

    doc = {'total': len(profiles), 'profiles': profiles}

    return web.Response(headers=headers, body=bytes(encoder.encode(doc), 'utf-8'))

async def thumbnail(request):
    filename = request.match_info['filename']
    print('retrieving image with id: %s' % filename)
    
    if not await fs.exists({'filename': filename}):
        return web.Response(content_type='application/json', body=bytes(json.dumps({'404':'File Not Found'}),'utf-8'), status=404)

    gridout = await fs.find_one({'filename': filename})

    headers = {
        'Content-Type': gridout.content_type
    }
    return web.Response(headers=headers, body=await gridout.read())

app = web.Application(middlewares=[auth_factory])
app.router.add_route('GET', '/v1/profiles.json', profile_search)

app.router.add_route('GET', '/v1/images/thumbnails/{filename}', thumbnail)


"""
app.router.add_route('GET', '/v1/profiles/get.json', hello)
app.router.add_route('GET', '/v1/profiles/s/{site}/p/{phone}/search.json', hello)
"""

db_client = AsyncIOMotorClient(config.mongo_url)
db = db_client[config.database]
fs = AsyncIOMotorGridFS(db)

auth = hmac_auth.HMACMongoAuth()

loop = asyncio.get_event_loop()
handler = app.make_handler()
f = loop.create_server(handler, '0.0.0.0', 8080)
srv = loop.run_until_complete(f)
print('serving on', srv.sockets[0].getsockname())

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.run_until_complete(handler.finish_connections(1.0))
    loop.run_until_complete(app.finish())
loop.close()
db_client.close()