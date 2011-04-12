``collective.blueprint.jsonmigrator.plonearticle``
==================================================

Update images, files, links for plone article contents.

Configuration options
---------------------

datafield-separator : os separator in case that export is provided by windows system

Expected data structure in pipeline:

    * **_plonearticle_attachments**: information of attached files
    * **_plonearticle_refs**: information of attached refs
    * **_plonearticle_images** : information of attached images

Option configuration:

    * datafield-separator : src os separator
    * path-key : for changing the path key

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
    blueprint = collective.blueprint.jsonmigrator.plonearticle

Data in pipeline::

    {
        "_path": "/Plone/index_html", 
        "_plonearticle_refs": [
        {
            "description": [
                "Missions", 
                {}
            ], 
            "referencedContent": [
                "125d3b5fd50e0da288bfb1d0751a60f7", 
                {}
            ], 
            "id": [
                "linkproxy.2011-04-10.5244530114", 
                {}
            ], 
            "title": [
                "missions", 
                {}
            ]
        }
        ],
        "_plonearticle_attachments": [
        {
            "attachedFile": [
                {
                    
                    "filename": "Voeux_JPA_VF.doc", 
                    "content_type": "application/msword", 
                    "data": "0\\1.json-file-1", 
                    "size": 29184
                }, 
                {}
            ], 
            "description": [
                "", 
                {}
            ], 
            "id": [
                "fileproxy.2011-04-10.5244535753", 
                {}
            ], 
            "title": [
                "VOEUX 2009 DE J.P AGON", 
                {}
            ]
          }, 
          {
            "attachedFile": [
                {
                    "filename": "IMG_0026 1.JPG", 
                    "content_type": "image/jpeg", 
                    "data": "0\\1.json-file-2", 
                    "size": 1228698
                }, 
                {}
            ], 
            "description": [
                "", 
                {}
            ], 
            "id": [
                "fileproxy.2011-04-10.5244539481", 
                {}
            ], 
            "title": [
                "File.doc", 
                {}
            ]
            }
        ], 
     
    
    }
