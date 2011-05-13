
import time
import tempfile
import os
import os.path
import simplejson
import logging
import transaction
import shutil
from PIL import Image
from DateTime import DateTime
from Acquisition import aq_base
from ZODB.POSException import ConflictError

from zope.interface import implements
from zope.interface import classProvides

from plone.i18n.normalizer import idnormalizer


from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import defaultKeys
from collective.transmogrifier.utils import resolvePackageReferenceOrFile

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.BaseUnit import BaseUnit
from AccessControl.interfaces import IRoleManager
from Products.PloneArticle.interfaces import IPloneArticle

## linguaplone migration
HAVE_LP = None
try:
    from Products.LinguaPlone.interfaces import ITranslatable
    HAVE_LP = True
except ImportError:
    HAVE_LP = False

DATAFIELD = '_datafield_'
STATISTICSFIELD = '_statistics_field_prefix_'

logger = logging.getLogger('collective.blueprint.jsonmigrator')

class JSONSource(object):
    """ """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        self.path = resolvePackageReferenceOrFile(options['path'])
        if self.path is None or not os.path.isdir(self.path):
            raise Exception, 'Path ('+str(self.path)+') does not exists.'

        self.datafield_prefix = options.get('datafield-prefix', DATAFIELD)
        self.datafield_separator = options.get('datafield-separator', None)

    def __iter__(self):
        for item in self.previous:
            yield item

        for item3 in sorted([int(i)
                                for i in os.listdir(self.path)
                                    if not i.startswith('.')]):

            for item2 in sorted([int(j[:-5])
                                    for j in os.listdir(os.path.join(self.path, str(item3)))
                                        if j.endswith('.json')]):
                json_file_path =  os.path.join(self.path, str(item3),
                                               str(item2)+'.json')
                f = open(json_file_path)
                try:
                    item = simplejson.loads(f.read())
                except:
                    logger.exception('error in reading %s' % json_file_path)
                item['_json_file_path'] = json_file_path
                f.close()
                for key in item.keys():
                    if key.startswith(self.datafield_prefix):
                        
                        if self.datafield_separator:
                            
                            item[key]['path'] = item[key]['path'].replace(\
                                self.datafield_separator,
                                os.path.sep)
                        #file_name = os.path.join(os.path.dirname(item[key]['']
                        #    os.path.basename(item[key]['path']
                        item[key]['path'] = os.path.join(self.path,
                                                         item[key]['path'])

                yield item

class SkipItems(object):

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.first = int(options.get('first', 0))

    def __iter__(self):
        count = 1
        for item in self.previous:
            if count > self.first:
                yield item
            count += 1

class PartialCommit(object):

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.step = int(options.get('every', 100))

    def __iter__(self):
        count = 1
        for item in self.previous:
            yield item
            if count % self.step == 0:
                transaction.commit()
            count += 1

class Statistics(object):
    """ This has to be placed in the pipeline just after all sources
    """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.stats = {'START_TIME':     int(time.time()),
                      'TIME_LAST_STEP': 0,
                      'STEP':           options.get('log-step', 25),
                      'OBJ_COUNT':      0,
                      'EXISTED':        0,
                      'ADDED':          0,
                      'NOT-ADDED':      0,}
        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.statistics_prefix = options.get('statisticsfield-prefix', STATISTICSFIELD)
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

    def __iter__(self):
        for item in self.previous:

            self.stats['OBJ_COUNT'] += 1

            yield item

            #if self.statistics_prefix + 'existed' in item and item[self.statistics_prefix + 'existed']:
            #    self.stats['EXISTED'] += 1
            #else:
            #    keys = item.keys()
            #    pathkey = self.pathkey(*keys)[0]
            #    path = item[pathkey]
            #    path = path.encode('ASCII')
            #    context = self.context.unrestrictedTraverse(path, None)
            #    if context is not None and path == '/'.join(context.getPhysicalPath()):
            #        self.stats['ADDED'] += 1
            #    else:
            #        self.stats['NOT-ADDED'] += 1

            if self.stats['OBJ_COUNT'] % self.stats['STEP'] == 0:

                keys = item.keys()
                pathkey = self.pathkey(*keys)[0]
                path = item.get(pathkey, 'Unknown')
                logging.warning('Migrating now: %s' % path)

                now = int(time.time())
                stat = 'COUNT: %d; ' % self.stats['OBJ_COUNT']
                stat += 'TOTAL TIME: %d; ' % (now - self.stats['START_TIME'])
                stat += 'STEP TIME: %d; ' % (now - self.stats['TIME_LAST_STEP'])
                self.stats['TIME_LAST_STEP'] = now
                logging.warning(stat)


