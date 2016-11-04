import asyncio
import aiohttp
import hmac_auth
import config
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFS


async def get_url(url):

    auth = hmac_auth.HMACMongoAuth()

    db_client = AsyncIOMotorClient(config.mongo_url)
    db = db_client[config.database]

    api_user = await auth.create_api_user(db, 'mdn')

    print('key: %s' % api_user['api_key'])
    print('secret: %s' % api_user['api_secret'])

    headers = [('Accept', 'application/json')]
    params = [
        ('apiKey', api_user['api_key']),
        ('page', "0"),
        ('size', "10")
    ]

    hash = auth.sign_request('GET', url, params=params, key=api_user['api_secret'])
    print('message hash: %s' % hash)

    headers.append(('X-Auth', hash))
    headers.append(('X-ApiKey', api_user['api_key']))

    async with client.get(url, headers=headers, params=params) as response:
        print(response.headers)
        if response.status != 200:
            print('HTTP status: %s' % response.status)
        res = await response.json()

    print(res['profiles'][0]['profile'])
    print(res['profiles'][9]['profile'])

    headers = [('Accept', 'application/json')]
    params = [
        ('apiKey', api_user['api_key']),
        ('page', "1"),
        ('size', "10")
    ]

    hash = auth.sign_request('GET', url, params=params, key=api_user['api_secret'])
    print('message hash: %s' % hash)

    headers.append(('X-Auth', hash))
    headers.append(('X-ApiKey', api_user['api_key']))

    async with client.get(url, headers=headers, params=params) as response:
        print(response.headers)
        if response.status != 200:
            print('HTTP status: %s' % response.status)
        res = await response.json()

    print(res['profiles'][0]['profile'])
    print(res['profiles'][9]['profile'])

    headers = [('Accept', 'application/json')]
    params = [
        ('apiKey', api_user['api_key']),
        ('page', "0"),
        ('size', "20")
    ]

    hash = auth.sign_request('GET', url, params=params, key=api_user['api_secret'])
    print('message hash: %s' % hash)

    headers.append(('X-Auth', hash))
    headers.append(('X-ApiKey', api_user['api_key']))

    async with client.get(url, headers=headers, params=params) as response:
        print(response.headers)
        if response.status != 200:
            print('HTTP status: %s' % response.status)
        res = await response.json()

    print(res['profiles'][0]['profile'], res['profiles'][0]['name'], res['profiles'][0]['image_ids'])
    print(res['profiles'][9]['profile'], res['profiles'][9]['name'], res['profiles'][9]['image_ids'])
    print(res['profiles'][10]['profile'], res['profiles'][10]['name'], res['profiles'][10]['image_ids'])
    print(res['profiles'][19]['profile'], res['profiles'][19]['name'], res['profiles'][19]['image_ids'])



loop = asyncio.get_event_loop()
client = aiohttp.ClientSession(loop=loop)

loop.run_until_complete(get_url('http://127.0.0.1:8080/v1/profiles.json'))

client.close()

