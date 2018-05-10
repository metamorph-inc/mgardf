# -*- coding: utf-8 -*-

from mgardf.mgardfconverter import MgaRdfConverter
import os
import sys
import time
import udm

# PATH_MGA = r'C:\Users\Adam\repo\tto-robotics\centipede\TASCK_Centipede.mga'
# PATH_UDM_XML = r'C:\Users\Adam\repo\tonka\generated\CyPhyML\models\CyPhyML_udm.xml'
PATH_MGA = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\sf.mga')
PATH_XME = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\sf.xme')
PATH_UDM_XML = os.path.join(os.path.abspath(os.path.dirname(__file__)), r'models\SF.xml')

uml_diagram = udm.uml_diagram()
meta_dn = udm.SmartDataNetwork(uml_diagram)
meta_dn.open(PATH_UDM_XML.encode("utf-8"), b"")
meta_dn = meta_dn

dn = udm.SmartDataNetwork(meta_dn.root)
dn.open(PATH_MGA.encode("utf-8"), b"")

start = time.time()

# cls.g = MgaRdfConverter.convert(dn.root, udm_xml=BasicTestSuite.PATH_UDM_XML)
# import cProfile
#
# pr = cProfile.Profile()
# pr.enable()
g = MgaRdfConverter.convert(dn.root, udm_xml=PATH_UDM_XML)
# pr.disable()

end = time.time()
print('Time: {} sec'.format(end - start))

# print(g.serialize(format='turtle'))

dn.close_no_update()
meta_dn.close_no_update()

# Let's load our stats file and sort it
# to focus on long-running code and our code specifically
# import StringIO
# import pstats
#
# s = StringIO.StringIO()
# ps = pstats.Stats(pr, stream=s).sort_stats('filename', 'cumulative')
# ps.print_stats()
#
# for line in s.getvalue().split('\n'):
#     print(line)
