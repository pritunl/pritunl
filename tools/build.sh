#!/bin/bash
set -e
python2 tools/builder.py set-version $1
python2 tools/builder.py build
python2 tools/builder.py upload
