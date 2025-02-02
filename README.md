# Oscilla Power Triton-C Dashboard

2024-09-19

- [Overview](#overview)
- [Contacts:](#contacts)
- [Flow](#flow)
- [Example Power Matrix](#example-power-matrix)
- [Architecture](#architecture)
  - [Frontend](#frontend)
  - [Backend](#backend)
  - [Packaging](#packaging)
- [Building and Running](#building-and-running)
  - [Frontend](#frontend-1)
    - [Backend](#backend-1)
    - [Visualization](#visualization)

# Overview

The [Oscilla Power Triton-C](https://www.oscillapower.com/triton-c) is a
prototype 100 kW Wave Energy Converter (WEC) planned to deploy at the
[U.S. Navy Wave Energy Test Site
(WETS)](https://tethys.pnnl.gov/project-sites/us-navy-wave-energy-test-site-wets#:~:text=deploying%20at%20WETS.-,Location,'ahu%2C%20Hawai'i.)
sometime in 2023. In order to better understand the power performance of
the WEC, NREL is building a dashboard to visualize power performance and
wave conditions for the duration of the device deployment. Onboard the
WEC is some type of data acquisition system that saves data using
[Canary Labs](https://www.canarylabs.com/) software. The code in this
repository interfaces with the WEC Canary server, saves data offline,
and builds power performance visualizations which are displayed in a web
application.

![[Oscilla Power Triton-C
Dashboard](http://10.1.10.29/)](./docs/img/dashboard_above_the_fold.png)

# Contacts:

- Andrew Simms: andrew.simms@nrel.gov
- Rebecca Fao: rebecca.fao@nrel.gov

# Flow

``` mermaid
flowchart LR
    MHKiTWave[MHKiT Wave]
    MHKiTPower[MHKiT Power]

    WMI --> CDIP -->|Spectra| MHKiTWave -->|QOI| DB

    subgraph Dashboard
        direction TB
        PTO[PTO Timeseries]
        GPS[GPS Location]
        WaveConditions[Wave Conditions]
        PowerMat[Power Matrix Visualizations]
    end

    WEC --> Canary <--> Server --> DB
    DB --> PTO
    DB --> GPS
    CDIP --> WaveConditions
    DB --> MHKiTPower --> PowerMat

```

# Example Power Matrix

![Example Power Matrix](./frontend/public/img/pto_2_pm_mean_latest.svg)

# Architecture

![Dashboard Architecture](docs/img/architecture.png)

## Frontend

Frontend handles presenting data to the client. Frontend is built with
react.js served through next.js. For simplication we request data server
side using `getServerSideProps` which pulls stored data files from the
local file system.

## Backend

- **`./backend/collect_WEC_data.py`**

  - Query and download data from the WEC via Canary and store it as:
    - Raw JSON in `./data/triton_c/`
    - Structured data in the SQLite database: `./data/triton_c.db`

- **`./backend/collect_spectra_data.py`**

  - Query and download data from CDIP and store it as:
    - Combined NetCDF (`.nc`) file with `waveTime` variables
    - Structured Wave Quality of Interest (QOI) generated from spectra
      in the SQLite database: `./data/triton_c.db`

- **`./backend/build_visualizations.py`**

  - Select ALL power data
    - Calculate averages (hourly?)
    - Calculate averages (hourly?)
  - Select ALL
  - Save output SVG images to: `./frontend/public/img/viz_latest/`

## Packaging

A custom packaging script, `package.py` was written to simplify the
deployment process to Oscilla Power server. Running `python3 package.py`
will produce zip files of each application which can then be copied to
the server, unzipped, and ran with Docker.

# Building and Running

## Frontend

Copy `frontend.zip` to server `dashboard` folder and unzip using
`unzip frontend.zip -d frontend`. `cd` into `frontend` directory and
build and run Docker.

Frontend Docker build command:

``` sh
sudo docker build -t frontend .
```

The local filesystem must be mounted for reading and writing using `-v`.
Port 3000 of the nextjs server is mapped to port 80 of the host machine.

Frontend Docker run command:

``` sh
sudo docker run -dp 80:3000 -v /home/nrel@oscillapower.local/dashboard/data:/home/nrel@oscillapower.local/dashboard/data frontend
```

### Backend

Use conda python `oscilla-dashboard` environment built via the
`./backend/environment.yml` file

``` sh
conda env create -f environment.yml
conda activate oscilla-dashboard
python3 collect_WEC_data.py
```

For simplicity we are using `cron` to run the backend python scripts
periodically. This previously was done with Docker, which is a good idea
but is hard to troubleshoot through all the layers (python \| Conda \|
cron \| container). This could be revisited in the future, but using
cron on the base system seems acceptable.

Config:

``` sh
SHELL=/bin/bash

*/1 * * * * /bin/bash -l -c 'source /home/nrel@oscillapower.local/miniconda3/etc/profile.d/conda.sh && conda activate oscilla-dashboard && python3 /home/nrel@oscillapower.local/dashboard/backend/collect_WEC_data.py >> ~/cron-collect-WEC-data.log 2>&1'
*/20 * * * * /bin/bash -l -c 'source /home/nrel@oscillapower.local/miniconda3/etc/profile.d/conda.sh && conda activate oscilla-dashboard && python3 /home/nrel@oscillapower.local/dashboard/backend/collect_spectra_data.py >> ~/cron-collect-spectra-data.log 2>&1'
*/20 * * * * /bin/bash -l -c 'source /home/nrel@oscillapower.local/miniconda3/etc/profile.d/conda.sh && conda activate oscilla-dashboard && python3 /home/nrel@oscillapower.local/dashboard/backend/build_visualizations.py >> ~/cron-build-visualizations.log 2>&1'
* * * * * /bin/bash -l -c 'date > ~/cron-test.txt'
* * * * * /bin/bash -l -c 'source /home/nrel@oscillapower.local/miniconda3/etc/profile.d/conda.sh && conda activate oscilla-dashboard && which python3 > ~/cron-py-test.txt'
```

Editing:

``` sh
crontab -e
```

Verification/Logging:

Check the following logs:

Verify cron is working:

``` sh
cat ~/cron-test.txt
```

Verify conda python is working:

``` sh
cat ~/cron-py-test.txt
```

Check individual script logs for errors. This is should have full stack
traces if Python is failing in unexpected ways.

``` sh
cat ~/cron-collect-WEC-data.log
```

``` sh
cat ~/cron-collect-spectra-data.log
```

``` sh
cat ~/cron-build-visualizations.log
```

Check the python logs:

``` sh
tail -f ~/dashboard/logs/Triton_C_Backend_Processes.log
```

### Visualization

Run via `./backend/build_visualizations.py`.

Utilizes `mhkit` to build power matricies.

Grabs all available WEC power and WMI summary data, calculates the
hourly? average power data and concats that with the WMI data by
timestamp. Follows [MHKiT Wave
Example](https://mhkit-software.github.io/MHKiT/wave_example.html) to
calculate and generate matplotlib power matrices. Saves these
visualizations to `./frontend/public/img/viz_latest/`.
