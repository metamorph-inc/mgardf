mgardf
======
.. image:: https://ci.appveyor.com/api/projects/status/github/metamorph-inc/mgardf?svg=true
   :target: https://ci.appveyor.com/project/adamnagel/mgardf

This is a library for converting GME MGA files to RDF. By default it translates only the specified project. If given access to the UDM XML, it can export an RDF version of the language (meta-model) as well.

It's still in the prototype stage, but functional enough to be used for some model-reading tasks. It does not support modification of the model project.

Installation
------------
You can install this package using Python's **pip**:

.. code-block::

   python -m pip install git+git://github.com/metamorph-inc/mgardf.git

Usage
-----
.. code-block::

   python -m mgardf <GME project (.xme or .mga)> <path to UDM XML for language>
   
Example
-------
This example uses the `openmeta-vahana <https://github.com/metamorph-inc/openmeta-vahana>`_ project.

From the **CyPhy_Model** directory, we'll run **mgardf**:

.. code-block::
   
   >python -m mgardf openmeta-vahana.xme "C:\Program Files (x86)\META\meta\CyPhyML_udm.xml"
   INFO:rdflib:RDFLib Version: 4.2.2
   creating a temporary MGA file at c:\users\adam\appdata\local\temp\tmp3idb3o.mga
   RDF exported in TTL format: openmeta-vahana.ttl
   done
   
The generated file, **openmeta-vahana.ttl**, has all of the model content inside, plus a few useful prefixes. In the excerpt, we see entries for two elements, both *PythonWrapper* blocks wrappers in a trade study.

.. code-block:: Turtle

   @prefix gme: <https://forge.isis.vanderbilt.edu/gme/> .
   @prefix model: <http://localhost/model/> .
   @prefix openmeta: <http://www.metamorphsoftware.com/openmeta/> .
   @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
   @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
   @prefix xml: <http://www.w3.org/XML/1998/namespace> .
   @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

   
   model:id_100001069 a openmeta:PythonWrapper ;
       openmeta:PyFilename "scripts\\cruise_power.py" ;
       openmeta:name "CruisePower" ;
       gme:name "CruisePower" ;
       gme:parent model:id_100001066 ;
       gme:path "RootFolder.Testing.ParametricExploration.TiltWingPET.VahanaTiltWingOptimizerPET.CruisePower" .

   model:id_100001101 a openmeta:PythonWrapper ;
       openmeta:PyFilename "scripts\\cruise_power.py" ;
       openmeta:name "CruisePower" ;
       gme:name "CruisePower" ;
       gme:parent model:id_100001099 ;
       gme:path "RootFolder.Testing.ParametricExploration.TiltWingOptimizerPETMassBreakdown.CruisePower" .
       
   (snip)
   
Once we load the RDF into a triplestore database, such as Apache Jena-Fuseki, we can use SPARQL queries to extract specific information. Browsing the TTL file for a few examples helps you get accustomed to the available data and terms.
       
Here's a query to find all of the **Parametric Exploration** models in the project:

.. code-block:: SPARQL
   
   PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
   prefix model: <http://localhost/model/>
   prefix openmeta: <http://www.metamorphsoftware.com/openmeta/>

   SELECT ?pet ?pet_name ?pet_path
   WHERE {
     ?pet a openmeta:ParametricExploration .
     ?pet openmeta:name ?pet_name .
     ?pet gme:path ?pet_path .
   }
   
and partial result:

.. code-block::

   ?pet_name	?pet	?pet_path
   "WHATIFCruiseSpeedTiltWingPET"         <http://localhost/model/id_100000712>	"RootFolder.Testing.ParametricExploration.AdditionalTiltWingPETs.WHATIFCruiseSpeedTiltWingPET"
   "Bayesian5VahanaTiltWingOptimizerPET"  <http://localhost/model/id_100000486>	"RootFolder.Testing.ParametricExploration.Debug.TestBayesianOptimization.Bayesian5VahanaTiltWingOptimizerPET"
   "CalculateTimeAndEnergyRequirements"   <http://localhost/model/id_100000933>	"RootFolder.Testing.ParametricExploration.TiltWingPETOrganized.VahanaTiltWingOptimizerPET.CalculateTimeAndEnergyRequirements"
   "TiltWingPET"                          <http://localhost/model/id_100001064>	"RootFolder.Testing.ParametricExploration.TiltWingPET"
   
Let's modify the query to find all of the **PythonWrapper** elements that are part of the **ParametricExploration** called *"TiltWingPET"* (the primary trade study for that model):

.. code-block:: SPARQL

   PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
   prefix model: <http://localhost/model/>
   prefix openmeta: <http://www.metamorphsoftware.com/openmeta/>

   SELECT *
   WHERE {
     ?pet a openmeta:ParametricExploration .
     ?pet openmeta:name "TiltWingPET" .

     ?block gme:parent+ ?pet .

     ?block a openmeta:PythonWrapper .
     ?block openmeta:name ?block_name .
     ?block gme:path ?block_path .
   }
   
and partial result:

.. code-block:: 
   
   ?block_name	?block_path
   "SimpleMission"   "RootFolder.Testing.ParametricExploration.TiltWingPET.VahanaTiltWingOptimizerPET.SimpleMission"
   "Constraint2"     "RootFolder.Testing.ParametricExploration.TiltWingPET.VahanaTiltWingOptimizerPET.Constraint2"
   "CalculateDOCPerKm"	"RootFolder.Testing.ParametricExploration.TiltWingPET.VahanaTiltWingOptimizerPET.CalculateDOCPerKm"
   "rPropScaled"     "RootFolder.Testing.ParametricExploration.TiltWingPET.VahanaTiltWingOptimizerPET.rPropScaled"
   "PropMass"        "RootFolder.Testing.ParametricExploration.TiltWingPET.VahanaTiltWingOptimizerPET.PropMass"
   
   (snip)
   