class Mimetype(object):
    """ """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        if 'mimetype-key' in options:
            mimetypekeys = options['mimetype-key'].splitlines()
        else:
            mimetypekeys = defaultKeys(options['blueprint'], name, 'content_type')
        self.mimetypekey = Matcher(*mimetypekeys)

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            mimetypekey = self.mimetypekey(*item.keys())[0]

            if not pathkey or not mimetypekey or \
               mimetypekey not in item:      # not enough info
                yield item; continue

            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None:                     # path doesn't exist
                yield item; continue

            if IBaseObject.providedBy(obj):
                obj.setFormat(item[mimetypekey])

            yield item


class WorkflowHistory(object):
    """ """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.wftool = getToolByName(self.context, 'portal_workflow')

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        if 'workflowhistory-key' in options:
            workflowhistorykeys = options['workflowhistory-key'].splitlines()
        else:
            workflowhistorykeys = defaultKeys(options['blueprint'], name, 'workflow_history')
        self.workflowhistorykey = Matcher(*workflowhistorykeys)


    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            workflowhistorykey = self.workflowhistorykey(*item.keys())[0]

            if not pathkey or not workflowhistorykey or \
               workflowhistorykey not in item:  # not enough info
                yield item; continue

            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None or not getattr(obj, 'workflow_history', False):
                yield item; continue

            if IBaseObject.providedBy(obj):
                item_tmp = item

                # get back datetime stamp and set the workflow history
                for workflow in item_tmp[workflowhistorykey]:
                    for k, workflow2 in enumerate(item_tmp[workflowhistorykey][workflow]):
                        item_tmp[workflowhistorykey][workflow][k]['time'] = DateTime(item_tmp[workflowhistorykey][workflow][k]['time'])
                obj.workflow_history.data = item_tmp[workflowhistorykey]

                # update security
                workflows = self.wftool.getWorkflowsFor(obj)
                if workflows:
                    workflows[0].updateRoleMappingsFor(obj)

            yield item


class Properties(object):
    """ """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context


        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        if 'properties-key' in options:
            propertieskeys = options['properties-key'].splitlines()
        else:
            propertieskeys = defaultKeys(options['blueprint'], name, 'properties')
        self.propertieskey = Matcher(*propertieskeys)

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            propertieskey = self.propertieskey(*item.keys())[0]

            if not pathkey or not propertieskey or \
               propertieskey not in item:   # not enough info
                yield item; continue

            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None:                 # path doesn't exist
                yield item; continue
            if IBaseObject.providedBy(obj):
                if getattr(aq_base(obj), '_delProperty', False):
                    for prop in item[propertieskey]:
                        if getattr(aq_base(obj), prop[0], None) is not None:
                            # if object have a attribute equal to property, do nothing
                            continue
                        try:
                            if obj.hasProperty(prop[0]):
                                obj._updateProperty(prop[0], prop[1])
                            else:
                                obj._setProperty(prop[0], prop[1], prop[2])
                        except ConflictError:
                            raise
                        except Exception, e:
                            raise Exception('Failed to set property %s type %s to %s at object %s. ERROR: %s' % \
                                                        (prop[0], prop[1], prop[2], str(obj), str(e)))

            yield item


class Owner(object):
    """ """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.acl_users = getToolByName(self.context, 'acl_users')
        self.memtool = getToolByName(self.context, 'portal_membership')

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        if 'owner-key' in options:
            ownerkeys = options['owner-key'].splitlines()
        else:
            ownerkeys = defaultKeys(options['blueprint'], name, 'owner')
        self.ownerkey = Matcher(*ownerkeys)

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            ownerkey = self.ownerkey(*item.keys())[0]
            if not pathkey or not ownerkey or \
               ownerkey not in item:    # not enough info
                yield item; continue

            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None:             # path doesn't exist
                yield item; continue

            if IBaseObject.providedBy(obj):

                if item[ownerkey]:
                    try:
                        obj.changeOwnership(self.acl_users.getUserById(item[ownerkey]))
                    except Exception, e:
                        raise Exception('ERROR: %s SETTING OWNERSHIP TO %s' % (str(e), item[pathkey]))

                    try:
                        obj.manage_setLocalRoles(item[ownerkey], ['Owner'])
                    except Exception, e:
                        raise Exception('ERROR: %s SETTING OWNERSHIP2 TO %s' % (str(e), item[pathkey]))
            yield item


