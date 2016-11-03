import signal
import sys
import asyncio
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFS
from bs4 import BeautifulSoup

import config
import domain


class MDNAdapter:

    def __init__(self, client, db, fs):
        self.client = client
        self.db = db
        self.fs = fs

    def paginator(self, index):
        return config.site_urls['mdn']

    async def get_url(self, url):
        headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
        async with self.client.get(url, headers=headers) as response:
            if response.status != 200:
                return None
            return await response.read()

    async def get_page(self, index):
        print(self.paginator(index))
        html = await self.get_url(self.paginator(index))
        print('got html')

        soup = BeautifulSoup(html, 'html.parser')

        title = soup(class_='sabai-directory-title') 
        info = soup.find_all(class_='sabai-directory-info')
        category = soup.find_all(class_='sabai-directory-category')
        photos = soup.find_all(class_='sabai-directory-photos')
        
        print('extracting')

        for k in range(len(title)):
            profile = domain.Profile('mdn')

            profile.profile = title[k].a['href']
            profile.name = title[k].a['title']
            try:
                profile.location = info[k](class_='sabai-directory-location')[0].span.text
            except:
                pass
            try:
                profile.number = info[k](class_='sabai-directory-contact-tel')[0].span.text
            except:
                pass
            try:
                profile.email = info[k](class_='sabai-directory-contact-email')[0].a.text
            except:
                pass
            try:
                profile.website = info[k](class_='sabai-directory-contact-website')[0].a['href']
            except:
                pass
            try:
                profile.add_image_url(photos[k].a.img['src'])
            except:
                pass

            await profile.store(self.client, self.fs, self.db)

    def get_site(self, loop):
        for k in range(1):
            print('creating task')
            loop.create_task(self.get_page(k))


def signal_handler(signal, frame):
    client.close()
    db_client.close()
    loop.stop()
    sys.exit(0)

loop = asyncio.get_event_loop()
client = aiohttp.ClientSession(loop=loop)

print('setting up db client')
db_client = AsyncIOMotorClient(config.mongo_url)
db = db_client[config.database]
fs = AsyncIOMotorGridFS(db)

print('setting up signal handler')
signal.signal(signal.SIGINT, signal_handler)

adapter = MDNAdapter(client, db, fs)
adapter.get_site(loop)

loop.run_forever()