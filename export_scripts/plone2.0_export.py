###############################################################################
#####                                                                     #####
#####   IMPORTANT, READ THIS !!!                                          #####
#####   ------------------------                                          #####
#####                                                                     #####
#####   Bellow is the external method which you enable by adding it       #####
#####   into your Plone site.                                             #####
#####                                                                     #####
###############################################################################

import os
import re
import shutil
import ConfigParser
### DEPENDENCY 2.0.0 for python2.3
import simplejson

from datetime import datetime
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from App.config import getConfiguration
CONFIG = ConfigParser.SafeConfigParser()
CONFIG.optionxform = str
import logging
logger = logging.getLogger('plone20_export')

PAV3_MODEL_RE = re.compile(r'plonearticle_model([\d]*)')

try:
    #import pdb;pdb.set_trace();
    CONFIG.readfp(open(os.path.join(getConfiguration().instancehome,
                                    'jsonmigrator.ini')))
except:
    logger.exception('Please specify ini file jsonmigrator.ini')
    logger.warning('Please specify ini file jsonmigrator.ini in your %s' \
          % getConfiguration().instancehome)

COUNTER = 1

############## Move configuration to jsonmigrator.ini 
############## in DEFAULT section specify
##############     - CLASSNAME_TO_SKIP_LAUD (list separated by CARRIAGE_RETURN)
##############     -  CLASSNAME_TO_SKIP  (list separated by CARRIAGE_RETURN)

def getconf(option, default):
    global CONFIG
    if not CONFIG.has_option('DEFAULT', option):
        return default
    else:
        return CONFIG.get('DEFAULT', option)
        
    

HOMEDIR = getconf('HOMEDIR',
                  '/Users/rok/Projects/yaco/unex_exported_data')
logger.info("HOMEDIR : %s" % HOMEDIR)

CLASSNAME_TO_SKIP_LAUD = [x.strip() for x \
                          in getconf('CLASSNAME_TO_SKIP_LAUD',
                                    """ControllerPythonScript
                                    ControllerPageTemplate
                                    ControllerValidator
                                    PythonScript
                                    SQL
                                    Connection
                                    ZetadbScript
                                    ExternalMethod
                                    ZetadbSqlInsert
                                    ZetadbMysqlda
                                    SiteRoot
                                    ZetadbApplication
                                    ZetadbZptInsert
                                    I18NLayer
                                    ZetadbZptView
                                    BrowserIdManager
                                    ZetadbScriptSelectMaster
                                    ZetadbSqlSelect""").splitlines()]

CLASSNAME_TO_SKIP = [x.strip() for x \
                          in getconf('CLASSNAME_TO_SKIP',
                                        """CatalogTool
                                        MemberDataTool
                                        SkinsTool
                                        TypesTool
                                        UndoTool
                                        URLTool
                                        WorkflowTool
                                        DiscussionTool
                                        MembershipTool
                                        RegistrationTool
                                        PropertiesTool
                                        MetadataTool
                                        SyndicationTool
                                        PloneTool
                                        NavigationTool
                                        FactoryTool
                                        FormTool
                                        MigrationTool
                                        CalendarTool
                                        QuickInstallerTool
                                        GroupsTool
                                        GroupDataTool
                                        MailHost
                                        CookieCrumbler
                                        ContentTypeRegistry
                                        GroupUserFolder
                                        CachingPolicyManager
                                        InterfaceTool
                                        PloneControlPanel
                                        FormController
                                        SiteErrorLog
                                        SinTool
                                        ArchetypeTool
                                        RAMCacheManager
                                        PloneArticleTool
                                        SyndicationInformation
                                        ActionIconsTool
                                        AcceleratedHTTPCacheManager
                                        ActionsTool
                                        UIDCatalog
                                        ReferenceCatalog
                                        ContentPanelsTool
                                        MimeTypesRegistry
                                        LanguageTool
                                        TransformTool""").splitlines()]

ID_TO_SKIP = [x.strip() for x \
                          in getconf('ID_TO_SKIP',
                                        """Members""").splitlines()]
NON_FOLDERISH_CLASSNAME = [x.strip() for x \
                          in getconf('NON_FOLDERISH_CLASSNAME',
                                        """PloneArticle""").splitlines()]
