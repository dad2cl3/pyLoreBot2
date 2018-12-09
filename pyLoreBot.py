import aiohttp, asyncio, boto3, discord, json, math
import manifest, search, setup

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

reload_index = False


# verify bot setup prior to doing any other work.
setup.main()


async def server_change(action, server_name):
    print('Server change occurred...')

    webhook_url = config['admin']['webhook']
    headers = {
        'Content-Type': 'application/json'
    }

    msg = {
        'content': config['admin'][action].format(server_name)
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=webhook_url,
            headers=headers,
            data=json.dumps(msg)
        ) as response:
            if response.status == 200:
                print('Server change sent...')
            else:
                print(response.status)


async def check_manifest():
    await client.wait_until_ready()

    while not client.is_closed:
        print('Check for new manifest...')
        global reload_index

        manifest_metadata = manifest.compare_manifest_versions()

        for game_version in manifest_metadata:
            if manifest_metadata[game_version]['new']:
                reload_index = manifest.download_manifest(game_version, manifest_metadata)

        if reload_index:
            print('Reloading index to reflect current manifest data...')
            success = manifest.load_manifest(manifest_metadata)

            if success:
                for game_version in manifest_metadata:
                    if 'new' in manifest_metadata[game_version]:
                        del manifest_metadata[game_version]['new']

                with open('data/manifest_versions.json', 'w') as local:
                    local.seek(0)
                    local.truncate()
                    local.write(json.dumps(manifest_metadata))
                reload_index = False
        else:
            print('Index contains current manifest data...')

        await asyncio.sleep(config['refresh_interval'])


def build_embed(lore_entry):

    #print(lore_entry['item_name'])
    #print(lore_entry['item_description'])

    lore_embed = discord.Embed(
        title=lore_entry['name'],
        description=lore_entry['subtitle']
    )

    # add footer if present in bot configuration
    if 'footer' in config:
        lore_embed.set_footer(
            icon_url=config['footer']['icon_url'],
            text='{0} - API Time: {1}'.format(config['footer']['text'], lore_entry['duration'])
        )

    lore_description = lore_entry['description']

    #lore_description = scrub(lore_description)

    print('{0} - {1}'.format(lore_entry['name'], len(lore_description)))

    if len(lore_description) < 6000:
        if len(lore_description) > 1024:
            # calculate number of fields
            fields = math.ceil(len(lore_description)/1024)

            for i in range(0,fields):
                # get description chunk
                chunk_start = 1024 * i

                if i < (fields - 1):
                    # not last chunk
                    chunk_end = 1024 * (i + 1)
                else:
                    # last chunk
                    chunk_end = len(lore_description)

                chunk_description = lore_description[chunk_start:chunk_end]

                if i == 0:
                    embed_name = 'Lore'
                else:
                    embed_name = "Lore (cont'd)"

                lore_embed.add_field(
                    name = embed_name,
                    value = chunk_description
                )
        elif len(lore_description) < 1024 and len(lore_description) > 0:
            lore_embed.add_field(
                name='Lore',
                value=lore_description
            )

        lore_embed.set_thumbnail(
            url=lore_entry['icon']
        )

        # measure embed
        embed_length = len(json.dumps(lore_embed.to_dict()))
        print('Embed length: {0}'.format(embed_length))
    else:
        lore_embed = {}

    return lore_embed


def log_metadata(metadata):
    print('Logging request/response metadata...')

    try:
        response = sqs_client.send_message(
            QueueUrl=config['aws']['sqs_url'],
            MessageBody=json.dumps(metadata)
        )
        print(response)
        return response
    except:
        print('Unable to publish the message metadata...')
        return {}


client = discord.Client()
sqs_client = boto3.client('sqs')


@client.event
async def on_ready():
    print('Bot ready...')

@client.event
async def on_message(message):
    #print('Message sent...')
    global reload_index

    if message.content.startswith(config['command_prefix']):
        if not reload_index:
            # log the message metadata
            print('Message received...')

            lore_search = str(message.content).replace('{0} '.format(config['command_prefix']), '')
            search_results = search.main(lore_search)
            lore = search_results['results']
            # print(lore) # debugging

            # request metadata
            # if message.server != None:

            metadata = {
                'id': message.id,
                'payload': str(message.content),
                'server_id': message.server.id,
                'server_name': str(message.server),
                'sender_id': message.author.id,
                'sender_name': str(message.author),
                'channel_id': message.channel.id,
                'channel_name': str(message.channel),
                'timestamp': str(message.timestamp),
                'lore': search_results
            }
            # print(json.dumps(metadata, indent=4)) # debugging
            logging_response = log_metadata(metadata)
            print(logging_response)

            if len(lore) > 0:
                for lore_entry in lore:

                    lore_entry['duration'] = search_results['duration']
                    lore_embed = build_embed(lore_entry)

                    if lore_embed == {}:
                        print('Description length is too long...')
                    else:
                        await client.send_message(message.channel, content='`!lore {0}`'.format(lore_search), embed=lore_embed)

            else:
                troll = config['troll']
                troll['duration'] = search_results['duration']
                troll_embed = build_embed(troll)

                await client.send_message(message.channel, content='`{0} {1}`'.format(config['command_prefix'], lore_search), embed=troll_embed)
        else:
            print('Reloading index...')
            await client.send_message(message.channel, content='LoreBot is reloading. Please try your request in a few minutes.')

@client.event
async def on_server_join(server):
    print('Joined server...')

    await server_change('join', str(server))


@client.event
async def on_server_remove(server):
    print('Departed server...')

    await server_change('leave', str(server))

client.loop.create_task(check_manifest())
client.run(config['discord_token'])