``collective.blueprint.jsonmigrator.linguarelation``
====================================================

Set linguaplone relaation between contents.

Configuration options
---------------------


Expected data structure in pipeline:

    * **_canonical**: path of canonical object


Example
-------

This example will try to store content of ``0/1.json-file-1`` 

Configuration::

    [tranmogrifier]
    pipeline =
        source
        plonearticle

    ...

    [datafields]
    blueprint = collective.blueprint.jsonmigrator.linguarelation

Data in pipeline::

    {
        "_path": "/Plone/index_html-fr", 
        "_canonical": "/Plone/index_html",
    
    }
