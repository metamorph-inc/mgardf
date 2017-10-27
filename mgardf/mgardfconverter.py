from rdflib import Graph, Namespace, RDF, RDFS, Literal
import xml.etree.ElementTree as ET
import _winreg as winreg
import os
import sys

with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\META") as software_meta:
    meta_path, _ = winreg.QueryValueEx(software_meta, "META_PATH")
sys.path.append(os.path.join(meta_path, 'bin'))
import udm


class MgaRdfConverter(object):
    def __init__(self, udm_xml=None):
        self.g = Graph()

        self.NS_GME = Namespace('https://forge.isis.vanderbilt.edu/gme/')
        self.NS_METAMODEL = Namespace('http://www.metamorphsoftware.com/openmeta/')
        self.NS_MODEL = Namespace('http://localhost/model/')

        self.g.namespace_manager.bind('gme', self.NS_GME)
        self.g.namespace_manager.bind('openmeta', self.NS_METAMODEL)
        self.g.namespace_manager.bind('model', self.NS_MODEL)

        self._assoc_class_names = set()
        self._class_attributes = dict()

        g_meta = Graph()
        g_meta.namespace_manager.bind('gme', self.NS_GME)
        g_meta.namespace_manager.bind('openmeta', self.NS_METAMODEL)

        if udm_xml:
            tree = ET.parse(udm_xml)
            root = tree.getroot()

            # Build graph structures around the language
            for clazz in root.iter('Class'):
                uri_class = self.NS_METAMODEL[clazz.get('_id')]
                g_meta.add((uri_class, RDF.type, self.NS_GME['class']))

                g_meta.add((uri_class, self.NS_GME['id'], Literal(clazz.get('_id'))))
                g_meta.add((uri_class, self.NS_GME['name'], Literal(clazz.get('name'))))
                g_meta.add((uri_class, self.NS_GME['isAbstract'], Literal(clazz.get('isAbstract') == 'true')))

                basetypes = clazz.get('baseTypes')
                if basetypes:
                    for basetype_id in basetypes.split(' '):
                        g_meta.add((uri_class, self.NS_GME['baseType'], self.NS_METAMODEL[basetype_id]))

                association_id = clazz.get('association')
                if association_id:
                    g_meta.add((uri_class, RDF.type, self.NS_GME['association']))

                for attr in clazz.iter('Attribute'):
                    g_meta.add((uri_class, self.NS_GME['hasAttribute'], Literal(attr.get('name'))))

            # Make a list of all the association classes
            sparql_AllAssociations = """
                PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
                SELECT ?name
                WHERE {
                    ?class a gme:association .
                    ?class gme:name ?name
                }"""
            result_assoc = g_meta.query(sparql_AllAssociations)
            self._assoc_class_names = set([a[0] for a in result_assoc])

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

    def visit(self, obj):
        uri_obj = self.NS_MODEL['id_' + str(obj.id)]

        has_type = False
        type_obj = None
        try:
            type_obj = obj.type.name
            has_type = True
        except RuntimeError:
            print ('Could not identify type for object with id {}'.format(obj.id))

        if has_type:
            uri_type = self.NS_METAMODEL[type_obj]
            self.g.add((uri_obj, RDF.type, uri_type))

            if type_obj in self._assoc_class_names:
                src_attr = getattr(obj, 'src' + obj.type.name)
                dst_attr = getattr(obj, 'dst' + obj.type.name)

                src_uri = self.NS_MODEL['id_' + str(src_attr.id)]
                dst_uri = self.NS_MODEL['id_' + str(dst_attr.id)]

                self.g.add((uri_obj, self.NS_METAMODEL['src' + obj.type.name], src_uri))
                self.g.add((uri_obj, self.NS_METAMODEL['dst' + obj.type.name], dst_uri))

            # Attributes
            if type_obj in self._class_attributes:
                for attr in self._class_attributes[obj.type.name]:
                    attr_attr = getattr(obj, attr)
                    self.g.add((uri_obj, self.NS_METAMODEL[attr], Literal(attr_attr)))

        else:  # has_type == False
            # This is a folder
            uri_type = self.NS_GME['Folder']
            self.g.add((uri_obj, RDF.type, uri_type))

            if obj.parent == udm.null:
                # Additionally, this is the root folder
                uri_type = self.NS_GME['RootFolder']
                self.g.add((uri_obj, RDF.type, uri_type))

        try:
            fco_name = obj.name
            self.g.add((uri_obj, self.NS_GME.name, Literal(fco_name)))
        except Exception:
            print ('Could not get name for object with id {}'.format(obj.id))

        if not obj.parent == udm.null:
            self.g.add((uri_obj, self.NS_GME.parent, self.NS_MODEL['id_' + str(obj.parent.id)]))

        for child in obj.children():
            self.visit(child)
