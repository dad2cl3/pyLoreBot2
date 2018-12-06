# Introduction
**Another** Discord bot for searching Destiny and Destiny 2 lore written in Python which can be invited using this [link]().

## Dependencies
[Whoosh](https://pypi.org/project/Whoosh/) - Pure Python full text index and search library. Whoosh functions like a search engine and the search capabilities are very comprehensive. The [Whoosh documentation](https://whoosh.readthedocs.io/en/latest/) is outstanding.

[requests](https://pypi.org/project/requests/) - Well-known Python HTTP requests library.

[jsonschema](https://pypi.org/project/jsonschema/) - Python JSON schema library

## Search Capabilities
Whoosh relies upon a user-defined schema that defines how documents are indexed, what is stored within the index, and how the index can be searched and sorted. The *lore* schema defines the following fields:
1. **game** - the version of the game manifest
2. **source** - the source of lore contained within the document
3. **id** - unique identifier of the document
4. **name** - name of the document
5. **subtitle** - subtitle of the document if available
6. **description** - description of the document
7. **icon** - icon associated with the document
8. **image** - image or screenshot associated with the document (*Note:* not currently returned in the Discord response)

The fields *source* and *name* are sortable within the index and the fields *source*, *name*, *subtitle*, and *description* are stored and searchable.
### Game Versions
There are currently two versions of the game stored in the index: *destiny* and *destiny2*. The values can be used to limit the search results. More on that later.
### Lore Sources
[Bungie.net](https://www.bungie.net) shares publicly a mobile manifest file that contains definitions and metadata for in-game activities, armor, weapons, materials, etc. In the original Destiny game, the lore was stored in grimoire cards which are still present in the Destiny manifest.  The release of Destiny 2 saw Bungie move the lore into the game more tightly. Lore can be found attached to inventory items and accomplishments(or records) within the game.


The bot supports three sources of lore:

1. *grimoire* - Lore from the original Destiny game
2. *inventory* - Lore in Destiny 2 associated with inventory items obtainable within the game
3. *records* - Lore in Destiny 2 associated with accomplishments within the game

### Searching
Like all Discord bots, the search is initiated from within Discord by a user who types **!lore**. Anything that follows the command prefix is considered search criteria. The search criteria is parsed by the Whoosh library and the query is executed against the index.

Most importantly, the Whoosh library allows a user to isolate a search as much, or as little, as desired. By default, a search is performed against all lore sources. However, a user can isolate a search to a specific source of lore. The following command:

```!lore source:grimoire omnigul```

will only search the grimoire lore.

The Whoosh library also supports operators such as AND, NOT, and OR and parentheses for grouping. As a result, a user can be very precise when searching as follows:

```!lore (eris AND ikora) AND NOT (zavala OR asher)```

Search phrases are also supported. By default, the search ```!lore king's fall``` is parsed to 
```king AND fall``` and any documents that contain both terms are returned. To be more precise, a user can search on ```!lore "king's fall"``` and only documents that contain the phrase *king's fall* are returned.

Currently, two types of wildcard searches are supported. The _?_ wildcard operator allows a user to perform searches where a single character can vary within the search criteria. For example, the search ```!lore h?ve``` will return all documents that contain the words _have_ and _hive_. The _*_ wildcard operator allows a user to perform searches where multiple characters can vary within the search criteria. For example, the search ```!lore h*e``` will return all documents that contain the words _have_ and _hive_ as well as _here_ and _heave_ if those words were found within the document index.

Finally, users can isolate a search based on any of the fields stored in the schema. For example:

```!lore source:grimoire name:"king's fall"```

will return only grimoire lore that contains the phrase *king's fall* in the name field of the document. As mentioned earlier, a user can limit the search to game versions in a similar fashion:

```!lore game:destiny2 source:records forge```

will return only Destiny 2 lore found in the lore associated with records achievable in game where the term forge exists. Limiting the game version to *destiny* is redundant with setting the source of the lore to *grimoire* since only one source of lore exists within the original version of the game's manifest. The additional grouping is really only useful for Destiny 2 where there are multiple sources of lore within the Destiny 2 manifest.

## Maintenance Capabilities
Bungie does release updates to the mobile manifest files periodically. As a result, the bot periodically checks to see if a new version of either of the mobile manifest files exists. If one or both files have newer versions, the bot will download, unzip, and rebuild the underlying search index. The frequency of the check can be set in the [bot configuration](https://github.com/dad2cl3/pyLoreBot2/blob/master/sample-config.json).

The setup of the bot is pretty flexible. Customized settings of the directory structure for storing the manifest data and index, and the naming of the manifest files and index itself can be set in the configuration file.

## Logging
The bot does have one external dependency that can easily be removed or altered. The bot logs metadata for requests to MongoDB through Amazon Simple Queue Service (SQS) and AWS Lambda. Every message to the bot put a message on the queue. The queue in turn triggers a Lambda function that picks up the message and writes the metadata to MongoDB.