#!/bin/sh

pyinstaller videoserver.py

mkdir -p deb/DEBIAN
mkdir -p deb/usr/local

cp -R dist/videoserver deb/usr/local
cp install/* deb/DEBIAN/
mkdir -p deb/usr/local/videoserver/install
cp install/* deb/usr/local/videoserver/install
chmod 0555 deb/DEBIAN/postinst
dpkg-deb --build deb videoserver.deb
rm -rf dist/ build/ deb/
rm videoserver.spec
