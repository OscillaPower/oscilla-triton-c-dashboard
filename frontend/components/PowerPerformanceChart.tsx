import * as React from "react";

import { useTheme } from "@mui/material/styles";

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";

export interface PowerPerformanceData {
  name: string; // Timestamp as string
  "PTO Bow kW": number;
  "PTO Stbd kW": number;
  "PTO Port kW": number;
  "Total Power kW": number;
}

interface IndividualPowerPerformanceChartProps {
  data: [PowerPerformanceData];
  dataKey: string;
  title: string;
  color: string;
}

function IndividualPowerPerformanceChart(
  props: IndividualPowerPerformanceChartProps
) {
  const theme = useTheme();
  return (
    <Box flexDirection="row" justifyContent="center" alignItems="center">
      <Box sx={{ display: "flex" }}>
        <ResponsiveContainer width="100%" height={50}>
          <LineChart
            data={props.data}
            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          >
            <Line
              type="monotone"
              dataKey={props.dataKey}
              stroke={props.color}
              dot={false}
            />
            <Tooltip
              labelStyle={{ fontFamily: theme.typography.fontFamily }}
              itemStyle={{ fontFamily: theme.typography.fontFamily }}
              formatter={(value) => `${value} kW`}
              isAnimationActive={false}
            />
            <YAxis
              type="number"
              domain={[0, "dataMax + 100"]}
              tickCount={0}
              width={0}
            />
            <XAxis dataKey="name" hide={true} />
          </LineChart>
        </ResponsiveContainer>
      </Box>
      <Box sx={{ display: "flex" }}>
        <Typography variant="subtitle1" textAlign="left">
          {props.title}
        </Typography>
      </Box>
    </Box>
  );
}

interface PowerPerformanceChartProps {
  data: [PowerPerformanceData];
  totalPowerOnly?: boolean;
}

export default function PowerPerformanceChart(
  props: PowerPerformanceChartProps
) {
  const timeframeString = `${props.data?.at(0)?.name} - ${
    props.data.at(-1)?.name
  }`;
  return (
    <Paper sx={{ padding: 3 }} elevation={0}>
      <Box sx={{ display: "flex", flexDirection: "column" }}>
        <Typography variant="overline" textAlign="left" fontWeight="bold">
          PTO Power Timeseries
        </Typography>
        <Typography variant="caption" textAlign="left">
          {timeframeString}
        </Typography>
      </Box>
      <IndividualPowerPerformanceChart
        data={props.data}
        dataKey="Total Power kW"
        title="Total Power (kW)"
        color="#8884d8"
      />
      {props.totalPowerOnly == true ? null : (
        <>
          <IndividualPowerPerformanceChart
            data={props.data}
            dataKey="PTO Bow kW"
            title="PTO Bow Power (kW)"
            color="#D32F2F"
          />
          <IndividualPowerPerformanceChart
            data={props.data}
            dataKey="PTO Port kW"
            title="PTO Port Power (kW)"
            color="#1976D2"
          />
          <IndividualPowerPerformanceChart
            data={props.data}
            dataKey="PTO Stbd kW"
            title="PTO Starboard Power (kW)"
            color="#388E3C"
          />
        </>
      )}
    </Paper>
  );
}
