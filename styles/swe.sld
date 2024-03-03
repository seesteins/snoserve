<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc" version="1.0.0" xmlns:sld="http://www.opengis.net/sld">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>swe</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="ramp">
              <sld:ColorMapEntry opacity="0" label="0" color="#ffffff" quantity="0"/>
              <sld:ColorMapEntry label="12" color="#ffffff" quantity="12"/>
              <sld:ColorMapEntry label="25" color="#cdcdcd" quantity="25"/>
              <sld:ColorMapEntry label="50" color="#beffff" quantity="50"/>
              <sld:ColorMapEntry label="100" color="#4b73ff" quantity="100"/>
              <sld:ColorMapEntry label="200" color="#d700e1" quantity="200"/>
              <sld:ColorMapEntry label="400" color="#ff0000" quantity="400"/>
              <sld:ColorMapEntry label="800" color="#000000" quantity="800"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
</StyledLayerDescriptor>