JUST_TREAT_WAPPER = False
try:
    JUST_TREAT_WAPPER = eval(getconf('JUST_TREAT_WAPPER',False))
except:
    JUST_TREAT_WAPPER = False
print 'ID_TO_SKIP %s ' % str(ID_TO_SKIP)

try:
    MAX_TREAT = int(getconf('MAX_TREAT', 0))
except:
    MAX_TREAT = 0

try:
    MAX_CACHE_DB = int(getconf('MAX_CACHE_DB', 500))
except:
    MAX_CACHE_DB = 500


def export_plone20(self):

    global COUNTER
    global TMPDIR
    global ID_TO_SKIP

    COUNTER = 1
    TODAY = datetime.today()
    TMPDIR = os.path.join(HOMEDIR,'content_%s_%s' % \
                          (self.getId(),
                           TODAY.strftime('%Y-%m-%d-%H-%M-%S')))

    id_to_skip = self.REQUEST.get('id_to_skip', None)
    if id_to_skip is not None:
        ID_TO_SKIP += id_to_skip.split(',')

    if os.path.isdir(TMPDIR):
        shutil.rmtree(TMPDIR)
    else:
        os.mkdir(TMPDIR)
    
    write(walk(self))

    # TODO: we should return something more useful
    return 'SUCCESS :: '+self.absolute_url()+'\n'


def walk(folder):
    global COUNTER
    for item_id in folder.objectIds():
        item = folder[item_id]
        if item.__class__.__name__ in CLASSNAME_TO_SKIP or \
           item.getId() in ID_TO_SKIP or (JUST_TREAT_WAPPER and \
                item.__class__.__name__\
                                          not in CLASSNAME_TO_WAPPER_MAP) or \
                (item.__class__.__name__ in CLASSNAME_TO_SKIP_LAUD):
            logger.info('>> SKIPPING :: ['+item.__class__.__name__+'] '\
                                          + item.absolute_url())
            continue
        if MAX_TREAT != 0 and COUNTER >= MAX_TREAT:
            continue
        logger.info('>> TREAT :: ('+ str(COUNTER) +')['+item.__class__.__name__+'] '\
                                          + item.absolute_url())
        yield item
        if getattr(item, 'objectIds', None) and \
           item.objectIds() and \
           item.__class__.__name__  not in NON_FOLDERISH_CLASSNAME:
            for subitem in walk(item):
                yield subitem


def write(items):

    global COUNTER

    for item in items:
        if item.__class__.__name__\
               not in CLASSNAME_TO_WAPPER_MAP.keys():
            import pdb; pdb.set_trace()
            raise Exception, 'No wrapper defined for "'+item.__class__.__name__+ \
                                                  '" ('+item.absolute_url()+').'
        try:
            
            dictionary = CLASSNAME_TO_WAPPER_MAP[item.__class__.__name__](item)
            write_to_jsonfile(dictionary)
            COUNTER += 1
            if (COUNTER % MAX_CACHE_DB)==0:
                logger.info('Purge ZODB cache')
                [item.Control_Panel.Database[x]._getDB().cacheMinimize() \
                 for x in item.Control_Panel.Database.getDatabaseNames()]
        except:
            print "there is an error on %s" % item.absolute_url()
            #import pdb;pdb.set_trace();
            raise


