# A collection of scripts for running Colmap with known camera parameters
[Nathaniel Burgdorfer](https://nburgdorfer.github.io)

## Installation
Please clone the repo:
```bash
git clone git@github.com:nburgdorfer/colmap_scripts.git
```

This library requires Python. We recommend using [conda](https://anaconda.org/) to manage Python environments:
```bash
conda create -n colmap python=3.9.19
```
```bash
conda activate colmap
```

We provide the necessary versions of all required Python packages:
```bash
pip install -r requirements.txt
```

Make sure that colmap is installed:
```bash
git clone https://github.com/colmap/colmap
```

```bash
sudo apt install \
    git \
    cmake \
    ninja-build \
    build-essential \
    libboost-program-options-dev \
    libboost-filesystem-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libgmock-dev \
    libsqlite3-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libceres-dev
```

```bash
git clone https://github.com/colmap/colmap.git
cd colmap
mkdir build
cd build
cmake ..
make -j
sudo make install
```

## Usage
We provide two main scripts; `dtu_sparse_depth.sh` and `tnt_sparse_depth.sh`. Each script is fairly similar and provides all of the necessary steps to run Colmap with known camera parameters for the DTU and TNT datasets. If you would like to add your own dataset, please feel free to copy one of the bash scripts and modify it accordingly. You may also need to modify the `utility.py` file to add I/O functions for your dataset.

We provide some example data from each supported dataset:

- [DTU](https://stevens0-my.sharepoint.com/:u:/g/personal/nburgdor_stevens_edu/ERDdULsQ-j9BmOKIOMM5UCQBSlkfdACGkgvOue0J6yZ3Gw?e=xR9G1w)
- [TNT](https://stevens0-my.sharepoint.com/:u:/g/personal/nburgdor_stevens_edu/EWCKcrdXz39Ir8zHE-EJ_2sB_nNs1B8ycLIQ6cD05uKfTg?e=yswd5j)

The scripts receive as input two arguments:
```bash
./dtu_sparse_depth.sh <path-to-data> <scene>
```

After downloading either dataset, simply run:
```bash
./<dataset>_sparse_depth.sh <path-to-downloaded-data> scan001
```
and example of which being:

```bash
./dtu_sparse_depth.sh /mnt/Data/DTU/ scan001
```