class PermissionMapping(object):
    """ """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        if 'perms-key' in options:
            permskeys = options['perms-key'].splitlines()
        else:
            permskeys = defaultKeys(options['blueprint'], name, 'permission_mapping')
        self.permskey = Matcher(*permskeys)

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            permskey = self.permskey(*item.keys())[0]

            if not pathkey or not permskey or \
               permskey not in item:    # not enough info
                yield item; continue

            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None:             # path doesn't exist
                yield item; continue

            if IRoleManager.providedBy(obj):
                for perm, perm_dict in item[permskey].items():
                    try:
                        obj.manage_permission(perm,
                            roles=perm_dict['roles'],
                            acquire=perm_dict['acquire'])
                    except ValueError:
                        logging.error('Error setting the perm "%s"' % perm)

            yield item

class LocalRoles(object):
    """ """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        if 'local-roles-key' in options:
            roleskeys = options['local-roles-key'].splitlines()
        else:
            roleskeys = defaultKeys(options['blueprint'], name, 'ac_local_roles')
        self.roleskey = Matcher(*roleskeys)

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            roleskey = self.roleskey(*item.keys())[0]

            if not pathkey or not roleskey or \
               roleskey not in item:    # not enough info
                yield item; continue

            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None:             # path doesn't exist
                yield item; continue

            if IRoleManager.providedBy(obj):
                
                if self.options.get('erasebefore'):
                    obj.__ac_local_roles__ = {}
                for principal, roles in item[roleskey].items():
                    if roles:
                        if principal.startswith(u'group_'):
                            principal = idnormalizer.normalize(principal)
                        obj.manage_addLocalRoles(principal, roles)
                obj.reindexObjectSecurity()

            yield item


class LinguaRelation(object):
    """ an section about linguaplone """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        

    def __iter__(self):
        for item in self.previous:
            
            pathkey = self.pathkey(*item.keys())[0]
            
            if not pathkey:                     # not enough info
                yield item; continue
            if not HAVE_LP:  ## not LinguaPlone
                yield item; continue
            #if  'mission' in item[pathkey]:
            #    import pdb;pdb.set_trace();

            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None:                     # path doesn't exist
                yield item; continue
            if obj.getLanguage() != item['language']:
                obj.setLanguage(item['language'])
            
            
            if not ITranslatable.providedBy(obj):
                yield item; continue ## not a linguaplone object
            else:
                canonical_path = item.get('_canonical')
                language = item.get('language','')
                if not canonical_path:
                    yield item; continue
                try:
                    canonical = self.context.unrestrictedTraverse(canonical_path.lstrip('/'), None)
                except:
                    yield item; continue
                try:
                    if not canonical.hasTranslation(language):
                        canonical.addTranslationReference(obj)
                        yield item; continue
                except:
                    yield item; continue