def write_to_jsonfile(item):
    global COUNTER
    

    SUB_TMPDIR = os.path.join(TMPDIR, str(COUNTER/1000)) # 1000 files per folder, so we dont reach some fs limit
    if not os.path.isdir(SUB_TMPDIR):
        os.mkdir(SUB_TMPDIR)

    # we store data fields in separate files
    datafield_counter = 1
    if '__datafields__' in item.keys():
        for datafield in item['__datafields__']:
            datafield_filepath = os.path.join(SUB_TMPDIR, str(COUNTER)+'.json-file-'+str(datafield_counter))
            f = open(datafield_filepath, 'wb')
            if type(item[datafield]) is dict:
                f.write(item[datafield]['data'])
                del item[datafield]['data']
            else:
                f.write(item[datafield])
                item[datafield] = {}
            #f.write(item[datafield])
            item[datafield]['path'] = os.path.join(str(COUNTER/1000), str(COUNTER)+'.json-file-'+str(datafield_counter))
            #item[datafield] = os.path.join(str(COUNTER/1000), str(COUNTER)+'.json-file-'+str(datafield_counter))
            f.close()
            datafield_counter += 1
        item.pop(u'__datafields__')
    if '_plonearticle_attachments' in item:
        for item2 in item['_plonearticle_attachments']:
            if not item2.has_key('attachedFile'):
                continue
            datafield_filepath = os.path.join(SUB_TMPDIR, str(COUNTER)+'.json-file-'+str(datafield_counter))
            f = open(datafield_filepath, 'wb')            
            f.write(item2['attachedFile'][0]['data'])            
            item2['attachedFile'][0]['data'] = os.path.join(str(COUNTER/1000), str(COUNTER)+'.json-file-'+str(datafield_counter))
            f.close()
            datafield_counter += 1
    if '_plonearticle_images' in item:
        for item2 in item['_plonearticle_images']:
            if not item2.has_key('attachedImage'):
                continue
            datafield_filepath = os.path.join(SUB_TMPDIR, str(COUNTER)+'.json-file-'+str(datafield_counter))
            f = open(datafield_filepath, 'wb')
            try:
                f.write(item2['attachedImage'][0]['data'])
            except:
                import pdb; pdb.set_trace()
            item2['attachedImage'][0]['data'] = os.path.join(str(COUNTER/1000), str(COUNTER)+'.json-file-'+str(datafield_counter))
            f.close()
            datafield_counter += 1
    
    f = open(os.path.join(SUB_TMPDIR, str(COUNTER)+'.json'), 'wb')
    try:
        simplejson.dump(item, f, indent=4)
    except:
        raise str(item)
    f.close()


def getPermissionMapping(acperm):
    result = {}
    for entry in acperm:
        result[entry[0]] = entry[1]
    return result

def safe_decode(s, charset, errors):
    if type(s) is type(u''):
        return s
    if hasattr(s, 'decode'):
        return s.decode(charset, errors)

    if s.__class__.__name__ == 'BaseUnit':
        return str(s).decode(charset, errors)
    else:
        return s

