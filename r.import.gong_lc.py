#!/usr/bin/env python3
############################################################################
#
# MODULE:       r.import.gong_lc
# AUTHOR(S):    Guido Riembauer
# PURPOSE:      Downloads and imports Gong et al. global land cover raster map
#
# COPYRIGHT:    (C) 2021-2022 by mundialis GmbH & Co. KG and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

# %module
# % description: Downloads and imports Gong et al. global land cover raster map.
# % keyword: raster
# % keyword: import
# % keyword: land cover
# % keyword: classification
# %end

# %option G_OPT_R_OUTPUT
# % required: yes
# % label: Output raster map name for classification map
# %end

# %option G_OPT_M_DIR
# % key: directory
# % required: no
# % multiple: no
# % label: Directory path where to download and temporarily store the data. If not set the data will be downloaded to a temporary directory. The downloaded data will be removed after the import
# %end

# %option G_OPT_MEMORYMB
# %end

# %flag
# % key: r
# % description: Use region resolution instead of input resolution
# %end

import atexit
from itertools import product
import os
import psutil
import shutil
import sys
import wget

import grass.script as grass

rm_files = []
rm_folders = []
rm_rasters = []


def cleanup():
    grass.message(_("Cleaning up..."))
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element="raster")["file"]:
            grass.run_command("g.remove", type="raster", name=rmrast, **kwargs)
    for rmfile in rm_files:
        try:
            os.remove(rmfile)
        except Exception as e:
            grass.warning(_("Cannot remove file <%s>: %s" % (rmfile, e)))
    for folder in rm_folders:
        if os.path.isdir(folder):
            try:
                shutil.rmtree(folder)
            except Exception as e:
                grass.warning(_("Cannot remove dir <%s>: %s" % (folder, e)))


def freeRAM(unit, percent=100):
    """The function gives the amount of the percentages of the installed RAM.
    Args:
        unit(string): 'GB' or 'MB'
        percent(int): number of percent which shoud be used of the free RAM
                      default 100%
    Returns:
        memory_MB_percent/memory_GB_percent(int): percent of the free RAM in
                                                  MB or GB

    """
    # use psutil cause of alpine busybox free version for RAM/SWAP usage
    mem_available = psutil.virtual_memory().available
    swap_free = psutil.swap_memory().free
    memory_GB = (mem_available + swap_free) / 1024.0 ** 3
    memory_MB = (mem_available + swap_free) / 1024.0 ** 2

    if unit == "MB":
        memory_MB_percent = memory_MB * percent / 100.0
        return int(round(memory_MB_percent))
    elif unit == "GB":
        memory_GB_percent = memory_GB * percent / 100.0
        return int(round(memory_GB_percent))
    else:
        grass.fatal(_("Memory unit <%s> not supported" % unit))


def test_memory():
    # check memory
    memory = int(options["memory"])
    free_ram = freeRAM("MB", 100)
    if free_ram < memory:
        grass.warning(
            _("Using %d MB but only %d MB RAM available." % (memory, free_ram))
        )
        options["memory"] = free_ram
        grass.warning(_("Set used memory to %d MB." % (options["memory"])))


def categories_for_discrete_classification(map):
    discrete_classification_coding = {
        "10": "Cropland",
        "20": "Forest",
        "30": "Grassland",
        "40": "Shrubland",
        "50": "Wetland",
        "60": "Water",
        "70": "Tundra",
        "80": "Impervious surface",
        "90": "Bareland",
        "100": "Snow/Ice",
    }
    # category
    category_text = ""
    for class_num, class_text in discrete_classification_coding.items():
        category_text += "%s|%s\n" % (class_num, class_text)
    cat_proc = grass.feed_command("r.category", map=map, rules="-", separator="pipe")
    cat_proc.stdin.write(category_text.encode())
    cat_proc.stdin.close()
    cat_proc.wait()


def get_required_tiles():
    # tiles are of 2 * 2 degrees size
    # the tilename is defined by the lower left corner
    region_dict = grass.parse_command("g.region", flags="lg")
    n_tile = int(float(region_dict["nw_lat"]) - float(region_dict["nw_lat"]) % 2)
    s_tile = int(float(region_dict["sw_lat"]) - float(region_dict["sw_lat"]) % 2)
    e_tile = int(float(region_dict["nw_long"]) - float(region_dict["nw_long"]) % 2)
    w_tile = int(float(region_dict["ne_long"]) - float(region_dict["ne_long"]) % 2)
    required_ns_tiles = list(range(s_tile, n_tile + 1, 2))
    required_ew_tiles = list(range(e_tile, w_tile + 1, 2))
    required_tiles_raw = list(product(required_ns_tiles, required_ew_tiles))
    required_tiles = []
    for tile in required_tiles_raw:
        tilename = "fromglc10v01_{}_{}.tif".format(tile[0], tile[1])
        required_tiles.append(tilename)
    return required_tiles


def main():

    global rm_rasters, rm_folders, rm_files

    pid = str(os.getpid())
    baseurl = "http://data.ess.tsinghua.edu.cn/data/fromglc10_2017v01"
    if options["directory"]:
        download_dir = options["directory"]
        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)
    else:
        download_dir = grass.tempdir()
        rm_folders.append(download_dir)

    tiles = get_required_tiles()
    local_paths = []
    for tile in tiles:
        local_path = os.path.join(download_dir, tile)
        url = os.path.join(baseurl, tile)
        try:
            grass.message(_("Downloading {}...").format(url))
            wget.download(url, local_path)
            local_paths.append(local_path)
            rm_files.append(local_path)
        except Exception as e:
            grass.fatal(_("There was a problem downloading {}: {}").format(url, e))
    grass.message(_("Importing..."))
    grassnames = []
    test_memory()
    for idx, file in enumerate(local_paths):
        outname = "gong_classification_part_{}_{}".format(idx, pid)
        import_kwargs = {
            "input": file,
            "output": outname,
            "extent": "region",
            "memory": options["memory"],
        }
        if flags["r"]:
            import_kwargs["resolution"] = "region"
            import_kwargs["resample"] = "nearest"
        grass.run_command("r.import", **import_kwargs, quiet=True)
        grassnames.append(outname)
        rm_rasters.append(outname)

    if len(grassnames) == 1:
        grass.run_command(
            "g.rename",
            raster="{},{}".format(grassnames[0], options["output"]),
            quiet=True,
        )
    else:
        grass.run_command(
            "r.patch", input=grassnames, output=options["output"], quiet=True
        )

    categories_for_discrete_classification(options["output"])
    grass.message(_("Generated raster map <{}>").format(options["output"]))

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
