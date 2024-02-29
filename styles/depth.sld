<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.0.0" xmlns:gml="http://www.opengis.net/gml" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>depth</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="ramp">
              <sld:ColorMapEntry quantity="0" opacity="0" label="0 mm" color="#ffffff"/>
              <sld:ColorMapEntry quantity="1" label="1 mm" color="#ffffff"/>
              <sld:ColorMapEntry quantity="125" label="125 mm" color="#cccccc"/>
              <sld:ColorMapEntry quantity="250" label="250 mm" color="#bbffff"/>
              <sld:ColorMapEntry quantity="500" label="500 mm" color="#477fff"/>
              <sld:ColorMapEntry quantity="1000" label="1000 mm" color="#d700de"/>
              <sld:ColorMapEntry quantity="2000" label="2000 mm" color="#ff0000"/>
              <sld:ColorMapEntry quantity="4000" label="4000 mm" color="#000000"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
</StyledLayerDescriptor>
