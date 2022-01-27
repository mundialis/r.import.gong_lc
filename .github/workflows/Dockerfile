FROM mundialis/grass-py3-pdal:latest-alpine

WORKDIR /src
COPY . /src
COPY .github/workflows/test.sh /src
RUN apk add gcc make python3-dev musl-dev linux-headers
RUN test -e requirements.txt && pip3 install -r requirements.txt || echo "No requirements.txt"

# # run tests with downloaded NC test loaction
# RUN grass -c epsg:3358 /grassdb/nc_spm_empty --exec bash test.sh NC

# run tests in empty location
RUN grass -c epsg:3358 /grassdb/nc_spm_empty --exec bash test.sh
