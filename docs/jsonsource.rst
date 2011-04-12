``collective.blueprint.jsonmigrator.source``
============================================

Read JSON files and insert them into tranmogrifier pipeline.

Parameters
----------

:path (required):
    Path to directory containing JSON files (look in example bellow).

    Also possible to specify in ``some.package:path/to/json/directory`` way.

:path-separator:
    os path separator use in json file (in case of json file is created on windows) 

:datafield-prefix:
    prefix for indicate  file fields prefix. Path is transformed by this blue print 

Example
-------

Configuration::

    [tranmogrifier]
    pipeline =
        source

    [source]
    blueprint = collective.blueprint.jsonmigrator.source
    path = some.package:/path/to/json/dir
    path-separator = \
    datafield-prefix = _data_    

JSON files structure::

    some.package:/path/to/json/dir
        |-> 0/
            |-> 1.json
            |-> 2.json
            ...
            |-> 999.json
        |-> 1/
            |-> 1000.json
            |-> 1001.json
            ...

JSON file::

    {
        "_path": "/Plone/front-page",
        "_type": "Document",
        ...
        "_data_backgroundImage": {
             "path": "0\\20.json-file-1", 
        },
    }
