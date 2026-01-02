#!/bin/sh
set -e

export GOOGLE_APPLICATION_CREDENTIALS="/run/secrets/google_adc.json"
export TABBY_ROOT="/root/.tabby"

if [ -z "$GOOGLE_PROJECT_ID" ] || [ -z "$GOOGLE_REGION" ]; then
  echo '$GOOGLE_PROJECT_ID and $GOOGLE_REGION must be defined'
fi

if [ ! -d "$TABBY_ROOT" ]; then
  echo "$TABBY_ROOT not found"
  exit 1
fi

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "Google ADC not found"
  exit 1
fi

cp "/opt/config.toml" "$TABBY_ROOT"

cd /opt/vertex2tabby
"$HOME/.pixi/bin/pixi" run start &
PID1=$!

/opt/tabby/bin/tabby serve &
PID2=$!

trap "kill $PID1 $PID2" TERM INT
wait