class BaseWrapper(dict):
    """Wraps the dublin core metadata and pass it as tranmogrifier friendly style
    """

    def __init__(self, obj):
        self.obj = obj

        self.portal = getToolByName(obj, 'portal_url').getPortalObject()
        relative_url = getToolByName(obj, 'portal_url').getRelativeContentURL
        self.portal_utils = getToolByName(obj, 'plone_utils')
        self.charset = self.portal.portal_properties.site_properties.default_charset

        if not self.charset: # newer seen it missing ... but users can change it
            self.charset = 'utf-8'
        
        self['__datafields__'] = []
        #self['_path'] = '/'.join(self.obj.getPhysicalPath())
        self['_path'] = relative_url(self.obj)
        self['_type'] = self.obj.__class__.__name__

        self['id'] = obj.getId()
        self['title'] = safe_decode(obj.title,self.charset, 'ignore')
        self['description'] = safe_decode(obj.description,self.charset, 'ignore')
        self['language'] = obj.Language()
        self['rights'] = safe_decode(obj.rights,self.charset, 'ignore')
        # for DC attrs that are tuples
        for attr in ('subject', 'contributors'):
            self[attr] = []
            val_tuple = getattr(obj, attr, False)
            if val_tuple:
                for val in val_tuple:
                    self[attr].append(safe_decode(val,self.charset, 'ignore'))
                self[attr] = tuple(self[attr])
        # Creators
        self['creators'] = []
        val_tuple = obj.Creators()
        if val_tuple:
            for val in val_tuple:
                self['creators'].append(safe_decode(val,self.charset, 'ignore'))
                
        
        # for DC attrs that are DateTimes
        datetimes_dict = {'creation_date': 'creation_date',
                          'modification_date': 'modification_date',
                          'expiration_date': 'expirationDate',
                          'effective_date': 'effectiveDate'}
        for old_name, new_name in datetimes_dict.items():
            val = getattr(obj, old_name, False)
            if val:
                self[new_name] = str(val)

        # workflow history
        if hasattr(obj, 'workflow_history'):
            workflow_history = obj.workflow_history.data
            try:
                for w in workflow_history:
                    for i, w2 in enumerate(workflow_history[w]):
                        workflow_history[w][i]['time'] = str(workflow_history[w][i]['time'])
                        workflow_history[w][i]['comments'] = safe_decode(workflow_history[w][i]['comments'],self.charset, 'ignore')
            except:
                import pdb; pdb.set_trace()
            self['_workflow_history'] = workflow_history

        # default view
        
        if 'layout' in obj.__dict__:
            self['_layout'] = obj.__dict__['layout']
        try:
            _browser = self.plone_utils.browserDefault(aq_base(obj))[1]
        except:
            _browser = None
        if _browser:
            ## _browser can be value [None]
            try:
                _browser = '/'.join(_browser)
            except:
                _browser = ''
            if _browser not in ['folder_listing']:
                self['_layout'] = ''
                self['_defaultpage'] = _browser
        #elif obj.getId() != 'index_html':
        #    self['_layout'] = _browser
        #    self['_defaultpage'] = ''

        # format
        self['_content_type'] = obj.Format()

        # properties
        self['_properties'] = []
        if getattr(aq_base(obj), 'propertyIds', False):
            obj_base = aq_base(obj)
            for pid in obj_base.propertyIds():
                val = obj_base.getProperty(pid)
                typ = obj_base.getPropertyType(pid)
                if typ == 'string':
                    if getattr(val, 'decode', False):
                        try:
                            val = safe_decode(val,self.charset, 'ignore')
                        except UnicodeEncodeError:
                            val = unicode(val)
                    else:
                        val = unicode(val)
                self['_properties'].append((pid, val,
                                       obj_base.getPropertyType(pid)))

        # local roles
        self['_ac_local_roles'] = {}
        if getattr(obj, '__ac_local_roles__', False):
            for key, val in obj.__ac_local_roles__.items():
                if key is not None:
                    self['_ac_local_roles'][key] = val
                    if 'Owner' in val:
                        self['_owner'] = key

        self['_userdefined_roles'] = ()
        if getattr(aq_base(obj), 'userdefined_roles', False):
            self['_userdefined_roles'] = obj.userdefined_roles()

        self['_permission_mapping'] = {}
        if getattr(aq_base(obj), 'permission_settings', False):
            roles = obj.validRoles()
            ps = obj.permission_settings()
            for perm in ps:
                unchecked = 0
                if not perm['acquire']:
                    unchecked = 1
                new_roles = []
                for role in perm['roles']:
                    if role['checked']:
                        role_idx = role['name'].index('r')+1
                        role_name = roles[int(role['name'][role_idx:])]
                        new_roles.append(role_name)
                if unchecked or new_roles:
                    self['_permission_mapping'][perm['name']] = \
                         {'acquire': not unchecked,
                          'roles': new_roles}
    
        if getattr(aq_base(obj), 'isCanonical', False):
            if not obj.isCanonical():
                canonical = obj.getCanonical()
                self['_canonical'] = relative_url(canonical)
                
                        
#        self['_ac_inherited_permissions'] = {}
#        if getattr(aq_base(obj), 'ac_inherited_permissions', False):
#            oldmap = getPermissionMapping(obj.ac_inherited_permissions(1))
#            for key, values in oldmap.items():
#                old_p = Permission(key, values, obj)
#                self['_ac_inherited_permissions'][key] = old_p.getRoles()

        

        #if getattr(aq_base(obj), 'getWrappedOwner', False):
        #    self['_owner'] = (1, obj.getWrappedOwner().getId())
        #else:
            # fallback
            # not very nice but at least it works
            # trying to get/set the owner via getOwner(), changeOwnership(...)
            # did not work, at least not with plone 1.x, at 1.0.1, zope 2.6.2
        #    self['_owner'] = (0, obj.getOwner(info = 1).getId())

    def decode(self, s, encodings=('utf8', 'latin1', 'ascii')):
        if self.charset:
            test_encodings = (self.charset, ) + encodings
        for encoding in test_encodings:
            try:
                return s.decode(encoding)
            except UnicodeDecodeError:
                pass
        return safe_decode(s,test_encodings[0], 'ignore')


class DocumentWrapper(BaseWrapper):

    def __init__(self, obj):
        super(DocumentWrapper, self).__init__(obj)
        if hasattr(obj, 'text'):
            self['text'] = safe_decode(obj.text,self.charset, 'ignore')


