#!/bin/sh
set -e

USERS_FILE=${USERS_FILE:-/app/data/users.json}

if [ ! -f "$USERS_FILE" ] && [ -f /app/users.json ]; then
    cp /app/users.json "$USERS_FILE"
    echo "Copied default users.json to $USERS_FILE"
fi

exec "$@"
