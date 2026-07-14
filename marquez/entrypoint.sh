#!/bin/bash
set -e

sed "s|\${POSTGRES_PASSWORD}|${POSTGRES_PASSWORD}|g" /usr/src/app/config.yml > /tmp/config.yml
cp /tmp/config.yml /usr/src/app/config.yml

exec java ${JAVA_OPTS:--Duser.timezone=UTC -Dlog4j2.formatMsgNoLookups=true} \
  -jar marquez-*.jar server ${MARQUEZ_CONFIG}