class I18NFolderWrapper(BaseWrapper):

    def __init__(self, obj):
        super(I18NFolderWrapper, self).__init__(obj)
        # We are ignoring another languages
        lang = obj.getDefaultLanguage()
        data = obj.folder_languages.get(lang, None)
        if data is not None:
            self['title'] = safe_decode(data['title'],self.charset, 'ignore')
            self['description'] = safe_decode(data['description'],self.charset, 'ignore')
        else:
            logger.error('ERROR: Cannot get default data for I18NFolder "%s"' % self['_path'])

        # delete empty title in properties
        for prop in self['_properties']:
            propname, propvalue, proptitle = prop
            if propname == "title":
                self['_properties'].remove(prop)


        # Not lose information: generate properites es_title, en_title, etc.
        for lang in obj.folder_languages:
            data = obj.folder_languages[lang]
            for field in data:
                self['_properties'].append(['%s_%s' % (lang, field),
                                            safe_decode(data[field],self.charset, 'ignore'),
                                            'text'])


class LinkWrapper(BaseWrapper):

    def __init__(self, obj):
        super(LinkWrapper, self).__init__(obj)
        self['remoteUrl'] = obj.remote_url()


class NewsItemWrapper(DocumentWrapper):

    def __init__(self, obj):
        super(NewsItemWrapper, self).__init__(obj)
        self['text_format'] = obj.text_format


class ListCriteriaWrapper(BaseWrapper):

    def __init__(self, obj):
        super(ListCriteriaWrapper, self).__init__(obj)
        self['field'] = obj.field
        self['value'] = obj.value
        self['operator'] = obj.operator


class StringCriteriaWrapper(BaseWrapper):

    def __init__(self, obj):
        super(StringCriteriaWrapper, self).__init__(obj)
        self['field'] = obj.field
        self['value'] = obj.value


class SortCriteriaWrapper(BaseWrapper):

    def __init__(self, obj):
        super(SortCriteriaWrapper, self).__init__(obj)
        self['index'] = obj.index
        self['reversed'] = obj.reversed


class DateCriteriaWrapper(BaseWrapper):

    def __init__(self, obj):
        super(DateCriteriaWrapper, self).__init__(obj)
        self['field'] = obj.field
        self['value'] = obj.value
        self['operation'] = obj.operation
        self['daterange'] = obj.daterange


class FileWrapper(BaseWrapper):
    ## fs file ##
    def __init__(self, obj):
        super(FileWrapper, self).__init__(obj)
        self['__datafields__'].append('_datafield_file')
        data = str(obj.data)
        if len(data) != obj.getSize():
             raise Exception, 'Problem while extracting data for File content type at '+obj.absolute_url()
        self['_datafield_file'] = data



class ImageWrapper(BaseWrapper):
    ## fs image ##
    def __init__(self, obj):
        super(ImageWrapper, self).__init__(obj)
        self['__datafields__'].append('_datafield_image')
        data = str(obj.data)
        if len(data) != obj.getSize():
             raise Exception, 'Problem while extracting data for Image content type at '+obj.absolute_url()
        self['_datafield_image'] = data


class EventWrapper(BaseWrapper):

    def __init__(self, obj):
        super(EventWrapper, self).__init__(obj)
        self['startDate'] = str(obj.start_date)
        self['endDate'] = str(obj.end_date)
        self['location'] = safe_decode(obj.location,self.charset, 'ignore')
        self['contactName'] = safe_decode(obj.contact_name(),self.charset, 'ignore')
        self['contactEmail'] = obj.contact_email()
        self['contactPhone'] = obj.contact_phone()
        self['eventUrl'] = obj.event_url()


