from rdflib import Graph, Namespace, RDF, RDFS, Literal
import xml.etree.ElementTree as ET
import _winreg as winreg
import os
import sys
import udm

import collections
import functools


# Memoize taken from https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
class memoized(object):
    """Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # un-cacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)


class MgaRdfConverter(object):
    def __init__(self, udm_xml=None):
        self.g = Graph()

        self.NS_GME = Namespace('https://forge.isis.vanderbilt.edu/gme/')
        self.NS_METAMODEL = Namespace('http://www.metamorphsoftware.com/openmeta/')
        self.NS_MODEL = Namespace('http://localhost/model/')

        self.URI_ARCHETYPE = self.NS_GME['archetype']
        self.URI_GME_NAME = self.NS_GME.name
        self.URI_METAMODEL_NAME = self.NS_METAMODEL.name
        self.URI_GME_PARENT = self.NS_GME.parent
        self.URI_GME_SUBTYPE = self.NS_GME.subtype
        self.URI_GME_INSTANCE = self.NS_GME.instance

        self.g.namespace_manager.bind('gme', self.NS_GME)
        self.g.namespace_manager.bind('openmeta', self.NS_METAMODEL)
        self.g.namespace_manager.bind('model', self.NS_MODEL)

        self._assoc_class_names = set()

        # Dictionary format:
        #   class name : set of names of attributes that this class has
        self._class_attributes = dict()

        # Dictionary format:
        #   reference class name : rolename
        # (reference side rolename, not referent side)
        # We need this rolename in order to find call the right attribute
        # for fetching the referent when we have the reference object.
        self._reference_class_roles = dict()

        g_meta = Graph()
        g_meta.namespace_manager.bind('gme', self.NS_GME)
        g_meta.namespace_manager.bind('openmeta', self.NS_METAMODEL)

        if udm_xml:
            self.parse_metamodel(g_meta, udm_xml)

    def parse_metamodel(self, g_meta, udm_xml):
        tree = ET.parse(udm_xml)
        root = tree.getroot()
        # Build graph structures around the language
        for clazz in root.iter('Class'):
            id_class = clazz.get('_id')
            uri_class = self.NS_METAMODEL[id_class]
            g_meta.add((uri_class, RDF.type, self.NS_GME['class']))
            g_meta.add((uri_class, self.NS_GME['id'], Literal(id_class)))
            g_meta.add((uri_class, self.NS_GME['name'], Literal(clazz.get('name'))))
            g_meta.add((uri_class, self.NS_GME['isAbstract'], Literal(clazz.get('isAbstract') == 'true')))

            basetypes = clazz.get('baseTypes')
            if basetypes:
                for basetype_id in basetypes.split(' '):
                    g_meta.add((uri_class, self.NS_GME['baseType'], self.NS_METAMODEL[basetype_id]))

            stereotype = clazz.get('stereotype')
            if stereotype == 'Connection':
                g_meta.add((uri_class, RDF.type, self.NS_GME['association']))
                self._assoc_class_names.add(clazz.get('name'))

            elif stereotype == 'Reference':
                assoc_role_ids = clazz.get('associationRoles')

                if assoc_role_ids:
                    for assoc_role_id in assoc_role_ids.split(' '):
                        # We need to get the corresponding association.
                        association = tree.find('.//AssociationRole[@_id="{}"]/..'
                                                .format(assoc_role_id))

                        # We need to make sure that the Association does not correspond to a Connection class.
                        # This is the only way to tell reference associations from connection associations.
                        # A Reference class has exactly one referent class.
                        # If Association has no "assocClass" attribute, then we're clear.
                        if association.get('assocClass'):
                            continue

                        rolename = None
                        association_roles = association.findall('AssociationRole')
                        for ar in association_roles:
                            id_ar_target = ar.get('target')
                            if id_ar_target != id_class:
                                rolename = ar.get('name')

                        if rolename:
                            self._reference_class_roles[clazz.get('name')] = rolename

            for attr in clazz.iter('Attribute'):
                g_meta.add((uri_class, self.NS_GME['hasAttribute'], Literal(attr.get('name'))))

        sparql_PropogateAttributeInheritance = """
                PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>

                CONSTRUCT {?subclass gme:hasAttribute ?attribute}
                WHERE {
                    ?class a gme:class . 
                    ?class gme:hasAttribute ?attribute .
                    ?subclass  gme:baseType ?class
                }"""
        result_attr_inheritance = g_meta.query(sparql_PropogateAttributeInheritance)
        g_attr_inheritance = Graph().parse(data=result_attr_inheritance.serialize())
        g_inheritance = g_meta + g_attr_inheritance

        sparql_AllClassAttributes = """
                PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>

                SELECT ?class_name ?attribute
                WHERE {
                    ?class a gme:class .
                    ?class gme:name ?class_name .
                    ?class gme:hasAttribute ?attribute
                }"""
        for row in g_inheritance.query(sparql_AllClassAttributes):
            name_class = str(row[0])
            name_attr = str(row[1])

            if name_class not in self._class_attributes:
                self._class_attributes[name_class] = set()
            self._class_attributes[name_class].add(name_attr)

    @staticmethod
    def convert(fco, udm_xml=None):
        v = MgaRdfConverter(udm_xml=udm_xml)
        v.visit(fco)
        return v.g

    @memoized
    def build_obj_uri(self, obj_id):
        return self.NS_MODEL['id_' + str(obj_id)]

    @memoized
    def build_type_uri(self, type_name):
        return self.NS_METAMODEL[type_name]

    # Many attribute values are repeated, so it's worthwhile to memoize
    @memoized
    def val_to_literal(self, value):
        return Literal(value)

    # These attribute URIs get built frequently, so it's worthwhile to memoize
    @memoized
    def build_attr_uri(self, name_attr):
        return self.NS_METAMODEL[name_attr]

    @memoized
    def build_connection_role_uris(self, name_class):
        uri_src_role = self.NS_METAMODEL['src' + name_class]
        uri_dst_role = self.NS_METAMODEL['dst' + name_class]
        return uri_src_role, uri_dst_role

    @staticmethod
    def ancestors(o):
        while o:
            yield o
            o = o.parent

    def visit(self, obj):
        uri_obj = self.build_obj_uri(obj.id)
        obj_type_name = obj.type.name
        uri_type = self.build_type_uri(obj_type_name)

        self.g.add((uri_obj, RDF.type, uri_type))

        ancestor_chain = list([a.name for a in self.ancestors(obj)])
        ancestor_chain.reverse()
        self.g.add((uri_obj, self.NS_GME['path'],
                    Literal('.'.join(ancestor_chain))))

        if obj.is_subtype:
            self.g.add((uri_obj, RDF.type, self.URI_GME_SUBTYPE))
        if obj.is_instance:
            self.g.add((uri_obj, RDF.type, self.URI_GME_INSTANCE))
        if not obj.archetype == udm.null:
            arch_uri = self.build_obj_uri(obj.archetype.id)
            self.g.add((uri_obj, self.URI_ARCHETYPE, arch_uri))

        if obj_type_name in self._assoc_class_names:
            src_attr = getattr(obj, 'src' + obj_type_name)
            dst_attr = getattr(obj, 'dst' + obj_type_name)

            src_uri = self.build_obj_uri(src_attr.id)
            dst_uri = self.build_obj_uri(dst_attr.id)

            uri_src_role, uri_dst_role = self.build_connection_role_uris(obj_type_name)

            self.g.add((uri_obj, uri_src_role, src_uri))
            self.g.add((uri_obj, uri_dst_role, dst_uri))

        # Attributes
        if obj_type_name in self._class_attributes:
            for name_attr in self._class_attributes[obj_type_name]:
                val_attr = getattr(obj, name_attr)
                literal_attr = self.val_to_literal(val_attr)
                self.g.add((uri_obj, self.build_attr_uri(name_attr), literal_attr))

        # References
        if obj_type_name in self._reference_class_roles:
            rolename = self._reference_class_roles[obj_type_name]
            referent = getattr(obj, rolename)
            uri_referent = self.build_obj_uri(referent.id)

            self.g.add((uri_obj, self.NS_GME.references, uri_referent))

        literal_name = Literal(obj.name)
        self.g.add((uri_obj, self.URI_GME_NAME, literal_name))
        self.g.add((uri_obj, self.URI_METAMODEL_NAME, literal_name))

        if not obj.parent == udm.null:
            parent_uri = self.build_obj_uri(obj.parent.id)
            self.g.add((uri_obj, self.URI_GME_PARENT, parent_uri))

        for child in obj.children():
            self.visit(child)
