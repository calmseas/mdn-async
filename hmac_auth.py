import hashlib, binascii, os, hmac, base64, uuid
import json
import asyncio
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFS


def generate_secret():
    dk = hashlib.pbkdf2_hmac('sha256', os.urandom(512), os.urandom(128), 100000)
    return binascii.hexlify(dk)


def generate_api():
    return uuid.uuid4().hex


def sign_message(msg, key):
    dig = hmac.new(key, msg=msg.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


class HMACMongoAuth:

    def __init__(self, key=None):
        self.key = key

    def sign_request(self, verb, url, params=None, body=None, key=None):
        signing = [
            ('verb', verb),
            ('url', url),
            ('params', params),
            ('body', body)
        ]
        #print(json.dumps(signing, indent=1))

        if self.key is not None:
            return sign_message(json.dumps(signing, indent=1), self.key)
        return sign_message(json.dumps(signing, indent=1), key)

    async def check_auth(self, db, request):
        if 'X-Auth' not in request.headers:
            return False

        message_hash = request.headers['X-Auth']

        if 'X-ApiKey' in request.headers:
            api_key = request.headers['X-ApiKey']

        elif 'apiKey' in request.GET:
            api_key = request.GET['apiKey']

        else:
            return False

        api_user = await db.api_users.find_one({'api_key' : api_key})

        if api_user is None:
            return False

        params = [(key,value) for key, value in request.GET.items()]
        url = request.scheme+'://'+request.host+request.path

        server_hash = self.sign_request(request.method,
                                        url,
                                        params=params,
                                        key=api_user['api_secret'])

        print('message hash: %s' % message_hash)
        print('server hash: %s' % server_hash)

        return server_hash == message_hash

    async def create_api_user(self, db, application):
        api_user = await db.api_users.find_one({'application' : application})

        if api_user:
            return api_user

        doc = {'application': application,
               'api_key': generate_api(),
               'api_secret': generate_secret()}

        await db.api_users.insert(doc)

        return doc