class ArchetypesWrapper(BaseWrapper):

    def __init__(self, obj):
        
        super(ArchetypesWrapper, self).__init__(obj)
        
        fields = obj.schema.fields()
        for field in fields:
            type_ = field.__class__.__name__
            if type_ in ['StringField', 'BooleanField', 'LinesField', 'IntegerField', 'TextField',
                         'SimpleDataGridField', 'FloatField', 'FixedPointField']:
                try:
                    value = field.get(obj)
                except:
                    try:
                        value = field.getRaw(obj)
                    except:
                        if field.getStorage().__class__.__name__ == 'PostgreSQLStorage':
                            continue
                        else:
                            import pdb; pdb.set_trace()
                if callable(value) is True:
                    value = value()
                if value:
                    self[unicode(field.__name__)] = value
            elif type_ in ['TALESString', 'ZPTField']:
                value = field.getRaw(obj)
                if value:
                    self[unicode(field.__name__)] = value
            elif type_ in ['DateTimeField']:
                value = str(field.get(obj))
                if value:
                    self[unicode(field.__name__)] = value
            elif type_ in ['ReferenceField']:
                value = field.get(obj)
                if value:
                    if field.multiValued:
                        self[unicode(field.__name__)] = ['/'+i.absolute_url() for i in value]
                    else:
                        self[unicode(field.__name__)] = value.absolute_url()
            elif type_ in ['ImageField', 'FileField', 'AttachmentField']:
                #import pdb;pdb.set_trace();
                fieldname = unicode('_data_'+field.__name__)
                value = field.get(obj)
                value2 = value
                if type(value) is not str:
                    try:
                        value = str(value.data)
                    except:
                        import pdb;pdb.set_trace();
                if value:
                    
                    self['__datafields__'].append(fieldname)
                    self[fieldname] = {}
                    for x in field.get(obj).__dict__:
                        if type(field.get(obj).__dict__[x]) in (int,str):  
                            self[fieldname][x] = field.get(obj).__dict__[x]
                    self[fieldname]['data'] = value

            elif type_ in ['ComputedField']:
                pass
            
            else:
                
                raise 'Unknown field type for ArchetypesWrapper : %s' % type_

    def _guessFilename(self, data, fname='', mimetype='', default=''):
        """
         Use the mimetype to guess the extension of the file/datafield if none exists.
         This is not a 100% correct, but does not really matter.
         In most cases it is nice that a word document has the doc extension, or that a picture has jpeg or bmp.
         It is a bit more human readable. When the extension is wrong it can just be ignored by the import anyway.
         """
        if not fname:
            return fname
        obj = self.obj
        mimetool = getToolByName(obj, 'mimetypes_registry')
        imimetype = mimetool.lookupExtension(fname)
        if mimetype and (imimetype is None): # no valid extension on fname
            # find extensions for mimetype
            classification = mimetool.classify(data, mimetype=mimetype)
            extensions = getattr(classification, 'extensions', default)
            extension = extensions[0] # just take the first one ... :-s
            fname = '%s.%s' % (fname, extension)
        return fname


class I18NLayerWrapper(ArchetypesWrapper):

    def __init__(self, obj):
        super(I18NLayerWrapper, self).__init__(obj)
        lang = obj.portal_properties.site_properties.default_language
        if lang not in obj.objectIds():
            logger.error('ERROR: Cannot get default data for I18NLayer "%s"' % self['_path'])
        else:
            real = obj[lang]
            self['title'] = safe_decode(real.title,self.charset, 'ignore')
            self['description'] = safe_decode(real.description,self.charset, 'ignore')
            self['text'] = safe_decode(real.text,self.charset, 'ignore')

        # Not lose information: generate properites es_title, en_title, etc.
        # TODO: Export all archetypes, but I don't need now, only document important fields
        for lang, content in obj.objectItems():
            data = dict(title = content.title,
                        description = content.description,
                        text = content.text)
            for field in data:
                self['_properties'].append(['%s_%s' % (lang, field),
                                            safe_decode(data[field],self.charset, 'ignore'),
                                            'text'])

def generateUniqueId(type_name=None):
    """
        Generate an id for the content
        This is not the archetype's uid.
    """
    from DateTime import DateTime
    from random import random

    now = DateTime()
    time = '%s.%s' % (now.strftime('%Y-%m-%d'), str(now.millis())[7:])
    rand = str(random())[2:6]
    prefix = ''
    suffix = ''

    if type_name is not None:
        prefix = type_name.replace(' ', '_') + '.'
    prefix = prefix.lower()

    return prefix + time + rand + suffix


def getNewModelName(model):
    re_match = PAV3_MODEL_RE.search(model)
    if re_match is not None:
        model = 'pa_model%s' % (re_match.group(1) or '1',)
    elif model == 'plonearticle_view':
        model = 'pa_model1'
    return model


