import re
import io
import config

google_geocoder_api = 'https://maps.googleapis.com/maps/api/geocode/json'
google_geocoder_api_key = 'AIzaSyBmRIiPc9flJRzh1X99nI3izzF7oTkDBeg'

def normalize_number(number):
    num = number.replace(' ','')
    if (num.startswith('0') and len(num) == 11):
        num = '+44' + num[1:]
    elif (num.startswith('44') and len(num) == 12):
        num = '+' + num
    return num


async def get_geocode(client, location):
    _loc = location

    payload = {'address': _loc, 'key': google_geocoder_api_key}
    async with client.get(google_geocoder_api, params=payload) as response:
        if response.status != 200:
            return None
        res = await response.json()

    if response.status != 200 or res['status'] != 'OK' or len(res['results']) > 1:
        return None

    loc = {}

    loc['formatted_address'] = res['results'][0]['formatted_address']
    loc['lat_long'] = res['results'][0]['geometry']['location']
    for component in res['results'][0]['address_components']:
        if component['types'][0] == 'neighborhood':
            loc['neighborhood'] = component['long_name']
        if component['types'][0] == 'locality':
            loc['locality'] = component['long_name']
        if component['types'][0] == 'country':
            loc['country'] = component['long_name']
        if component['types'][0] == 'postal_code_prefix':
            loc['postcode'] = component['long_name']

    return loc


class Profile:
    def __init__(self, site):
        self.site = site
        self.image_urls = []
        self.images = []
        self.name = None
        self.profile = None
        self.number = None
        self.location = None
        self.website = None
        
    def add_image_url(self, url):
        self.image_urls.append(url)

    def is_valid(self):
        assert self.name
        assert self.profile
        #assert self.number
        assert self.location
        #assert self.website

    async def get_document(self, client):
        number = None
        if self.number is not None:
            number = normalize_number(self.number)

        doc = {
            'site': self.site,
            'name': self.name,
            'profile': self.profile,
            'profkey': self.profile[self.profile.rindex('/')+1:],
            'website': self.website,
            'number': number,
            'location': self.location
        }
        doc['loc_data'] = await get_geocode(client, self.location)
        return doc

    async def store(self, client, fs, db):
        self.is_valid()
        doc = await self.get_document(client)

        existing = await db.profile.find_one({'profile': doc['profile']})

        if existing:
            doc['_id'] = existing['_id']

            # delete existing images
            for image in existing['image_ids']:
                await fs.delete(image)
                
        await self.store_images(client, fs, doc['profkey'])
        doc['image_ids'] = self.images
        await db.profile.save(doc)
        
    async def store_images(self, client, fs, profkey):
        avatar = False
        
        for url in self.image_urls:
            if 'notfound.file.png' in url:
                continue

            filename = url[url.rindex('/')+1:]
            print('filename: %s' % filename)

            async with client.get(url) as response:
                if response.status != 200:
                    continue
                image_bytes = await response.content.read()
                content_type = response.headers['content-type']

            bio = io.BytesIO(image_bytes)
            print('filesize: %d' % len(image_bytes))

            gridin = await fs.new_file()

            # Set metadata attributes.
            await gridin.set('content_type', content_type)
            await gridin.set('filename', filename)
            if self.number is not None:
                await gridin.set('assoc_number', normalize_number(self.number))
            await gridin.write(bio)

            self.images.append(filename)

            await gridin.close()
