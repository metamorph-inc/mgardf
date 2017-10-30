# -*- coding: utf-8 -*-

from mgardf.mgardfconverter import MgaRdfConverter
import unittest
import os
from utilities import xme2mga
import udm


class ElementTypesTestSuite(unittest.TestCase):
    """Test cases for each MetaGME type."""

    PATH_GME = r'C:\Program Files (x86)\GME'
    PATH_MGA = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            r'models\generic_language\gl_test_model.mga')
    PATH_XME = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            r'models\generic_language\gl_test_model.xme')
    PATH_UDM_XML = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                r'models\generic_language\generic_language_udm.xml')

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

    def test_reference_target(self):
        sparql_ref_and_referent = """
            PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
            PREFIX gl: <http://www.metamorphsoftware.com/openmeta/>

            SELECT ?ref ?referent
            WHERE {
                ?ref a gl:Reference .
                ?ref gme:parent ?parent .
                ?parent gme:name "RootModel" .
                
                ?ref gme:references ?referent .
                ?referent gme:name "Atom"
            }
        """

        res = self.g.query(sparql_ref_and_referent)
        self.assertEqual(1, len(res))
        for row in res:
            print (row)


if __name__ == '__main__':
    unittest.main()
