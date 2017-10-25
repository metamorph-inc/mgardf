from rdflib import Graph, Namespace, RDF, RDFS, Literal
import xml.etree.ElementTree as ET


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

    def visit(self, fco):
        uri_fco = self.NS_MODEL['id_' + str(fco.id)]
        uri_type = self.NS_METAMODEL[fco.type.name]
        self.g.add((uri_fco, RDF.type, uri_type))
        self.g.add((uri_fco, self.NS_GME.name, Literal(fco.name)))
        self.g.add((uri_fco, self.NS_GME.parent, self.NS_MODEL['id_' + str(fco.parent.id)]))

        for child in fco.children():
            self.visit(child)

        if fco.type.name in self._assoc_class_names:
            src_attr = getattr(fco, 'src' + fco.type.name)
            dst_attr = getattr(fco, 'dst' + fco.type.name)

            src_uri = self.NS_MODEL['id_' + str(src_attr.id)]
            dst_uri = self.NS_MODEL['id_' + str(dst_attr.id)]

            self.g.add((uri_fco, self.NS_METAMODEL['src' + fco.type.name], src_uri))
            self.g.add((uri_fco, self.NS_METAMODEL['dst' + fco.type.name], dst_uri))

        # Attributes
        if fco.type.name in self._class_attributes:
            for attr in self._class_attributes[fco.type.name]:
                attr_attr = getattr(fco, attr)
                self.g.add((uri_fco, self.NS_METAMODEL[attr], Literal(attr_attr)))
