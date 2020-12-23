#!/bin/bash


git archive --prefix=autodeploy-$1/ HEAD  | gzip > ~/rpmbuild/SOURCES/autodeploy-$1.tar.gz
cp rpm/autodeploy.spec ~/rpmbuild/SPECS/

