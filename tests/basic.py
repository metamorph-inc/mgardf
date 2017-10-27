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

    @staticmethod
    def pathMga():
        return r'C:\Users\Adam\repo\tto-robotics\centipede\TASCK_Centipede.mga'

    @staticmethod
    def pathUdmXml():
        return r'C:\Users\Adam\repo\tonka\generated\CyPhyML\models\CyPhyML_udm.xml'

    @classmethod
    def setUpClass(cls):
        # Load the MGA. Let's only do this once okay?
        path_gme = os.path.join(r'C:\Program Files (x86)\GME')
        path_sf_udm = os.path.join(path_gme, r'Paradigms\SF\SF.xml')
        cls.path_sf_udm = path_sf_udm

        path_mga = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\sf.mga')

        # need to open meta DN since it isn't compiled in
        uml_diagram = udm.uml_diagram()
        meta_dn = udm.SmartDataNetwork(uml_diagram)
        meta_dn.open(path_sf_udm.encode("utf-8"), b"")
        dn = udm.SmartDataNetwork(meta_dn.root)
        dn.open(path_mga.encode("utf-8"), b"")

        cls.dn = dn
        cls.dn_root = dn.root

    @classmethod
    def tearDownClass(cls):
        cls.dn.close_no_update()

    def test_absolute_truth_and_meaning(self):
        g = MgaRdfConverter.convert(self.dn_root, udm_xml=self.path_sf_udm)
        print(g.serialize(format='turtle'))


if __name__ == '__main__':
    unittest.main()
