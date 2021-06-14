#!/bin/sh
set -e
pritunl set-mongodb mongodb://${MONGODB_USER:-"pritunl"}:${MONGODB_PASSWORD}@${MONGODB_SERVER:-"mongo"}:27017/pritunl?authSource=admin
pritunl start