class Article322Wrapper(NewsItemWrapper):

    def __init__(self, obj):
        super(Article322Wrapper, self).__init__(obj)
        
        #(Pdb) self.__ordered_attachment_refs__.getItems()
        #['4e952a8c3af4b1bcedf38d475ac6049d']
        d = {'__ordered_attachment_refs__' : ('_plonearticle_attachments',
                                              'FileProxy',
                                              'attachedFile',
                                              'getFile'),
             '__ordered_image_refs__' : ('_plonearticle_images',
                                         'ImageProxy',
                                         'attachedImage',
                                         'getImage'),
                                         
             '__ordered_link_refs__' : ('_plonearticle_refs',
                                        'LinkProxy',
                                        'attachedLink',
                                        'getRemoteUrl')}
        ## layout

        model = obj.getModel()
        self['_layout'] = getNewModelName(model)

        
        ids =  obj.objectIds()
        for x in d:
            slot_name = d[x][0]
            id_name =  d[x][1]
            field_name = d[x][2]
            accessor = d[x][3]
            self[slot_name] = []
            for refid in getattr(obj,x).getItems():
                ref = None
                try:
                    ref = getattr(obj.at_references, refid).getTargetObject()
                except:
                    ## ghost ref
                    logger.exception("Attribut rror during migration on %s"\
                                     % str(obj))
                    continue ## just ignore it...
                inner = {
                    'id': (generateUniqueId(id_name), {}),
                    'title': (safe_decode(ref.Title(),
                                          self.charset, 'ignore'), {}),
                    'description': (safe_decode(ref.Description(),
                                                self.charset,
                                                'ignore'), {}),}
                if ref.id in ids:
                    ### internal
                    innerfile = getattr(ref, accessor)()
                    if innerfile:
                        di = {}
                        try:
                            data = str(innerfile.data)
                            for x in innerfile.__dict__:
                                if type(innerfile.__dict__[x]) in (int,str):
                                    di[x]  = innerfile.__dict__[x]
                        except:
                            data = innerfile
                            
                        
                        di['data'] = data
                        inner[field_name] = (di, {})
                                         
                else:
                    #### external
                    inner['referencedContent'] =  (ref.UID(), {})
                self[slot_name].append(inner)

                    
                    
                    
                
                

class ArticleWrapper(NewsItemWrapper):

    def __init__(self, obj):

        super(ArticleWrapper, self).__init__(obj)
        try:
            self['cooked_text'] = obj.cooked_text.decode(self.charset)
        except:
            self['cooked_text'] = obj.cooked_text.decode('latin-1')

        plonearticle_attachments = []
        for item_id in obj.attachments_ids:
            item = obj[item_id]
            plonearticle_attachments.append({
                'id':            (item_id, {}),
                'title':         (safe_decode(item.title, self.charset, 'ignore'), {}),
                'description':   (safe_decode(item.description, self.charset, 'ignore'), {}),
                'attachedFile':  [item.getFile(), {}],
                })
        self['_plonearticle_attachments'] = plonearticle_attachments

        plonearticle_images = []
        for item_id in obj.images_ids:
            item = obj[item_id]
            plonearticle_images.append({
                'id':            (item_id, {}),
                'title':         (safe_decode(item.title, self.charset, 'ignore'), {}),
                'description':   (safe_decode(self.charset, 'ignore'), {}),
                'attachedImage': [str(item.data), {}],
                })
        self['_plonearticle_images'] = plonearticle_images


class ZPhotoWrapper(BaseWrapper):

    def __init__(self, obj):
        super(ZPhotoWrapper, self).__init__(obj)
        self['show_exif'] = obj.show_exif
        self['exif'] = obj.exif
        self['iptc'] = obj.iptc
        self['path'] = obj.path
        self['dir'] = obj.dir
        self['filename'] = obj.filename
        #self['_thumbs'] = obj._thumbs
        self['dict_info'] = obj.dict_info
        self['format'] = obj.format
        self['tmpdir'] = obj.tmpdir
        self['backup'] = obj.backup


