import fs from "fs";
import path from "path";

import * as React from "react";

import Head from "next/head";
import Image from "next/image";
import dynamic from "next/dynamic";
import getConfig from "next/config";

import sqlite3 from "sqlite3";

import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";

import { createTheme, ThemeProvider, styled } from "@mui/material/styles";
import AppBar from "@mui/material/AppBar";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

import DashboardImageBox from "../components/DashboardImageBox";
import { GPSCoord } from "../components/WECLocationMap";
import PowerPerformanceChart, {
  PowerPerformanceData,
} from "../components/PowerPerformanceChart";

const Item = styled(Paper)(({ theme }) => ({
  ...theme.typography.body2,
  textAlign: "center",
  padding: theme.spacing(1),
}));

const gridItemHeight = "600px";

const deviceName = "Triton-C";
const title = `${deviceName} Dashboard`;
const description = `Dashboard for ${title} deployed at WETS`;

const theme = createTheme({
  components: {
    MuiTypography: {
      variants: [
        {
          props: { variant: "overline" },
          style: {
            fontSize: "16px",
            letterSpacing: 2,
          },
        },
      ],
    },
  },
});

function WECLocationMap(props: { coords: number[][] }) {
  const Map = dynamic(() => import("../components/WECLocationMap") as any, {
    ssr: false,
  });
  // @ts-ignore
  return <Map coords={props.coords} />;
}

interface HomeProps {
  serverDate: string;
  coords: number[][];
  powerPerformance: [PowerPerformanceData];
}

export default function Home(props: HomeProps) {
  return (
    <ThemeProvider theme={theme}>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static" sx={{ bgcolor: "white", color: "#545356" }}>
          <Grid container={true} spacing={2} margin={1}>
            <Image
              src="/img/oscilla_power_logo.png.webp"
              alt="Oscilla Power Logo"
              width={195}
              height={75}
              priority
              style={{ backgroundColor: "#ffffff", margin: "10px" }}
            />
            <Grid>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Typography
                  component="h1"
                  variant="h4"
                  color="inherit"
                  noWrap
                  sx={{ flexGrow: 1, padding: 1 }}
                >
                  {title}
                </Typography>
              </Box>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Typography
                  component="h1"
                  variant="caption"
                  color="inherit"
                  noWrap
                  sx={{ flexGrow: 1, padding: 1 }}
                >
                  Hawaii Time: {props.serverDate}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </AppBar>
        <Grid
          container
          spacing={1}
          marginTop={1}
          columns={{ xs: 4, sm: 6, md: 12 }}
        >
          <Grid
            container
            item
            spacing={1}
            columns={{ xs: 4, sm: 6, md: 12 }}
            direction="row-reverse"
          >
            <Grid item xs={8}>
              <Paper>
                <WECLocationMap coords={props.coords} />
              </Paper>
            </Grid>
            <Grid item xs={4}>
              <Item>
                <PowerPerformanceChart
                  data={props.powerPerformance}
                  totalPowerOnly={true}
                />
              </Item>
              <Item>
                <a
                  href="http://cdip.ucsd.edu/m/products/?stn=225p1"
                  target="_blank"
                  rel="noreferrer"
                >
                  <img
                    src="http://cdip.ucsd.edu/themes/media/images/plots/buoy_ww3.gd?stn=225&tz=UTC&units=standard"
                    style={{ maxHeight: gridItemHeight }}
                    alt="Wave Conditions at Kaneohe Bay, WETS, HI - 225"
                  />
                </a>
                <div>
                  <Typography variant="overline">
                    Wave Conditions at Kaneohe Bay, WETS, HI - 225
                  </Typography>
                </div>
              </Item>
            </Grid>
          </Grid>
          <Grid
            container
            item
            spacing={1}
            columns={{ xs: 4, sm: 4, md: 4, lg: 12 }}
          >
            <Grid item xs={3}>
              <Item>
                <DashboardImageBox
                  imageURL="/img/viz_latest/Total_Power_kW_power_matrix_latest.svg"
                  title="PTO-All Power Matrix"
                />
              </Item>
            </Grid>
            <Grid item xs={3}>
              <Item>
                <DashboardImageBox
                  imageURL="/img/viz_latest/PTO_Bow_Power_kW_power_matrix_latest.svg"
                  title="PTO-Bow Power Matrix"
                />
              </Item>
            </Grid>
            <Grid item xs={3}>
              <Item>
                <DashboardImageBox
                  imageURL="/img/viz_latest/PTO_Starboard_Power_kW_power_matrix_latest.svg"
                  title="PTO-Starboard Power Matrix"
                />
              </Item>
            </Grid>
            <Grid item xs={3}>
              <Item>
                <DashboardImageBox
                  imageURL="/img/viz_latest/PTO_Port_Power_kW_power_matrix_latest.svg"
                  title="PTO-Port Power Matrix"
                />
              </Item>
            </Grid>
            <Grid item xs={12}>
              <PowerPerformanceChart data={props.powerPerformance} />
            </Grid>
          </Grid>
        </Grid>
      </Box>
    </ThemeProvider>
  );
}

