import time
from pathlib import Path
import configparser
import pandas as pd
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt

from utils import is_float

HIKVISION = [1, 3, 4, 5, 6, 8, 9, 11, 33, 34, 125, 126, 128, 130, 131, 132, 133, 136, 137, 138, 139, 156]

HANWHA = [int(line.strip().split('.')[-1]) for line in open("hanwha.txt")]



def main():
    mp4_files = list(Path("/mnt/storage/scratch/cctv/").rglob("*.mp4"))
    print(f"Found {len(mp4_files)} files.")
    df = pd.DataFrame(mp4_files, columns=['FilePath'])
    df['FileSizeBytes'] = df['FilePath'].apply(lambda x: x.stat().st_size)
    df['FileSizeGB'] = df['FileSizeBytes'] / (1024 ** 3)

    df["dates"] = [x.stem for x in mp4_files]
    dt_format = "%Y%m%dT%H%M%S"
    df["s_dates"] = [datetime.strptime(x.stem.split('_')[0], dt_format) for x in mp4_files]
    df["f_dates"] = [datetime.strptime(x.stem.split('_')[1], dt_format) for x in mp4_files]
    df["ip"] = [x.parent.parent.parent.name if 'videos' in str(x) else x.parent.parent.name for x in mp4_files]
    df = df.sort_values(by=["s_dates", "f_dates"])
    dfs = [group for _, group in df.groupby('ip')]
    data = []
    for df in dfs:
        if not is_float(str(df["ip"].values[0])):
            print(f"skip {df['ip'].values[0]}")
            continue
        df = df.drop(columns=['FilePath'])
        df["dates"] = df['s_dates'].dt.date
        dfs_days = [group for _, group in df.groupby('dates')]
        for df_day in dfs_days:
            day_sum = df_day["FileSizeGB"].sum()
            data.append({"ip": df_day["ip"].values[0], "storage": day_sum, "date": df_day["dates"].values[0]})
    df_data = pd.DataFrame(data)
    print(df_data)
    df_data["ip_id"] = df_data["ip"].str.split('.').str[1].astype(int)
    df_data = df_data[df_data["ip_id"].isin(HIKVISION + HANWHA)]
    df_data['date'] = pd.to_datetime(df_data['date'])

    df_data['brand'] = df_data['ip_id'].apply(lambda x: 'HIKVISION' if x in HIKVISION else 'HANWHA')
    df_data = df_data.sort_values(by=["ip_id", "brand"])

    heatmap_data = df_data.pivot_table(index='ip', columns='date', values='storage')

    heatmap_data.loc["total"] = heatmap_data.sum()
    plt.figure(figsize=(20, 8*2))
    a = HIKVISION + HANWHA
    ip_order = [f"66.{x}" for x in a]
    heatmap_data.index = pd.Categorical(heatmap_data.index, categories=ip_order, ordered=True)
    heatmap_data = heatmap_data.sort_index()

    ax = sns.heatmap(heatmap_data, annot=True, fmt=".0f", cbar_kws={'label': 'Storage (GB)'})
    ax.set_xticklabels(heatmap_data.columns.strftime('%d-%m-%Y'))
    plt.title(f'Storage Usage Heatmap HIKVISION ({len(HIKVISION)}) HANWHA ({len(HANWHA)})')
    plt.xlabel('Date')

    ax.get_yticklabels()[-1].set_label("Total")
    for label in ax.get_yticklabels()[:-1]:
        ip_id = int(label.get_text().split('.')[1])
        if ip_id in HIKVISION:
            label.set_color('blue')
        elif ip_id in HANWHA:
            label.set_color('green')

    plt.ylabel('IP')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("storage.png")



if __name__ == "__main__":
    main()