from pathlib import Path
from dewarp import Defisheye
from farm_map import build_map


def main(out = "dewarp"):
    dtypes = ['orthographic', 'linear', 'equalarea', 'stereographic']
    formats = ['circular']
    fov = 180
    # thumbnails = list(Path("hd").rglob("*.jpg"))
    thumbnails = [Path("/mnt/storage/thumbnails/masks/45_mask.png"), Path("/mnt/storage/thumbnails/360/45.jpg")]

    results = []
    for thumbnail in thumbnails:
        # if int(thumbnail.stem) not in [52, 53, 141, 50, 49, 47, 45, 46, 54, 48, 39, 43, 41, 38, 44, 37, 40, 35, 42, 36]:
        #     continue

        print(thumbnail)
        for format in formats:
            for dtype in dtypes:
                for pfov in [175, 170, 160, 150, 130, 120, 110, 100, 90]:
                    x = None
                    y = None
                    a = -0.5  #

                    out_dir = Path(out) / Path(f"dewarp_{dtype}") / f"{pfov}"
                    out_dir.mkdir(parents=True, exist_ok=True)

                    img_out = out_dir / f"{thumbnail.name}"
                    print(img_out)

                    obj = Defisheye(thumbnail.as_posix(), dtype=dtype, format=format, fov=fov,
                                    pfov=pfov, xcenter=x, ycenter=y, angle=a, crop_left=0,
                                    crop_right=0, crop_top=0, crop_bottom=0)
                    obj.convert(img_out)
                    results.append(out_dir)
    return results
        # for format in formats:
        #     for dtype in dtypes:
        #         pfov = 120
        #         img_out = out_dir / f"{thumbnail.name}"
        #         a = -0.4  #
        #         crop_left = 220
        #         crop_top = 250
        #         crop_right = crop_left
        #         crop_bottom = 200
        #         obj = Defisheye(thumbnail.as_posix(), dtype=dtype, format=format, fov=fov, pfov=pfov, angle=a, crop_left=crop_left,
        #                         crop_right=crop_right,
        #                         crop_top=crop_top,
        #                         crop_bottom=crop_bottom)
        #         obj.convert(img_out)
        #         print(img_out)


if __name__ == "__main__":
    dirs = main()
    #dirs = [p for p in Path("dewarp").iterdir() if p.is_dir()]
    # for d in dirs:
    #     out_dir = d.parent / "map"
    #     out_dir.mkdir(parents=True, exist_ok=True)
    #     build_map(image_dir=d, map_dir = out_dir, tag=d.stem)
