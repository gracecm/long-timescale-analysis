# %%
from pathlib import Path

import dill
import h5py
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.style

# %%
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import patches
from matplotlib.patches import Circle
from scipy.io import loadmat

# %%
# %matplotlib inline


mpl.rcParams["figure.facecolor"] = "w"
mpl.rcParams["figure.dpi"] = 150
mpl.rcParams["savefig.dpi"] = 600
mpl.rcParams["savefig.transparent"] = True
mpl.rcParams["font.size"] = 15
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
mpl.rcParams["axes.titlesize"] = "xx-large"  # medium, large, x-large, xx-large

mpl.style.use("seaborn-deep")

# %%
from itertools import groupby


def encode_list(s_list):
    return [[len(list(group)), key[0]] for key, group in groupby(s_list)]


# %%
import sys

sys.path.append("../")
import analysis.utils.trx_utils as trx_utils

# %%
nn_filename = "/Genomics/ayroleslab2/scott/long-timescale-behavior/data/organized_tracks/20220217-lts-cam1/cam1_20220217_0through190_cam1_20220217_0through190_1-tracked.analysis.h5"
filename = "/Genomics/ayroleslab2/scott/git/lts-manuscript/analysis/20220217-lts-cam1_day1_24hourvars.h5"
import h5py
import numpy as np

with h5py.File(nn_filename, "r") as f:
    dset_names = list(f.keys())
    locations = f["tracks"][:].T
    node_names = [n.decode() for n in f["node_names"][:]]

with h5py.File(filename, "r") as f:
    locations = f["tracks"][:].T

z_vals_file = "/Genomics/ayroleslab2/scott/git/lts-manuscript/analysis/mmpy_lts_1d_subset/TSNE/zVals_wShed_groups.mat"
with h5py.File(z_vals_file, "r") as f:
    z_val_names_dset = f["zValNames"]
    references = [
        f[z_val_names_dset[dset_idx][0]]
        for dset_idx in range(z_val_names_dset.shape[0])
    ]
    z_val_names = ["".join(chr(i) for i in obj[:]) for obj in references]
    z_lens = [l[0] for l in f["zValLens"][:]]

d = {}
for z_val_name_idx, _ in enumerate(z_val_names):
    d[z_val_names[z_val_name_idx]] = [
        np.sum(z_lens[:(z_val_name_idx)]),
        np.sum(z_lens[: (z_val_name_idx + 1)]),
    ]
d[z_val_names[0]][0] = 0


print("===filename===")
print(filename)
print()

print("===HDF5 datasets===")
print(dset_names)
print()

print("===locations data shape===")
print(locations.shape)
print()

print("===nodes===")
for i, name in enumerate(node_names):
    print(f"{i}: {name}")
print()

# filtered_locations = trx_utils.fill_missing_np(locations)
# filtered_locations = trx_utils.smooth_median(filtered_locations)
# filtered_locations = trx_utils.smooth_gaussian(filtered_locations)
filtered_locations = locations
# %%
import importlib

importlib.reload(trx_utils)

# %%
videofile = "/Genomics/ayroleslab2/scott/long-timescale-behavior/data/organized_videos/20220217-lts-cam1/20220217-lts-cam1-0000.mp4"
min_length = 25
with h5py.File(
    "/Genomics/ayroleslab2/scott/git/lts-manuscript/analysis/mmpy_lts_1d_subset/TSNE/zVals_wShed_groups.mat"
) as f:
    for fly_idx in range(4):
        fly_id_mm = fly_idx
        fly_id_trx = fly_idx
        rle_list = encode_list(
            f["watershedRegions"][
                d[f"20220217-lts-cam1_day1_24hourvars-{fly_id_mm}-pcaModes"][0] : d[
                    f"20220217-lts-cam1_day1_24hourvars-{fly_id_mm}-pcaModes"
                ][1]
            ]
        )
        dict_rle = {
            "number": [p[1] for p in rle_list],
            "length": [p[0] for p in rle_list],
        }
        df = pd.DataFrame(dict_rle)
        # Get the end
        df["end"] = np.cumsum(df.length)
        # Get the start
        df["start"] = df["end"] - df.length
        _, angles = trx_utils.normalize_to_egocentric(
            filtered_locations[:, :, :, fly_id_trx],
            ctr_ind=node_names.index("thorax"),
            fwd_ind=node_names.index("head"),
            return_angles=True,
        )
        Path("analysis/brady50").mkdir(parents=True, exist_ok=True)
        for region in range(0, np.unique(f["watershedRegions"][:]).shape[0]):
            try:
                subset = df[
                    (df.number == region) & (df.end < 360000) & (df.length >= 10)
                ].sort_values(by=["length"], ascending=False)[0:3]
                for section in subset.iterrows():
                    print(section)
                    start = section[1]["start"]
                    end = section[1]["end"]
                    print(f"Frames: {start},{end}")
                    try:
                        trx_utils.plot_ego(
                            output_path=f"analysis/brady50/tsne-fly{fly_id_mm}-region{region}-frames{start}to{end}.mp4",
                            tracks=filtered_locations,
                            fly_ids=[fly_id_trx],
                            video_path=videofile,
                            angles=angles,
                            frame_start=start,
                            frame_end=min(end, start + 100),
                            trail_length=10,
                        )
                    except:
                        print(f"Failed to plot {start},{end}")
            except Exception as e:
                print(f"Failed to plot region {region}")
                print(e)

    # %%