class ZPhotoSlidesWrapper(BaseWrapper):

    def __init__(self, obj):
        super(ZPhotoSlidesWrapper, self).__init__(obj)
        try:
            self['update_date'] = str(obj.update_date)
            self['show_postcard'] = obj.show_postcard
            self['show_ARpostcard'] = obj.show_ARpostcard
            self['show_rating'] = obj.show_rating
            self['size'] = obj.size
            self['max_size'] = obj.max_size
            self['sort_field'] = obj.sort_field
            self['allow_export'] = obj.allow_export
            self['show_export'] = obj.show_export
            #self['visits_log'] = obj.visits_log
            self['non_hidden_pic'] = obj.non_hidden_pic
            self['list_non_hidden_pic'] = obj.list_non_hidden_pic
            self['rows'] = obj.rows
            self['column'] = obj.column
            self['zphoto_header'] = obj.zphoto_header
            self['list_photo'] = obj.list_photo
            self['zphoto_footer'] = obj.zphoto_footer
            self['symbolic_photo'] = obj.symbolic_photo
            self['keywords'] = obj.keywords
            self['first_big'] = obj.first_big
            self['show_automatic_slide_show'] = obj.show_automatic_slide_show
            self['show_viewed'] = obj.show_viewed
            self['show_exif'] = obj.show_exif
            self['photo_space'] = obj.photo_space
            self['last_modif'] = str(obj.last_modif)
            self['show_iptc'] = obj.show_iptc
            self['formats_available'] = obj.formats_available
            self['default_photo_size'] = obj.default_photo_size
            self['formats'] = obj.formats
            self['actual_css'] = obj.actual_css
            self['thumb_width'] = obj.thumb_width
            self['thumb_height'] = obj.thumb_height
            #self['list_rating'] = obj.list_rating
            self['photo_folder'] = obj.photo_folder
            self['tmpdir'] = obj.tmpdir
            self['lib'] = obj.lib
            self['convert'] = obj.convert
            self['use_http_cache'] = obj.use_http_cache
        except Exception:
            import pdb; pdb.set_trace()


class ContentPanels(BaseWrapper):

    def __init__(self, obj):
        super(ContentPanels, self).__init__(obj)
        self['_content_panels'] = obj.panelsConfig


class LocalFSWrapper(BaseWrapper):

    def __init__(self, obj):
        super(LocalFSWrapper, self).__init__(obj)
        self['basepath'] = obj.basepath


class ZopeObjectWrapper(BaseWrapper):

    def __init__(self, obj):
        super(ZopeObjectWrapper, self).__init__(obj)
        self['document_src'] = self.decode(obj.document_src())
        # self['__datafields__'].append('document_src')

# TODO: should be also possible to set it with through parameters
CLASSNAME_TO_WAPPER_MAP = {}
if CONFIG.has_section('CLASSNAME_TO_WAPPER_MAP'):
    for x in CONFIG.items('CLASSNAME_TO_WAPPER_MAP'):
        
        try:
            CLASSNAME_TO_WAPPER_MAP[x[0]] = eval(x[1].strip())
            logger.debug("map %s to %s" % (x[0], x[1]) )
        except:
            logger.info("cant add class for mapping %s" %  x[0])
            pass
else:
    print "load default CLASSNAME_TO_WAPPER_MAP"
    CLASSNAME_TO_WAPPER_MAP = {
        'LargePloneFolder':         BaseWrapper,
        'Folder':                   BaseWrapper,
        'PloneSite':                BaseWrapper,
        'PloneFolder':              BaseWrapper,
        'Document':                 DocumentWrapper,
        'File':                     FileWrapper,
        'Image':                    ImageWrapper,
        'Link':                     LinkWrapper,
        'Event':                    EventWrapper,
        'NewsItem':                 NewsItemWrapper,
        'Favorite':                 LinkWrapper,
        'Topic':                    BaseWrapper,
        'ListCriterion':            ListCriteriaWrapper,
        'SimpleStringCriterion':    StringCriteriaWrapper,
        'SortCriterion':            SortCriteriaWrapper,
        'FriendlyDateCriterion':    DateCriteriaWrapper,
        
        # custom ones
        'I18NFolder':               I18NFolderWrapper,
        'I18NLayer':                I18NLayerWrapper,
        'PloneArticle':             ArticleWrapper,
        'ZPhotoSlides':             ZPhotoSlidesWrapper,
        'ZPhoto':                   ZPhotoWrapper,
        'PloneLocalFolderNG':       ArchetypesWrapper,
        'LocalFS':                  LocalFSWrapper,
        'ContentPanels':            ContentPanels,
        'DTMLMethod':               ZopeObjectWrapper,
        'ZopePageTemplate':         ZopeObjectWrapper,
        
        }


