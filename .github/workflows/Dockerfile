FROM mundialis/grass-py3-pdal:latest-alpine

WORKDIR /src
COPY . /src
COPY .github/workflows/test.sh /src
RUN apk add gcc make python3-dev musl-dev linux-headers
RUN test -e requirements.txt && pip3 install -r requirements.txt || echo "No requirements.txt"

# # run tests with already downloaded NC test location
# RUN grass -c epsg:3358 /grassdb/nc_spm_empty --exec bash test.sh

# run tests in empty location and download "nc_spm_full_v2alpha2.tar.gz" location
RUN grass -c epsg:3358 /grassdb/nc_spm_empty --exec bash test.sh NC
