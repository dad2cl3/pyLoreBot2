import json, os
import index
from jsonschema import validate

with open('setup.json', 'r') as setup_file:
    setup = json.load(setup_file)

with open('manifest_versions.schema', 'r') as manifest_versions_schema:
    schema = json.load(manifest_versions_schema)


def create_local_history_file():
    print('Creating local history file...')

    with open('data/manifest_versions.json', 'w') as versions_file:
        versions_file.write(json.dumps(setup['install']['manifest_versions']))


def main():
    # does the data folder exist?
    if os.path.isdir('data') == False:
        print('Data folder does not exist...')
    # no create along with supporting documents
        print('Creating data folder...')
        os.mkdir('data')

        create_local_history_file()
    else:
        print('Data folder already exists...')
        # does the local version history exist?
        if os.path.isfile('data/manifest_versions.json') == False:
            print('Local history file does not exist...')
            create_local_history_file()
        else:
            # make sure local version history file contains needed structure
            print('Confirming structure of local version history file...')
            # is the file empty?
            if os.stat('data/manifest_versions.json').st_size == 0:
                print('Local history file is empty...')
                create_local_history_file()
            # does the file contain json?
            elif os.stat('data/manifest_versions.json').st_size > 0:
                print('Local history file is not empty...')
                try:
                    with open('data/manifest_versions.json', 'r') as local_history_file:
                        local_history = json.load(local_history_file)

                    validate(local_history, schema)
                except:
                    print('Local history file failed validation...')
                    create_local_history_file()


    # does the indices folder exist?
    if os.path.isdir('indices') == False:
        print('Indices folder does not exist...')
        # no create indices folder
        print('Creating indices folder...')
        os.mkdir('indices')
        print('Creating lore index...')
        index.main()
    else:
        print('Indices folder already exists...')