import * as React from "react";

import {
  AttributionControl,
  Circle,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  Tooltip,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import L from "leaflet";

import Box from "@mui/material/Box";

const WETS_LAT = 21.46505198833667;
const WETS_LNG = -157.75991236826218 - 0.01;

const TRITON_C_EXPECTED_MOORING_LAT = 21.465688877709113;
const TRITON_C_EXPECTED_MOORING_LNG = -157.7506368665354;
const TRITON_C_WATCH_CIRCLE_METERS = 30;

const CDIP_BUOY_225_K_BAY_LAT = 21.4774;
const CDIP_BUOY_225_K_BAY_LNG = -157.75684;

L.Icon.Default.imagePath = "img/";

const attribution =
  'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>';
const attributionPrefix = `Oscilla Power Triton-C | ${new Date().getFullYear()} <a href='www.oscillapower.com'>Oscilla Power</a>`;

interface WECLocationMapProps {
  coords: number[][];
}

export const WECLocationMap = (props: WECLocationMapProps) => {
  let lastUsedLat: number = 0;
  let lastUsedLng: number = 0;

  const currentData = props.coords[0];
  const currentLat = currentData[1];
  const currentLng = currentData[2];

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      position="relative"
      flex={1}
      height="868px"
      width="100%"
    >
      <MapContainer
        center={[currentLat, currentLng]}
        zoom={13}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%" }}
        attributionControl={false}
      >
        <TileLayer
          attribution={attribution}
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <AttributionControl position="bottomright" prefix={attributionPrefix} />

        <Marker position={[CDIP_BUOY_225_K_BAY_LAT, CDIP_BUOY_225_K_BAY_LNG]}>
          <Tooltip permanent={true} interactive={true}>
            Observation Buoy
            <br />
            <a
              href="http://cdip.ucsd.edu/m/products/?stn=225p1"
              target="_blank"
              rel="noreferrer"
            >
              KANEOHE BAY, WETS, HI - 225
            </a>
          </Tooltip>
        </Marker>

        {props.coords.slice(0, 1).map((coord: number[], i: number) => {
          const timestamp = coord[0];
          const lat = coord[1];
          const lng = coord[2];
          // const date = new Date(rawTimestamp);
          // const timestampString = date.toString();

          if ((lastUsedLat !== lat && lastUsedLng !== lng) || i == 0) {
            return (
              <React.Fragment key={lat}>
                <Marker position={[lat, lng]} key={timestamp}>
                  Test
                  <Tooltip permanent>{timestamp}</Tooltip>
                  <Popup>
                    {timestamp}
                    <br />
                    Lat: {lat}
                    <br />
                    Long: {lng}
                  </Popup>
                </Marker>
              </React.Fragment>
            );
          } else {
            return null;
          }
        })}
        <Circle
          center={[
            TRITON_C_EXPECTED_MOORING_LAT,
            TRITON_C_EXPECTED_MOORING_LNG,
          ]}
          radius={TRITON_C_WATCH_CIRCLE_METERS}
        />
      </MapContainer>
    </Box>
  );
};

export default WECLocationMap;
