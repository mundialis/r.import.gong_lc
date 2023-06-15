#!/usr/bin/env bash

# fail on non-zero return code from a subprocess
set -e

# download NC test location if the test needs the data and run tests
if [ "$1" == "NC" ]
then
  g.extension g.download.location
  g.download.location url=https://grass.osgeo.org/sampledata/north_carolina/nc_spm_full_v2alpha2.tar.gz path=/grassdb
  g.mapset mapset=PERMANENT location=nc_spm_full_v2alpha2 -c
  g.list all
fi

# run all tests in folder
FILENAME=$(basename "$(find . -name *.html -maxdepth 1)")
ADDON="${FILENAME%%.html}"

CURRENTDIR=$(pwd)
g.extension extension=${ADDON} url=. && \
for file in $(find . -type f -name test*.py) ; \
do  \
  echo ${file}
  BASENAME=$(basename "${file}") ; \
  DIR=$(dirname "${file}") ; \
  cd ${CURRENTDIR}/${DIR} && python3 -m unittest ${BASENAME}
done
