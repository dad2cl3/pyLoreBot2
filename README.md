# Introduction
**Another** Discond bot for searching Destiny and Destiny 2 lore written in Python.

## Dependencies
[Whoosh](https://pypi.org/project/Whoosh/) - Pure Python full text index and search library.

[requests](https://pypi.org/project/requests/) - Well-known Python HTTP requests library.

## Search Capabilities
Whoosh relies upon a user-defined schema that defines how documents are indexed and what is stored within the index and how the index can be searched and sorted. The *lore* schema defines the following fields:
1. **type** - the type of lore contained within the document
2. **id** - unique identifier of the document
3. **name** - name of the document
4. **subtitle** - subtitle of the document if available
5. **description** - description of the document
6. **icon** - icon associated with the document
7. **image** - image or screenshot associated the document (*Note:* not currently returned in the Discord response)

The fields *type* and *name* are sortable within the index and the fields *type*, *name*, *subtitle*, and *description* are stored and searchable.
### Lore Sources

[Bungie.net](https://www.bungie.net) shares publicly a mobile manifest file that contains definitions and metadata for in-game activities, armor, weapons, materials, etc. In the original Destiny game, the lore was stored in grimoire cards which are still present in the Destiny manifest.  The release of Destiny 2 saw Bungie move the lore into the game more tightly. Lore can be found attached to inventory items and accomplishments(or records) within the game.

The bot supports three lore sources:

1. *grimoire* - Lore from the original Destiny game
2. *inventory* - Lore in Destiny 2 associated with inventory items obtainable within the game
3. *records* - Lore in Destiny 2 associated with accomplishments within the game

### Searching
Like all Discord bots, the search is initiated from within Discord by a user who types **!lore**. Anything that follows the command prefix is considered search criteria. The search criteria is parsed by the Whoosh library and the query is executed against the index. Whoosh functions like a search engine and supports a lot of the syntax that Apache Lucene supports. The search capabilities are very comprehensive and the [Whoosh documentation](https://whoosh.readthedocs.io/en/latest/) is outstanding.

Most importantly, the Whoosh library allows a user to isolate the search as desired. By default, a search is performed against all lore sources. However, a user can isolate a search to a specific type of lore. The following command:

```!lore type:grimoire omnigul```

will only search the grimoire lore.

The Whoosh library also supports operators such as AND, NOT, and OR and parentheses for grouping. As a result, a user can be very precise when searching as follows:

```!lore (eris AND ikora) AND NOT (zavala OR asher)```

Search phrases are also supported. Normally the search ```!lore king's fall``` would be parsed to 
```king AND fall``` and any documents that contained both terms would be returned. Instead, a user can search on ```!lore "king's fall"``` and only documents that contain the phrase *king's fall* are returned.

Finally, users can isolate a search based on any of the fields stored in the schema. For example:

```!lore type:grimoire name:"king's fall"```

will return only grimoire lore that contains the phrase *king's fall* in the name field of the document.

## Maintenance Capabilities
Bungie does release updates to the mobile manifest files periodically. As a result, the bot periodically checks to see if a new version of either of the mobile manifest files exists. If one or both files have newer versions, the bot will download, unzip, and rebuild the underlying search index. The frequency of the check can be set in the [bot configuration]().

## Logging
The bot does have one external dependency that can easily be removed. The bot logs metadata for requests to MongoDB through Amazon Simple Queue Service (SQS). Every message to the bot sends a message to the queue. The queue in turn triggers an AWS Lambda function that picks up the message and writes the metadata to MongoDB.