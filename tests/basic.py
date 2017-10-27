# -*- coding: utf-8 -*-

# from .context import mgardf
from mgardf.mgardfconverter import MgaRdfConverter
import unittest
import _winreg as winreg
import os
import sys

with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\META") as software_meta:
    meta_path, _ = winreg.QueryValueEx(software_meta, "META_PATH")
sys.path.append(os.path.join(meta_path, 'bin'))
import udm


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    PATH_GME = r'C:\Program Files (x86)\GME'
    # PATH_MGA = r'C:\Users\Adam\repo\tto-robotics\centipede\TASCK_Centipede.mga'
    PATH_MGA = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\sf.mga')
    # PATH_UDM_XML = r'C:\Users\Adam\repo\tonka\generated\CyPhyML\models\CyPhyML_udm.xml'
    PATH_UDM_XML = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\SF.xml')

    @classmethod
    def setUpClass(cls):
        # Load the MGA and UDM. Let's only do this once okay?

        uml_diagram = udm.uml_diagram()
        meta_dn = udm.SmartDataNetwork(uml_diagram)
        meta_dn.open(BasicTestSuite.PATH_UDM_XML.encode("utf-8"), b"")
        cls.meta_dn = meta_dn

        dn = udm.SmartDataNetwork(meta_dn.root)
        dn.open(BasicTestSuite.PATH_MGA.encode("utf-8"), b"")
        cls.dn = dn

        cls.g = MgaRdfConverter.convert(dn.root, udm_xml=BasicTestSuite.PATH_UDM_XML)

        print(cls.g.serialize(format='turtle'))

        cls.dn.close_no_update()
        cls.meta_dn.close_no_update()

    @classmethod
    def tearDownClass(cls):
        pass

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
        self.assertEqual(10, len(res))
        for row in res:
            self.assertIn(str(row[0]), ['Primitive', 'PrimitiveParts'])

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
            
            SELECT ?comp_descendant ?cd_name
            WHERE {
                ?comp a sf:Compound .
                ?comp sf:name "Compound_Instance" .
                
                ?comp_descendant gme:parent+ ?comp .
                ?comp_descendant a gme:instance
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
            
            SELECT ?comp_descendant ?cd_name
            WHERE {
                ?comp a sf:Compound .
                ?comp sf:name "Compound_Subtype" .
                
                ?comp_descendant gme:parent+ ?comp .
                ?comp_descendant a gme:subtype
            }
        """

        res = self.g.query(sparql_all_descendants)
        self.assertEqual(18, len(res))


if __name__ == '__main__':
    unittest.main()