class PloneArticleFields(object):
    """ updata data for plonearticle fields """
    
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        
        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
        self.datafield_separator = options.get('datafield-separator', None)

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            if not pathkey:                     # not enough info
                yield item; continue
            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None:                     # path doesn't exist
                yield item; continue

            def getUnit(x, field_name):
                name = x['id'][0]
                f_path = x[field_name][0]['data']
                x = x[field_name][0]
                if self.datafield_separator:
                    f_path = f_path.replace(self.datafield_separator,
                                            os.path.sep)
                f_name = os.path.basename(f_path)
                f_path = os.path.join(os.path.dirname(\
                    item['_json_file_path']),
                                      f_name)
                
                ###
                ## type2png = image/x-ms-bmp
                value = ''
                if x.get('content_type','') in self.options.get('type2png',''):
                    path = tempfile.mkdtemp()
                    img = Image.open(f_path)
                    new_path = os.path.join(path,'image.png')
                    img.save(new_path)
                    f = open(new_path, mode = 'rb')
                    value = f.read()
                    x['content_type'] =  'image/png'
                    ext = os.path.splitext(x.get('filename', ''))[-1]
                    x['filename'] = x.get('filename','').replace(ext, '.png')
                    try:
                        os.unlink(path)
                    except:
                        pass
                else:
                    f = open(f_path, mode = 'rb')
                    value = f.read()
   

                
                unit = BaseUnit(name = name,
                                file = value,
                                mimetype = x.get('content_type', ''),
                                filename = x.get('filename', ''),
                                instance = obj)
                f.close()
                return unit

            def getReferencedContent(x):
                path = x['referencedContent'][0]
                ## we try to get content
                try:
                    refobj = self.context.restrictedTraverse(path)
                    return (refobj.UID(),{})
                except:
                    item['_error'] = item['_json_file_path']
                    logger.exception('we cant set referencedContent for %s' % path)
                
                
            if IPloneArticle.providedBy(obj):
                
                if '_plonearticle_images' in item and \
                       len(item['_plonearticle_images']):
                    for (i, x) in enumerate(item['_plonearticle_images']) :
                        if 'attachedImage' in x:
                            
                            unit = getUnit(x,'attachedImage')
                            item['_plonearticle_images'][i]['attachedImage']=\
                                                                      (unit,{})
                        elif 'referencedContent' in x:
                            
                            item['_plonearticle_images'][i]['referencedContent']=getReferencedContent(x)
                    try:
                        obj.getField('images').set(obj,item['_plonearticle_images'])
                    except:
                        item['_error'] = item['_json_file_path']
                        #import pdb;pdb.set_trace();
                        logger.exception('cannot set images for %s %s' % \
                                         (item['_path'],
                                          item['_json_file_path'])
                                         )
                if '_plonearticle_attachments' in item and\
                       len(item['_plonearticle_attachments']):

                    for (i, x) in enumerate(item['_plonearticle_attachments']):
                        if 'attachedFile' in x:
                            unit = getUnit(x,'attachedFile')
                            item['_plonearticle_attachments'][i]['attachedFile'] =\
                                                                      (unit,{})
                        elif 'referencedContent' in x:
                            item['_plonearticle_attachments'][i]['referencedContent']=getReferencedContent(x)
                    try:
                        obj.getField('files').set(obj,
                                                  item['_plonearticle_attachments'])
                    except:
                        item['_error'] = item['_json_file_path']
                        #import pdb;pdb.set_trace();
                        logger.exception('cannot set files for %s %s' % \
                                         (item['_path'],
                                          item['_json_file_path'])
                                         )
                if '_plonearticle_refs' in item and \
                       len(item['_plonearticle_refs']):
                    for (i, x) in enumerate(item['_plonearticle_refs']):
                        if 'referencedContent' in x:
                            item['_plonearticle_refs'][i]['referencedContent']=getReferencedContent(x)
                    try:
                        obj.getField('links').set(obj,
                                                  item['_plonearticle_refs'])
                    except:
                        
                        item['_error'] = item['_json_file_path']
                        logger.exception('cannot set links for %s %s' % \
                                         (item['_path'],
                                          item['_json_file_path'])
                                         )
            yield item

class ReportError(object):
    """ """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        path = resolvePackageReferenceOrFile(options['path'])
        self.json =  resolvePackageReferenceOrFile(options['json'])
        self.error_file = open(path,'w')

    def __iter__(self):
        for item in self.previous:
            if '_error' in item:
                self.error_file.write(item['_error'] + "\n")
                #shutil.copy(item['_error'], self.json)
                path = os.path.dirname(item['_error'])
                for x in (x for x in os.listdir(path) \
                          if x.startswith(os.path.basename(item['_error']))):
                    shutil.copy(os.path.join(path, x), self.json)
                    
            yield item
    
                
class DataFields(object):
    """ """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
        

        self.datafield_prefix = options.get('datafield-prefix', DATAFIELD)

    def __iter__(self):
        for item in self.previous:
            
            pathkey = self.pathkey(*item.keys())[0]
            if not pathkey:                     # not enough info
                yield item; continue
            obj = self.context.unrestrictedTraverse(item[pathkey].lstrip('/'), None)
            if obj is None:                     # path doesn't exist
                yield item; continue
                
            if IBaseObject.providedBy(obj):
                for key in item.keys():
                    if not key.startswith(self.datafield_prefix):
                        continue
                    if not os.path.exists(item[key].get('path','')):
                        continue

                    fieldname = key[len(self.datafield_prefix):]
                    field = obj.getField(fieldname)
                    f = open(item[key]['path'],mode='rb')
                    value = f.read()
                    unit = BaseUnit(name = fieldname,
                                    file = value,
                                    mimetype = item[key].get('content_type',''),
                                    filename = item[key].get('filename',''),
                                    instance = obj 
                                    )
                    f.close()
                    if len(value) != len(field.get(obj)):
                        try:
                            field.set(obj, unit)
                        except:
                            item['_error'] = item['_json_file_path']
                            logger.exception('cannot set file(%s) for %s %s' % \
                                         (fieldname,
                                          item['_path'],
                                          item['_json_file_path'])
                                         )
                            
            yield item
