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

    @classmethod
    def tearDownClass(cls):
        cls.dn.close_no_update()
        cls.meta_dn.close_no_update()

    def test_absolute_truth_and_meaning(self):
        g = MgaRdfConverter.convert(self.dn.root, udm_xml=BasicTestSuite.PATH_UDM_XML)
        print(g.serialize(format='turtle'))


if __name__ == '__main__':
    unittest.main()
