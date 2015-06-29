#!/bin/bash -ex

# expected env variables:
# * WORKSPACE
# * DIST
# * REPO

export SIGNKEY=12CCD1CB

if [ -z "${WORKSPACE}" ]; then
    export WORKSPACE=.
fi

CI_URL="${JENKINS_URL}"

if [ -n "${JENKINS_URL}" ]; then
    CI_URL="${JENKINS_URL}"
elif [ -n "${HUDSON_URL}" ]; then
    CI_URL="${HUDSON_URL}"
else
    CI_URL="http://localhost:8080/"
fi

if ! [ -d "${WORKSPACE}/simplejson" ]; then
    wget https://pypi.python.org/packages/source/s/simplejson/simplejson-3.7.3.tar.gz --no-check-certificate
    tar zxf simplejson-3.7.3.tar.gz
    cp -r simplejson-3.7.3/simplejson ${WORKSPACE}/
    rm -rf simplejson-3.7.3*
fi

rm -rf ${WORKSPACE}/debian ${WORKSPACE}/download-list-*
python ${WORKSPACE}/get_artifacts_list.py ${CI_URL} "${JOB_NAME}" ${BUILD_NUMBER}

if ! [ -f "download-list-${BUILD_NUMBER}" ]; then
    echo "The job is meant to be started only from upstream!"
    exit 0
fi

wget -i download-list-${BUILD_NUMBER} -P ${WORKSPACE}/debian

cd ${REPO}
for i in *.deb; do
    dpkg-sig -s origin -v -k ${SIGNKEY} ${WORKSPACE}/debian/$i
    reprepro includedeb $DIST ${WORKSPACE}/debian/$i
done
