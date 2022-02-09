# Notes on Data

# Data Summary

## Sample Data

Uploaded manually to Azure Storage 
`az storage blob upload-batch --destination ContainerName --account-name YourAccountName --destination-path DirectoryInBlob --source /path/to/your/data`

This can be found in the `sample_data_upload.sh`

# Rasterframes

## RDPS
Regional Deterministic Prediction System
- [MSC Open Data](https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps_en/)

- Data types
  - TT = air temperature degC
  - PR = precipitation accumulation kg m**-2


- RDPS: [GeoMet](https://wiki.usask.ca/display/MESH/How+to+query+the+Web+Coverage+Service+%28WCS%29+of+GeoMet)

