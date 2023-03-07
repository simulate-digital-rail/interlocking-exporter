# Purpose
This module can be used to generate the necessary data for the Interlocking UI. It provides the methods `export_topology()`, `export_placement()` and `export_routes()` on the `Exporter` class.


Simple example to export Potsdam Hbf
```python
import json
from orm_importer.importer import ORMImporter
from interlocking_ui_exporter.exporter import Exporter

polygon = "52.389626549040095 13.069975376129152 52.39248124796051 13.070275783538818 52.39410493928074 13.054568767547607 52.39134200952107 13.05426836013794"  

topology = ORMImporter().run(polygon)

for node in topology.nodes.values():
    if len(node.connected_nodes) > 1:
        node.calc_anschluss_of_all_nodes()

exporter = Exporter(topology)
topology = exporter.export_topology()
placement = exporter.export_placement()
routes = exporter.export_routes()

print(json.dumps(topology))
print()
print(json.dumps(placement))
print()
print(json.dumps(routes))

```