// Server Side Data Request

interface DBRow {
  Timestamp: number;
  Raw_Timestamp: string;
  GPS_Lat: number;
  GPS_Lng: number;
  Is_Deployed: number;
  Is_Maint: number;
  PTO_Bow_Power_kW: number;
  PTO_Starboard_Power_kW: number;
  PTO_Port_Power_kW: number;
  Total_Power_kW: number;
  Mean_Wave_Period: number;
  Mean_Wave_Height: number;
}

const convertDateToHawaiiTime = (date: Date): string => {
  // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/DateTimeFormat#options
  return date.toLocaleString("en-US", { timeZone: "Pacific/Honolulu" });
};

const convertUnixTimestampToHawaiiTime = (unixNsTimestamp: number): string => {
  const date = new Date(unixNsTimestamp / 1000000);
  return convertDateToHawaiiTime(date);
};

const getHawaiiTime = (): string => {
  const date = new Date();
  return convertDateToHawaiiTime(date);
};

export async function getServerSideProps() {
  // Query the server for the current datetime
  // It might make sense to query the canary server to pass this info from the WEC
  const serverDate = new Date();

  // Relevant data is stored in files on the local system. To find this location through docker takes some additional work
  // Based on the environment this finds the "data" folder.
  const nodeEnv = process.env.NODE_ENV || "development";

  const { serverRuntimeConfig } = getConfig();
  const workingDir = serverRuntimeConfig.PROJECT_ROOT;
  let dataDir = path.join(workingDir, "..", "data");

  if (nodeEnv == "production") {
    dataDir = "/home/nrel@oscillapower.local/dashboard/data";
  }

  const db = new sqlite3.Database(dataDir + "/triton_c.db");

  const powerPerformanceQuery =
    "SELECT * from triton_c WHERE Total_Power_kW IS NOT NULL ORDER BY Timestamp DESC LIMIT 500;";
  const gpsQuery =
    "SELECT * from triton_c WHERE GPS_Lat IS NOT NULL AND GPS_Lng IS NOT NULL ORDER BY Timestamp DESC LIMIT 500;";

  const readPowerPerformanceAsync = new Promise(function (resolve, reject) {
    db.all(powerPerformanceQuery, [], (err, rows: DBRow[]) => {
      if (err) {
        reject({ error: err });
      }

      const powerPerformance: PowerPerformanceData[] = [];

      rows.reverse().forEach((row: DBRow) => {
        const niceTimestamp = convertUnixTimestampToHawaiiTime(
          row["Timestamp"],
        );
        powerPerformance.push({
          name: niceTimestamp,
          "PTO Bow kW": row["PTO_Starboard_Power_kW"],
          "PTO Stbd kW": row["PTO_Starboard_Power_kW"],
          "PTO Port kW": row["PTO_Bow_Power_kW"],
          "Total Power kW": row["Total_Power_kW"],
        });
      });

      resolve(powerPerformance);
    });
  });

  const readGPSAsync = new Promise(function (resolve, reject) {
    db.all(gpsQuery, [], (err, rows: DBRow[]) => {
      if (err) {
        reject({ error: err });
      }

      const coords: GPSCoord[] = [];

      // rows.reverse().forEach((row: DBRow) => {
      rows.forEach((row: DBRow) => {
        if (row["GPS_Lat"] !== undefined && row["GPS_Lng"] !== undefined) {
          const niceTimestamp = convertUnixTimestampToHawaiiTime(
            row["Timestamp"],
          );
          coords.push({
            timestamp: niceTimestamp,
            lat: row["GPS_Lat"],
            lng: row["GPS_Lng"],
          });
        }
      });

      resolve(coords);
    });
  });

  const readDBAsync = async function () {
    return Promise.all([readPowerPerformanceAsync, readGPSAsync]).then(
      (values) => {
        return {
          props: {
            serverDate: convertDateToHawaiiTime(serverDate),
            powerPerformance: values[0],
            coords: values[1],
          },
        };
      },
    );
  };

  return readDBAsync();
}
