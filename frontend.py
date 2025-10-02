import json
import os

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

VIDEO_BASE = Path("/mnt/storage/cctvnet")

st.set_page_config(page_title="Wyndhurst CCTV Network Dashboard", layout="wide")

count = st_autorefresh(interval=60*10 * 1000, limit=100, key="refresh")

# Title with subtitle
st.title("Wyndhurst CCTV Network Dashboard")
st.caption("Monitor storage usage, timelapses, and CCTV health at a glance.")
if st.button("Refresh"):
    st.rerun()

st.markdown("### File Browser")

# Styled link that looks like a button and opens in a new tab
st.markdown(
    """
    <a href="http://localhost:8502" target="_blank" style="text-decoration:none">
        <button style="
            background-color: #0099ff;
            color: white;
            border: none;
            padding: 0.5em 1em;
            font-size: 1em;
            border-radius: 4px;
            cursor: pointer;
        ">
            Open File Browser
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

# --- GitHub Project Links ---
st.markdown("### Project Repositories")
st.markdown(
    """
    [Documentation](https://uob.sharepoint.com/:f:/r/teams/grp-bvs-johnoldacrecentre/Shared%20Documents/AI%20Group/documentation?csf=1&web=1&e=xyZzt2)  
    
    Here are the related GitHub repositories for this project:

    - [Wyndhurst CCTV Network](https://github.com/biospi/WyndhurstCCTVNet)  
    - [Wyndhurst Farm PC](https://github.com/biospi/WyndhurstFarmPC)  
    - [CCTV Simulation](https://github.com/biospi/WhyndhurstCCTVSimulation)  
    - [Video Downloader](https://github.com/biospi/WyndhurstVideoDownload)  
    - [BBSRC Annotation Tool](https://github.com/biospi/BBSRC_Annotation_tool)  
    """,
    unsafe_allow_html=True,
)

# --- Disk Usage Graphs ---
st.markdown("## 📊 Disk Usage Overview")

with open("logs/disk_usage.json") as f:
    disk_data = json.load(f)


def to_gb(size_str):
    if size_str.endswith("T"):
        return float(size_str[:-1]) * 1024
    elif size_str.endswith("G"):
        return float(size_str[:-1])
    elif size_str.endswith("M"):
        return float(size_str[:-1]) / 1024
    else:
        return float(size_str)


def parse_df_output(df_text, target_mounts=None):
    results = {}
    lines = df_text.strip().splitlines()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 6:
            fs, size, used, avail, percent, mount = parts[:6]
            if (target_mounts and mount in target_mounts) or (not target_mounts and mount == "/"):
                size_gb, used_gb, avail_gb = to_gb(size), to_gb(used), to_gb(avail)
                try:
                    pct = float(percent.strip("%"))
                except:
                    pct = (used_gb / size_gb * 100) if size_gb > 0 else 0
                results[mount] = {
                    "size": size_gb, "used": used_gb, "avail": avail_gb, "percent": pct
                }
    return results


# Extract disk usage
local_usage = parse_df_output(disk_data["joc1_server"], ["/mnt/storage", "/mnt/usb_storage"])
dev_usage = parse_df_output(disk_data["dev_server"], ["/mnt/storage", "/mnt/usb_storage"])
farm_usage = parse_df_output(disk_data["farm_server"])  # just "/"


def gb_to_tb_str(val_gb, decimals=2):
    return f"{val_gb/1024:.{decimals}f} TB"

def plot_pie(stats, title):
    fig, ax = plt.subplots(figsize=(2.5, 2.5))
    ax.pie(
        [stats["used"], stats["avail"]],
        labels=[f"Used {stats['percent']:.0f}%", "Free"],
        autopct="%1.0f%%",
        startangle=90,
        colors=["#ff6666", "#66b3ff"],
        textprops={'fontsize': 8}
    )
    ax.set_title(title, fontsize=10)
    st.pyplot(fig)


# --- Single row with all pies ---
cols = st.columns(5)

with cols[0]:
    plot_pie(local_usage["/mnt/storage"], f"Joc1 Main Storage ({gb_to_tb_str(local_usage['/mnt/storage']['size'])})")
with cols[1]:
    plot_pie(local_usage["/mnt/usb_storage"], f"Joc1 USB Storage ({gb_to_tb_str(local_usage['/mnt/usb_storage']['size'])})")
with cols[2]:
    plot_pie(dev_usage["/mnt/storage"], f"Dev Main Storage ({gb_to_tb_str(dev_usage['/mnt/storage']['size'])})")
with cols[3]:
    plot_pie(dev_usage["/mnt/usb_storage"], f"Dev USB Storage ({gb_to_tb_str(dev_usage['/mnt/usb_storage']['size'])})")
with cols[4]:
    mount, stats = next(iter(farm_usage.items()))
    plot_pie(stats, f"Farm PC ({gb_to_tb_str(farm_usage['/']['size'])})")


# --- Daily storage chart ---
df = pd.read_csv("all_videos.csv")  # or query live data
df["date"] = pd.to_datetime(df["s_dates"], format="%Y%m%dT%H%M%S")
daily = df.groupby(df["date"].dt.date)["FileSizeGB"].sum()

fig, ax = plt.subplots()
daily.plot(ax=ax, title="Daily Storage Usage (GB)")
# st.pyplot(fig)

# --- Images and videos ---
st.markdown("### Storage Calendar")
st.image("/home/fo18103/PycharmProjects/Wyndhurst/daily_storage_calendar.png", caption="Calendar view of daily storage")

st.markdown("### Storage Snapshot")
st.image("/home/fo18103/PycharmProjects/Wyndhurst/storage/storage.png",
         caption="Latest storage snapshot")

st.markdown("### Timelapse")
timelapse_file = list(Path("timelapse").rglob("*.mp4"))
st.video(timelapse_file[0])

st.markdown("### Last CCTV Map")
map_file = list(Path("map").rglob("*.jpg"))
st.image(map_file[0], caption="Most recent frame captured")

# --- Thumbnails ---
st.markdown("### All Thumbnails")
thumbnails = sorted(list(Path("hd").rglob("*.jpg")))
full_paths = [thumb.resolve() for thumb in thumbnails]

num_cols = 10
cols = st.columns(num_cols)

for i, thumb in enumerate(thumbnails):
    col = cols[i % num_cols]
    with col:
        st.caption(f"{thumb.stem}")
        st.image(thumb, width='stretch')



# --- Map view ---
st.markdown("### CCTV Location")
st.map(pd.DataFrame({"lat": [51.341726], "lon": [-2.777592]}))


