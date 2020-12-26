#!/bin/bash
[ $# -eq 1 ] || echo "Argument (Version) is required..." && exit 1

git archive --prefix=autodeploy-$1/ HEAD  | gzip > ~/rpmbuild/SOURCES/autodeploy-$1.tar.gz
cp rpm/autodeploy.spec ~/rpmbuild/SPECS/
