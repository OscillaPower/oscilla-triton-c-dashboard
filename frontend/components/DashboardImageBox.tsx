import * as React from "react";

import Image from "next/image";

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

interface DashboardImageBoxProps {
  title: string;
  imageURL: string;
}

export default function DashboardImageBox(props: DashboardImageBoxProps) {
  const fallbackSrc = "/img/no_data.png";
  // These are a best guess
  const fallbackDim = { height: 15, width: 18 };

  const [imgSrc, setImgSrc] = React.useState(props.imageURL);
  const [imgDim, setImgDim] = React.useState({ height: 100, width: 100 });

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
        height={`${imgDim.height}vh`}
        width={`${imgDim.width}vw`}
      >
        <Image
          src={imgSrc}
          alt={props.title}
          fill
          onError={() => {
            setImgSrc(fallbackSrc);
            setImgDim(fallbackDim);
          }}
        />
      </Box>
      <Box>
        <Typography variant="overline">{props.title}</Typography>
      </Box>
    </Box>
  );
}
