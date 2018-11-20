import sys
from whoosh.fields import Schema, ID, TEXT, STORED
from whoosh import index


def main():
    print('Creating lore index...')
    # set the schema for the index
    schema = Schema(
        type=TEXT(stored=True,sortable=True),
        id=ID(stored=True),
        name=TEXT(stored=True,sortable=True),
        subtitle=TEXT(stored=True),
        description=TEXT(stored=True),
        icon=STORED,
        image=STORED
    )

    # create the index for the schema
    try:
        ix = index.create_in('indices', schema, indexname='lore')
        print('Lore index created...')
        return True
    except:
        print('Exception occurred creating index...')
        print(sys.exc_info()[0])
        return False