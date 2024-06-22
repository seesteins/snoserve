# snoserve
snoserve is a library for automatically retrieving and processing SNODAS data and uploading it to a Goeserver Database

## Installation

Prerequisites: A geoserver instance is required to make use of snoserve

### Docker

The recommended use of snoserve is through docker.
Documentation on installing docker here: https://docs.docker.com/engine/install/
Be sure to follow the post installation steps: https://docs.docker.com/engine/install/linux-postinstall/
#### Setup
##### Git clone the docker-snoserve repository 
```
git clone --recursive https://github.com/seesteins/docker-snoserve.git
cd docker-snoserve
```
##### Create a .env
Create your .env file with your geoserver information
```
cp example.env .env
nano .env
```
##### Add a workspace to your Geoserver instance
Add a workspace to your geoserver with a name and namespace of "SNODAS"
This is future work and a step to be removed.
##### Start docker-snoserve
Pull and setup a snoserve docker container. Snoserve will run once and then exit
```
docker compose up -d
```
##### Setup a cron job to run daily when SNODAS data is uploaded
SNODAS data is uploaded daily at around 9:15 AM Eastern Time. It takes time to process so I'd recommend running snoserve daily at 9:20 AM Eastern Time. Daylight savings time is observed by SNODAS so it would be prudent to run this on a system that also observes it.

Open crontab using  your editor of choice with `crontab -e` and add the following line. Be sure to adjust the time (minutes, hours, days, months, years) to the time of your server. Ensure that the directory matches that of your docker-snoserve repository that you pulled.
```
20 9 * * * cd ~/docker/docker-snoserve && docker compose up -d
```
### Add to a Caltopo map:
After running snoserve the SNODAS data can be added to your Caltopo for use in trip planning.
#### Add a custom source for both Snowdepth and SWE with the following settings:
Replace {geoserver_host} with the host of your geoserver instance.
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

Note that this requires your geoserver instance to be exposed to the internet. Cloudflare tunnels and Tailscale Funnels could be a place to start looking at this. Be sure to secure your server: https://github.com/imthenachoman/How-To-Secure-A-Linux-Server
## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
