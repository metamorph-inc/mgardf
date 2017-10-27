# -*- coding: utf-8 -*-

# from .context import mgardf
from mgardf.mgardfconverter import MgaRdfConverter
import _winreg as winreg
import os
import sys
import time

with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\META") as software_meta:
    meta_path, _ = winreg.QueryValueEx(software_meta, "META_PATH")
sys.path.append(os.path.join(meta_path, 'bin'))
import udm


PATH_GME = r'C:\Program Files (x86)\GME'
PATH_MGA = r'C:\Users\Adam\repo\tto-robotics\centipede\TASCK_Centipede.mga'
PATH_UDM_XML = r'C:\Users\Adam\repo\tonka\generated\CyPhyML\models\CyPhyML_udm.xml'

uml_diagram = udm.uml_diagram()
meta_dn = udm.SmartDataNetwork(uml_diagram)
meta_dn.open(PATH_UDM_XML.encode("utf-8"), b"")
meta_dn = meta_dn

dn = udm.SmartDataNetwork(meta_dn.root)
dn.open(PATH_MGA.encode("utf-8"), b"")

start = time.time()

# cls.g = MgaRdfConverter.convert(dn.root, udm_xml=BasicTestSuite.PATH_UDM_XML)
MgaRdfConverter.convert(dn.root)

end = time.time()
print('Time: {} sec'.format(end - start))

# print(g.serialize(format='turtle'))

dn.close_no_update()
meta_dn.close_no_update()
