# -*- coding: utf-8 -*-

from mgardf.mgardfconverter import MgaRdfConverter
import unittest
import os
import udm
from mgardf.utilities import xme2mga


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    PATH_GME = r'C:\Program Files (x86)\GME'
    PATH_MGA = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\sf.mga')
    PATH_XME = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\sf.xme')
    PATH_UDM_XML = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\SF.xml')

    @classmethod
    def setUpClass(cls):
        # Delete and reimport the SF model
        if os.path.exists(cls.PATH_MGA):
            os.remove(cls.PATH_MGA)
        xme2mga(cls.PATH_XME, cls.PATH_MGA)

        # Load the MGA and UDM. Let's only do this once okay?
        uml_diagram = udm.uml_diagram()
        meta_dn = udm.SmartDataNetwork(uml_diagram)
        meta_dn.open(cls.PATH_UDM_XML.encode("utf-8"), b"")
        cls.meta_dn = meta_dn

        dn = udm.SmartDataNetwork(meta_dn.root)
        dn.open(cls.PATH_MGA.encode("utf-8"), b"")
        cls.dn = dn

        cls.g = MgaRdfConverter.convert(dn.root, udm_xml=cls.PATH_UDM_XML)

        print(cls.g.serialize(format='turtle'))

        cls.dn.close_no_update()
        cls.meta_dn.close_no_update()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_mga_exists(self):
        self.assertTrue(os.path.exists(self.PATH_MGA))

    def test_root_primitive(self):
        sparql_root_primitive = """
            PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
            PREFIX sf: <http://www.metamorphsoftware.com/openmeta/>
            
            SELECT ?prim_name
            WHERE {
                ?rf a sf:RootFolder .
                ?rf sf:name ?rf_name .
                ?prim gme:parent ?rf .
                ?prim a sf:Primitive .
                ?prim gme:name ?prim_name
            }
        """

        res = self.g.query(sparql_root_primitive)
        self.assertEqual(1, len(res))
        for row in res:
            self.assertEqual('Primitive', str(row[0]))

    def test_find_all_primitives(self):
        sparql_all_primitives = """
            PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
            PREFIX sf: <http://www.metamorphsoftware.com/openmeta/>
            
            SELECT ?prim_name
            WHERE {
                ?prim a sf:Primitive .
                ?prim sf:name ?prim_name
            }
        """

        res = self.g.query(sparql_all_primitives)
        self.assertEqual(11, len(res))
        for row in res:
            self.assertIn(str(row[0]), ['Primitive', 'PrimitiveParts', 'Primitive_NotSubtype'])

    def test_instances(self):
        sparql_compound_instance = """
            PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
            PREFIX sf: <http://www.metamorphsoftware.com/openmeta/>
            
            SELECT ?comp
            WHERE {
                ?comp a sf:Compound .
                ?comp sf:name "Compound_Instance" .
                ?comp a gme:instance .
                ?comp gme:archetype ?comp_arch .
                ?comp_arch sf:name "Compound"
            }
        """

        res = self.g.query(sparql_compound_instance)
        self.assertEqual(1, len(res))

        # Test child objects are also instances
        sparql_all_descendants = """
            PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
            PREFIX sf: <http://www.metamorphsoftware.com/openmeta/>
            
            SELECT ?comp_descendant
            WHERE {
                ?comp a sf:Compound .
                ?comp sf:name "Compound_Instance" .
                
                ?comp_descendant gme:parent+ ?comp .
                ?comp_descendant a gme:instance .
                ?comp_descendant gme:archetype ?comp_desc_archetype
            }
        """

        res = self.g.query(sparql_all_descendants)
        self.assertEqual(18, len(res))

    def test_subtypes(self):
        sparql_compound_instance = """
            PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
            PREFIX sf: <http://www.metamorphsoftware.com/openmeta/>
            
            SELECT ?comp
            WHERE {
                ?comp a sf:Compound .
                ?comp sf:name "Compound_Subtype" .
                ?comp a gme:subtype .
                ?comp gme:archetype ?comp_arch .
                ?comp_arch sf:name "Compound"
            }
        """

        res = self.g.query(sparql_compound_instance)
        self.assertEqual(1, len(res))

        # Test child objects are also instances
        sparql_all_descendants = """
            PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
            PREFIX sf: <http://www.metamorphsoftware.com/openmeta/>
            
            SELECT ?comp_descendant
            WHERE {
                ?comp a sf:Compound .
                ?comp sf:name "Compound_Subtype" .
                
                ?comp_descendant gme:parent+ ?comp .
                ?comp_descendant a gme:subtype .
                ?comp_descendant gme:archetype ?comp_desc_archetype
            }
        """

        res = self.g.query(sparql_all_descendants)
        self.assertEqual(18, len(res))

        # Test that Primitive_NotSubtype is not also a subtype
        sparql_new_descendant = """
            PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
            PREFIX sf: <http://www.metamorphsoftware.com/openmeta/>
            
            SELECT ?comp_descendant
            WHERE {
                ?comp_descendant gme:name "Primitive_NotSubtype" .
                ?comp_descendant a gme:subtype
            }
        """

        res = self.g.query(sparql_new_descendant)
        self.assertEqual(0, len(res))


if __name__ == '__main__':
    unittest.main()
