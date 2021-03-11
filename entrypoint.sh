#!/bin/bash
set -eo pipefail

RUN_USER="deploy"
exec gosu $RUN_USER "$@"