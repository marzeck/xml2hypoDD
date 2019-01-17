# xml2hypoDD
Pyrocko based functions to convert quakeML and stationXML datasets to HypoDD formated files and back.
Short description of provided python functions: 
* *quakeml2phaseDD* is used to convert a catalog of earthquake events from quakeMl format to hypoDD input format ("catalog of absolute travel time data, e.g. file phase.dat")
* *stationXML2stationDD* is used to convert a seismic network inventory from stationXML format to hypoDD input format ("station input, e.g. station.dat"
* *reloc2quakeml* is used to convert hypoDD output after relocation (hypoDD.reloc) into an earthquake catalog in quakeML format. Initial hypocenter locations can be taken from original quakeML catalog (event identification performed with "convID.txt" file) or HypoDD output-file "hypoDD.loc".


### Requirements
* python
* [pyrocko](https://pyrocko.org/)

### Input formats
* event catalogs in [quakeML](https://quake.ethz.ch/quakeml/) format
* station information as [stationXML](https://www.fdsn.org/xml/station/)

### Citations

Schorlemmer, D., Euchner, F., Kästli, P., & Saul, J. (2011). QuakeML: status of the XML-based seismological data exchange format. Annals of Geophysics, 54(1), 59-65.

Ahern, T., Casey, R., Barnes, D., Benson, R., Knight, T., & Trabant, C. (2007). SEED Reference Manual, version 2.4. PLACE: Incorporated Research Institutions for Seismology.

Waldhauser, F. (2001). hypoDD--A Program to Compute Double-Difference Hypocenter Locations (hypoDD version 1.0-03/2001). US Geol. Surv. Open File Rep., 01, 113.
