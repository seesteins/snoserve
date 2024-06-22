# SNOSERVE
SNOSERVE is a library for automatically retrieving and processing SNODAS data and uploading it to a Goeserver Database

## Installation

Pre-requisites:
* A geoserver instance
* 

### Docker

The recommended use of SNOSERVE is through the a docker compose file.
Retrieve the docker

### Bare Metal

SNOSERVE can also be run directly on the system. By 

## USAGE:
### Add to a Caltopo map:
After running the scripts the SNODAS data can be added to your Caltopo for use in trip planning.
#### Add a custom source for both Snowdepth and SWE with the following settings:
Replace {geoserver_host} with the host over your geoserver instance.
##### Snowdepth
Type: WMS
Name: Snowdepth
URL Template: https://{geoserver_host}/geoserver/wms?SERVICE=WMS&?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&BBOX={left},{bottom},{right},{top}&WIDTH={tilesize}&HEIGHT={tilesize}&BGCOLOR=0xCCCCCC&FORMAT=image/png&EXCEPTIONS=application/vnd.ogc.se_inimage&SRS=EPSG:4326&TRANSPARENT=true&LAYERS=SNODAS:snowdepth
Overlay? No - Base Layer
##### SWE
Type: WMS
Name: SWE
URL Template: https://{geoserver_host}/geoserver/wms?SERVICE=WMS&?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&BBOX={left},{bottom},{right},{top}&WIDTH={tilesize}&HEIGHT={tilesize}&BGCOLOR=0xCCCCCC&FORMAT=image/png&EXCEPTIONS=application/vnd.ogc.se_inimage&SRS=EPSG:4326&TRANSPARENT=true&LAYERS=SNODAS:swe
Overlay? No - Base Layer