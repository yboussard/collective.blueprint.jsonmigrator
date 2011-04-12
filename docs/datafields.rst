``collective.blueprint.jsonmigrator.datafields``
================================================

Update data/blob fields of an object.

:TODO: missing base path (maybe even passed somehow from source blueprint)
:TODO: only update if needed

Configuration options
---------------------

No specific blueprint parameters.

Expected data structure in pipeline:

    * **_path**: path to object on which we want to change local roles.
    * **_datafield_<field>**: field which needs to store data

Option configuration:

    * datafield-prefix : for changing the prefix (by default _datafield_)
    * path-key : for changing the path key
    * datafield-separator : for changing separator of prefix

Example
-------

This example will try to store content of ``0/1.json-file-1`` into
``attachment`` field of ``/Plone/index_html`` object.

Configuration::

    [tranmogrifier]
    pipeline =
        source
        datafields

    ...

    [datafields]
    blueprint = collective.blueprint.jsonmigrator.datafields

Data in pipeline::

    {
        "_path": "/Plone/index_html", 
        "_datafield_attachment": {"filename": "DAF.jpg", 
                                 "content_type": "image/jpeg", 
                                 "path": "0\\20.json-file-1", 
                                 "height": 605, 
                                 "size": 63912,
                                 }
    }
