"""
Packs the current data folder into a zip file inside the store folder

@copyright: The Broad Institute of MIT and Harvard 2015
"""

import os, argparse, glob
import zipfile, zlib

parser = argparse.ArgumentParser()
parser.add_argument("name", nargs=1, default=["data"],
                    help="Name of zip file where to pack data folder")
args = parser.parse_args()

data_files = glob.glob("./data/*")

if not os.path.exists("./store"): os.makedirs("./store")

zip_filename = os.path.join("./store", args.name[0] + ".zip")

if os.path.exists(zip_filename):
    print "The file",zip_filename,"already exists, choose another name!"
    exit(1)

zf = zipfile.ZipFile(zip_filename, mode='w')
print "Compressing data folder into " + zip_filename + "..."
try:
    for file in data_files:
        print "  Adding file", file
        zf.write(file, compress_type=zipfile.ZIP_DEFLATED)
finally:
    zf.close()

print "Done."