We can also do a bit of network analysis. Here, we ask: "Which blocks depend on outputs from other blocks?" This query will capture the immediately-adjacent upstream and downstream analysis blocks in the TiltWing PET.

.. code-block:: SPARQL

   PREFIX gme: <https://forge.isis.vanderbilt.edu/gme/>
   prefix model: <http://localhost/model/>
   prefix openmeta: <http://www.metamorphsoftware.com/openmeta/>
   prefix : <http://localhost/network/>

   CONSTRUCT {
     ?block_downstream :DependsOn ?block_upstream .
     ?block_upstream :Name ?block_upstream_name .
     ?block_downstream :Name ?block_downstream_name .
   }
   WHERE {
     # First, get all pairs of blocks within the TiltWingPET
     ?pet a openmeta:ParametricExploration .
     ?pet openmeta:name "TiltWingPET" .
     ?block_upstream gme:parent+ ?pet .
     ?block_downstream gme:parent+ ?pet .

     # Look for cases where a port of Upstream Block
     #    is connected to a port of Downstream Block
     ?connection openmeta:srcResultFlow ?block_upstream_port .
     ?connection openmeta:dstResultFlow ?block_downstream_port .

     # Get ports from Upstream Block
     ?block_upstream a openmeta:PythonWrapper .
     ?block_upstream_port gme:parent ?block_upstream .
     ?block_upstream openmeta:name ?block_upstream_name .

     # Get ports from Downstream Block
     ?block_downstream a openmeta:PythonWrapper .
     ?block_downstream_port gme:parent ?block_downstream .
     ?block_downstream openmeta:name ?block_downstream_name .
   }
   
and the result:

.. code-block:: Turtle
   
   @prefix :      <http://localhost/network/> .
   @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
   @prefix xml:   <http://www.w3.org/XML/1998/namespace> .
   @prefix openmeta: <http://www.metamorphsoftware.com/openmeta/> .
   @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
   @prefix model: <http://localhost/model/> .
   @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
   @prefix gme:   <https://forge.isis.vanderbilt.edu/gme/> .

   model:id_100001094  :DependsOn  model:id_100001082 , model:id_100001070 ;
           :Name       "Constraint2" .

   model:id_100001075  :DependsOn  model:id_100001068 , model:id_100001069 , model:id_100001070 , model:id_100001081 ;
           :Name       "CanardMass" .

   model:id_100001084  :Name  "MaxTakeoffMassScaled" .

   model:id_100001093  :DependsOn  model:id_100001074 , model:id_100001083 ;
           :Name       "Constraint1" .

   model:id_100001074  :DependsOn  model:id_100001069 , model:id_100001070 , model:id_100001071 , model:id_100001081 ;
           :Name       "ReserveMission" .

   model:id_100001083  :Name  "BatteryMassScaled" .

   model:id_100001098  :DependsOn  model:id_100001070 , model:id_100001081 ;
           :Name       "PropMass" .

   model:id_100001073  :DependsOn  model:id_100001068 , model:id_100001069 , model:id_100001070 , model:id_100001081 ;
           :Name       "WingMass" .

   model:id_100001079  :DependsOn  model:id_100001069 , model:id_100001081 ;
           :Name       "ToolingCost" .

   model:id_100001082  :Name  "MotorMassScaled" .

   model:id_100001069  :DependsOn  model:id_100001068 , model:id_100001081 ;
           :Name       "CruisePower" .

   model:id_100001072  :DependsOn  model:id_100001069 , model:id_100001070 , model:id_100001081 ;
           :Name       "SimpleMission" .

   model:id_100001078  :DependsOn  model:id_100001075 , model:id_100001083 , model:id_100001082 , model:id_100001077 , model:id_100001098 , model:id_100001076 , model:id_100001084 , model:id_100001073 , model:id_100001070 , model:id_100001081 ;
           :Name       "ConfigWeight" .

   model:id_100001081  :Name  "rPropScaled" .

   model:id_100001068  :DependsOn  model:id_100001084 ;
           :Name       "MassToWeight" .

   model:id_100001071  :DependsOn  model:id_100001068 , model:id_100001069 , model:id_100001081 ;
           :Name       "LoiterPower" .

   model:id_100001077  :DependsOn  model:id_100001068 , model:id_100001069 ;
           :Name       "FuselageMass" .

   model:id_100001080  :DependsOn  model:id_100001082 , model:id_100001078 , model:id_100001083 , model:id_100001079 , model:id_100001081 , model:id_100001072 ;
           :Name       "OperatingCost" .

   model:id_100001067  :DependsOn  model:id_100001080 ;
           :Name       "CalculateDOCPerKm" .

   model:id_100001095  :DependsOn  model:id_100001078 , model:id_100001084 ;
           :Name       "Constraint3" .

   model:id_100001070  :DependsOn  model:id_100001068 , model:id_100001069 , model:id_100001081 ;
           :Name       "HoverPower" .

   model:id_100001076  :DependsOn  model:id_100001069 , model:id_100001070 , model:id_100001081 ;
           :Name       "WireMass" .
