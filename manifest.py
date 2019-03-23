import json, os, requests, sqlite3, sys, time, zipfile
from whoosh import index, writing
import scrubber

# open configuration file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)


def get_manifest_metadata(url):
    print('Getting manifest metadata...')

    headers = {
        'X-API-Key': config['manifest']['api_key']
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        metadata = response.json()

    version = {
        'version': metadata['Response']['version'],
        'path': 'https://www.bungie.net{0}'.format(metadata['Response']['mobileWorldContentPaths']['en'])
    }

    return version


def download_manifest(game_version, metadata):
    print('Download {0} manifest...'.format(game_version.title()))

    try:
        # download the file and write it to /tmp
        file_name = '/tmp/{0}-compressed-manifest'.format(game_version)

        response = requests.get(metadata[game_version]['path'])

        with open(file_name, 'wb') as zip_file:
            zip_file.write(response.content)

        # extract the file contents and rename the extracted file
        with zipfile.ZipFile(file_name) as zip_file:
            name = zip_file.namelist()
            zip_file.extractall()

        os.rename(name[0], 'data/{0}-manifest.content'.format(game_version))

        return True
    except:
        return False


def compare_manifest_versions():
    print('Comparing manifest versions...')

    # get local version history
    with open('data/manifest_versions.json', 'r') as local:
        local_version_history = json.load(local)

    version_metadata = {}

    for game_version in config['manifest']['metadata']:
        url = config['manifest']['metadata'][game_version]['url']
        version_metadata[game_version] = get_manifest_metadata(url)

    for game_version in local_version_history:
        if local_version_history[game_version] != version_metadata[game_version]:
            version_metadata[game_version]['new'] = True
        else:
            version_metadata[game_version]['new'] = False

    return version_metadata


def load_grimoire(game_version):
    print('Loading grimoire data...')

    # connect to the manifest
    print('Connecting to data/{0}-manifest.content'.format(game_version))
    conn = sqlite3.connect('data/{0}-manifest.content'.format(game_version))
    cur = conn.cursor()

    cards = []

    # get the grimoire cards
    cur.execute('SELECT json FROM {0}'.format('DestinyGrimoireCardDefinition'))
    items = cur.fetchall()
    # disconnect from the manifest
    conn.close()

    for item in items:
        card_json = json.loads(item[0])

        card = {
            'source': 'grimoire',
            'id': card_json['cardId'],
            'name': scrubber.scrub(card_json['cardName']),
            'icon': 'https://www.bungie.net{0}'.format(card_json['highResolution']['image']['sheetPath']),
            'image': 'https://www.bungie.net{0}'.format(card_json['highResolution']['image']['sheetPath'])
        }

        if 'cardIntro' in card_json:
            subtitle = scrubber.scrub(card_json['cardIntro'])
            card['subtitle'] = subtitle
        else:
            card['subtitle'] = ''

        if 'cardDescription' in card_json:
            description = scrubber.scrub(card_json['cardDescription'])
            card['description'] = description
        else:
            card['description'] = ''

        '''if 'icon' in card_json:
            icon = scrubber.scrub(card_json['icon'])
            card['icon'] = icon
        else:
            card['icon'] = '''''

        cards.append(card)

    print('Grimoire found: {0}'.format(len(cards)))

    # open index
    ix = index.open_dir('indices', indexname='lore')
    writer = ix.writer()

    documents = 0
    for card in cards:
        writer.add_document(
            game='destiny',
            source=card['source'],
            id=u'{0}'.format(card['id']),
            name=card['name'],
            subtitle=card['subtitle'],
            description=card['description'],
            icon=card['icon'],
            image=card['image']
        )

        documents += 1

    writer.commit()
    print('Documents loaded: {0}'.format(documents))


def load_inventory(game_version):
    print('Loading inventory data into the index...')

    # open database connection
    print('Connecting to data/{0}-manifest.content'.format(game_version))
    conn = sqlite3.connect('data/{0}-manifest.content'.format(game_version))
    cur = conn.cursor()
    # get inventory item data
    sql = 'SELECT json FROM {0}'.format('DestinyInventoryItemDefinition')
    cur.execute(sql)
    raw_items = cur.fetchall()
    # get lore data
    sql = 'SELECT json FROM {0}'.format('DestinyLoreDefinition')
    cur.execute(sql)
    raw_lore = cur.fetchall()
    # disconnect from the manifest
    conn.close()

    # build inventory metadata
    items = {}
    for raw_item in raw_items:
        item_json = json.loads(raw_item[0])

        item = {}

        if 'loreHash' in item_json:
            if 'screenshot' in item_json:
                screenshot_url = 'https://www.bungie.net{0}'.format(item_json['screenshot'])
            else:
                screenshot_url = ''

            item = {
                'source': 'inventory',
                'id': item_json['hash'],
                'name': item_json['displayProperties']['name'],
                'description': item_json['displayProperties']['description'],
                'icon': 'https://www.bungie.net{0}'.format(item_json['displayProperties']['icon']),
                'image': screenshot_url,
                'lore_hash': item_json['loreHash']
            }

            # print(item)
            items[item_json['hash']] = item

    # build lore metadata
    lore = {}
    for raw_entry in raw_lore:
        lore_json = json.loads(raw_entry[0])

        if 'description' in lore_json['displayProperties']:
            lore_description = lore_json['displayProperties']['description']
        else:
            lore_description = ''

        if 'subtitle' in lore_json:
            lore_subtitle = lore_json['subtitle']
        else:
            lore_subtitle = ''

        entry = {}

        entry = {
            'name': lore_json['displayProperties']['name'],
            'subtitle': lore_subtitle,
            'description': lore_description
        }

        lore[lore_json['hash']] = entry

    # find lore for inventory items
    combined_items = []
    for item in items:
        lore_hash = items[item]['lore_hash']
        lore_details = lore[lore_hash]

        combined_item = {
            'source': 'inventory',
            'id': u'{0}'.format(items[item]['id']),
            'name': lore_details['name'],
            'subtitle': lore_details['subtitle'],
            'description': lore_details['description'],
            'icon': items[item]['icon'],
            'image': items[item]['image']
        }

        combined_items.append(combined_item)

    print('Inventory lore found: {0}'.format(len(combined_items)))

    # open index
    ix = index.open_dir('indices', indexname='lore')
    writer = ix.writer()

    documents = 0
    for item in combined_items:
        writer.add_document(
            game='destiny2',
            source=item['source'],
            id=u'{0}'.format(item['id']),
            name=item['name'],
            subtitle=item['subtitle'],
            description=item['description'],
            icon=item['icon'],
            image=item['image']
        )

        documents += 1

    writer.commit()
    print('Documents loaded: {0}'.format(documents))


def load_records(game_version):
    print('Loading records data into the index...')

    # open database connection
    print('Connecting to data/{0}-manifest.content'.format(game_version))
    conn = sqlite3.connect('data/{0}-manifest.content'.format(game_version))
    cur = conn.cursor()
    # get records data
    sql = 'SELECT json FROM {0}'.format('DestinyRecordDefinition')
    cur.execute(sql)
    raw_items = cur.fetchall()
    # get lore data
    sql = 'SELECT json FROM {0}'.format('DestinyLoreDefinition')
    cur.execute(sql)
    raw_lore = cur.fetchall()
    # disconnect from the manifest
    conn.close()

    # build records metadata
    items = {}
    for raw_item in raw_items:
        item_json = json.loads(raw_item[0])

        item = {}

        if 'loreHash' in item_json:
            if 'screenshot' in item_json:
                screenshot_url = 'https://www.bungie.net{0}'.format(item_json['screenshot'])
            else:
                screenshot_url = ''

            item = {
                'type': 'inventory',
                'id': item_json['hash'],
                'name': item_json['displayProperties']['name'],
                'description': item_json['displayProperties']['description'],
                'icon': 'https://www.bungie.net{0}'.format(item_json['displayProperties']['icon']),
                'image': screenshot_url,
                'lore_hash': item_json['loreHash']
            }

            # print(item)
            items[item_json['hash']] = item

    # build lore metadata
    lore = {}
    for raw_entry in raw_lore:
        lore_json = json.loads(raw_entry[0])

        if 'description' in lore_json['displayProperties']:
            lore_description = lore_json['displayProperties']['description']
        else:
            lore_description = ''

        if 'subtitle' in lore_json:
            lore_subtitle = lore_json['subtitle']
        else:
            lore_subtitle = ''

        entry = {
            'name': lore_json['displayProperties']['name'],
            'subtitle': lore_subtitle,
            'description': lore_description
        }

        lore[lore_json['hash']] = entry

    # find lore for inventory items
    combined_items = []
    for item in items:
        lore_hash = items[item]['lore_hash']
        lore_details = lore[lore_hash]

        combined_item = {
            'source': 'records',
            'id': u'{0}'.format(items[item]['id']),
            'name': lore_details['name'],
            'subtitle': lore_details['subtitle'],
            'description': lore_details['description'],
            'icon': items[item]['icon'],
            'image': items[item]['image']
        }

        combined_items.append(combined_item)

    print('Records lore found: {0}'.format(len(combined_items)))

    # open index
    ix = index.open_dir('indices', indexname='lore')
    writer = ix.writer()

    documents = 0
    for item in combined_items:
        writer.add_document(
            game='destiny2',
            source=item['source'],
            id=u'{0}'.format(item['id']),
            name=item['name'],
            subtitle=item['subtitle'],
            description=item['description'],
            icon=item['icon'],
            image=item['image']
        )

        documents += 1

    writer.commit()
    print('Documents loaded: {0}'.format(documents))


def load_manifest(manifest_metadata):
    print('Loading manifest data into the index...')

    ix = index.open_dir('indices', indexname='lore')

    #doc_writer.commit(mergetype=writing.CLEAR)

    try:
        for game_version in manifest_metadata:
            if game_version == 'destiny':
                doc_writer = ix.writer()

                # purge existing documents based on type
                # doc_writer.delete_by_term(fieldname='type', text='grimoire')
                doc_writer.delete_by_term(fieldname='source', text='grimoire')
                doc_writer.commit()
                print('Purged grimoire documents...')

                # load new data
                start = time.time()
                load_grimoire(game_version)
                end = time.time()
                duration = end - start
                print('Grimoire load time: {0:.2f}s'.format(duration))
            elif game_version == 'destiny2':
                doc_writer = ix.writer()

                # purge existing documents based on type
                # doc_writer.delete_by_term(fieldname='type', text='inventory')
                doc_writer.delete_by_term(fieldname='source', text='inventory')
                doc_writer.commit()
                print('Purged inventory documents...')

                # load new data
                start = time.time()
                load_inventory(game_version)
                end = time.time()
                duration = end - start
                print('Inventory load time: {0:.2f}s'.format(duration))

                doc_writer = ix.writer()

                # purge existing documents based on type
                # doc_writer.delete_by_term(fieldname='type', text='records')
                doc_writer.delete_by_term(fieldname='source', text='records')
                doc_writer.commit()
                print('Purged records documents...')

                # load new data
                start = time.time()
                load_records(game_version)
                end = time.time()
                duration = end - start
                print('Records load time: {0:.2f}s'.format(duration))

        return True
    except:
        print('Exception occurred...')
        print(sys.exc_info()[0])
        return False


'''
manifest_metadata = compare_manifest_versions()
print(manifest_metadata)

reload_index = False
#reload_index = True

for game_version in manifest_metadata:
    if manifest_metadata[game_version]['new']:
        reload_index = True
        download_manifest(game_version, manifest_metadata)

if reload_index:
    print('Reloading index to reflect current manifest data...')
    load_manifest()
'''