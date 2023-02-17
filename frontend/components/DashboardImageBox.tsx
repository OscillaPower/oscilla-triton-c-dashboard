import * as React from "react";

import Image from "next/image";

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

interface DashboardImageBoxProps {
  title: string;
  imageURL: string;
}

const height = 100;
const width = 100;

export default function DashboardImageBox(props: DashboardImageBoxProps) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      position="relative"
      flex={1}
      height="400px"
    >
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        position="relative"
        height={`${height}vh`}
        width={`${width}vw`}
      >
        <Image src={props.imageURL} alt={props.title} fill />
      </Box>
      <Box>
        <Typography variant="overline">{props.title}</Typography>
      </Box>
    </Box>
  );
}
