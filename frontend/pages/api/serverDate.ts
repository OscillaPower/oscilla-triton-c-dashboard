import type { NextApiRequest, NextApiResponse } from "next";

type DateResponse = {
  serverDate: string;
};

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse<DateResponse>
) {
  const date = new Date();
  res.status(200).json({ serverDate: date.toString() });
}
