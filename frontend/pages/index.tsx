import fs from "fs";
import path from "path";

import * as React from "react";

import Head from "next/head";
import Image from "next/image";
import dynamic from "next/dynamic";
import getConfig from "next/config";

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
                  Hawaii Time: {getHawaiiTime()}
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
                  imageURL="/img/pto_1_pm_mean_latest.svg"
                  title="PTO-All Power Matrix"
                />
              </Item>
            </Grid>
            <Grid item xs={3}>
              <Item>
                <DashboardImageBox
                  imageURL="/img/pto_1_pm_mean_latest.svg"
                  title="PTO-Bow Power Matrix"
                />
              </Item>
            </Grid>
            <Grid item xs={3}>
              <Item>
                <DashboardImageBox
                  imageURL="/img/pto_2_pm_mean_latest.svg"
                  title="PTO-Starboard Power Matrix"
                />
              </Item>
            </Grid>
            <Grid item xs={3}>
              <Item>
                <DashboardImageBox
                  imageURL="/img/pto_3_pm_mean_latest.svg"
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

const convertDateToHawaiiTime = (date: Date): string => {
  // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/DateTimeFormat#options
  return date.toLocaleString("en-US", { timeZone: "Pacific/Honolulu" });
};

const convertCanaryTimestampToHawaiiTime = (canaryTime: number): string => {
  const date = new Date(canaryTime);
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

  function jsonFileFilter(value: string) {
    const filetype = value.split(".").pop();
    return filetype == "json";
  }

  const gpsCoordsDir = path.join(dataDir, "gps_coords");
  const gpsFiles = fs.readdirSync(gpsCoordsDir);

  // Sort the most recent gps coord files to the to the beginning of the array
  const gpsJsonFiles = gpsFiles.filter(jsonFileFilter).sort().reverse();

  // timestamp, lat, lng
  let coords: number[][] = [[0, 0, 0]];

  for (const gpsFile of gpsJsonFiles) {
    let rawdata = fs
      .readFileSync(path.join(dataDir, "gps_coords", gpsFile))
      .toString();
    let gps_coords = JSON.parse(rawdata);
    coords = gps_coords["data"] as number[][];

    if (coords.length == 0) {
      continue;
    } else if (coords[0][1] == 0) {
      continue;
    } else {
      break;
    }
  }

  // Filter coords to the 50 most recent coordinates
  const selectedCoords = coords.slice(-50, -1).map((row) => {
    return [convertCanaryTimestampToHawaiiTime(row[0]), row[1], row[2]];
  });

  const powerPerformanceDir = path.join(dataDir, "power_performance");
  const powerPerformanceFiles = fs.readdirSync(powerPerformanceDir);

  // Sort the most recent gps coord files to the to the beginning of the array
  const powerPerformanceJsonFiles = powerPerformanceFiles
    .filter(jsonFileFilter)
    .sort()
    .reverse();

  // ["Timestamp","Is_Deployed","Is_Maint","Mean_Wave_Period_Te","Mean_Wave_Height_Hm0","PTO_Bow_Power_kW","PTO_Starboard_Power_kW","PTO_Port_Power_kW","Total_Power"]
  let powerPerformanceData: number[][] = [[]];

  for (const powerPerformanceFile of powerPerformanceJsonFiles) {
    let rawdata = fs
      .readFileSync(path.join(powerPerformanceDir, powerPerformanceFile))
      .toString();
    let rawJson = JSON.parse(rawdata);
    powerPerformanceData = rawJson["data"] as number[][];

    if (powerPerformanceData.length == 0) {
      continue;
    } else {
      break;
    }
  }

  // Filter coords to the 50 most recent coordinates
  const selectedPowerPerformanceData = powerPerformanceData
    .slice(-500, -1)
    .reverse();

  const formattedPowerPerformanceData = selectedPowerPerformanceData.map(
    (row) => {
      // const rowDate = new Date()
      // const timestamp = `${rowDate.toLocaleDateString("haw")} ${rowDate.toLocaleTimeString("haw")}`
      return {
        name: convertCanaryTimestampToHawaiiTime(row[0]),
        "PTO Bow kW": row[5],
        "PTO Stbd kW": row[6],
        "PTO Port kW": row[7],
        "Total Power kW": row[8],
      };
    }
  );

  return {
    props: {
      serverDate: convertDateToHawaiiTime(serverDate),
      coords: selectedCoords,
      powerPerformance: formattedPowerPerformanceData,
    },
  };
}
