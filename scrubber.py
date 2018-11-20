import json

with open ('grimoire_cleanup.json', 'r') as grimoire_cleanup_file:
    cleanup_params = json.load(grimoire_cleanup_file)

def scrub(raw_string):
    for cleanup in cleanup_params['grimoire_cleanup']:
        raw_string = raw_string.replace(cleanup['old'], cleanup['new'])

    return raw_string