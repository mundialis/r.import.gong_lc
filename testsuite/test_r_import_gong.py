#!/usr/bin/env python3
############################################################################
#
# MODULE:       r.import.gong_lc test
# AUTHOR(S):    Guido Riembauer
# PURPOSE:      Tests r.import.gong_lc using actinia-test-assets
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

import os

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule
import grass.script as grass


class TestRImportGonglc(TestCase):
    pid_str = str(os.getpid())
    old_region = "saved_region_{}".format(pid_str)
    ref_map_small = "landclass96"
    ref_map_large = "boundary_county_500m"
    gong_map = "gong_output_map"

    @classmethod
    def setUpClass(self):
        """Ensures expected computational region and generated data"""
        grass.run_command("g.region", save=self.old_region)

    @classmethod
    def tearDownClass(self):
        """Remove the temporary region and generated data"""
        grass.run_command("g.region", region=self.old_region)

    def tearDown(self):
        """Remove the outputs created
        This is executed after each test run.
        """
        self.runModule("g.remove", type="raster", name=self.gong_map, flags="f")

    def test_single_tile_gong_import(self):
        """Test if gong_lc is imported successfully for a small area
        (= single tile)"""
        grass.run_command("g.region", raster=self.ref_map_small)
        gong = SimpleModule("r.import.gong_lc", output=self.gong_map)
        self.assertModule(gong)
        self.assertRasterExists(self.gong_map)
        # test that the output has certain statistics
        stats = grass.parse_command("r.univar", map=self.gong_map, flags="g")
        ref_dict_stats = {
            "n": "249324",
            "null_cells": "0",
            "cells": "249324",
            "min": "20",
            "max": "90",
            "range": "70",
            "mean": "35.3000513388202",
            "mean_of_abs": "35.3000513388202",
            "stddev": "22.5884727053757",
            "variance": "510.239099161504",
            "coeff_var": "63.9899145997409",
            "sum": "8801150",
        }
        self.assertEqual(
            stats,
            ref_dict_stats,
            (
                "The imported raster statistics of {}" "do not match the reference"
            ).format(self.gong_map),
        )
        # test if the result has the correct category labels
        ref_list_cats = [
            "20|Forest",
            "30|Grassland",
            "40|Shrubland",
            "50|Wetland",
            "60|Water",
            "80|Impervious surface",
            "90|Bareland",
        ]
        cats = list(
            grass.parse_command(
                "r.category", map=self.gong_map, separator="pipe"
            ).keys()
        )
        self.assertEqual(
            cats,
            ref_list_cats,
            (
                "The imported raster categories of {}" "do not match the reference"
            ).format(self.gong_map),
        )

    def test_multi_tile_gong_import(self):
        """Test if gong_lc is imported successfully for a large area
        (= multiple tiles)"""
        grass.run_command("g.region", raster=self.ref_map_large, res=10, grow=-10000)
        gong = SimpleModule("r.import.gong_lc", output=self.gong_map)
        self.assertModule(gong)
        self.assertRasterExists(self.gong_map)
        # test that the output has certain statistics
        stats = grass.parse_command("r.univar", map=self.gong_map, flags="g")
        ref_dict_stats = {
            "n": "859455000",
            "null_cells": "0",
            "cells": "859455000",
            "min": "10",
            "max": "100",
            "range": "90",
            "mean": "25.4821994287077",
            "mean_of_abs": "25.4821994287077",
            "stddev": "14.5127947027464",
            "variance": "210.621210084063",
            "coeff_var": "56.952676880774",
            "sum": "21900803710",
        }
        self.assertEqual(
            stats,
            ref_dict_stats,
            (
                "The imported raster statistics of {}" "do not match the reference"
            ).format(self.gong_map),
        )
        # test if the result has the correct category labels
        ref_list_cats = [
            "10|Cropland",
            "20|Forest",
            "30|Grassland",
            "40|Shrubland",
            "50|Wetland",
            "60|Water",
            "80|Impervious surface",
            "90|Bareland",
            "100|Snow/Ice",
        ]
        cats = list(
            grass.parse_command(
                "r.category", map=self.gong_map, separator="pipe"
            ).keys()
        )
        self.assertEqual(
            cats,
            ref_list_cats,
            (
                "The imported raster categories of {}" "do not match the reference"
            ).format(self.gong_map),
        )


if __name__ == "__main__":
    test()
