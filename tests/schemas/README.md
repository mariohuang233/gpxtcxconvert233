These unmodified schemas are test fixtures from Garmin's official definitions:

- https://www8.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd
- https://www8.garmin.com/xmlschemas/ActivityExtensionv2.xsd

Fetched for the project audit on 2026-10-09. `test_converter.py` validates the TCX document and each TPX/LX extension independently, so lax extension handling in the TCX schema does not hide extension errors. The files retain Garmin's original documentation and namespaces.
