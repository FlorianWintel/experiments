#!/bin/bash

source ../common/utils.sh

export DATASET_PATH="$1"; shift
export RESUME_PATH="$1"; shift


export CARLA_VERSION=0.9.14
#export INTERFUSER_COMMIT="$(get_commit_hash_interfuser 0.9.14)"
#export INTERFUSER_COMMIT="613cedcf523345b177939125c34cf3286323032e"
#export INTERFUSER_COMMIT="0cd54a526b4dd1e15406c9b50649e70008019dcf"
export INTERFUSER_COMMIT="f257146f9fcfaebe468a23aebad1a02fa35b43c7"


if [ ! -d "$DATASET_PATH" ]; then
    echo "Dataset path does not exist: $DATASET_PATH"
    exit 1
fi

export EXPERIMENT_NAME="C_${CARLA_VERSION}-I_${INTERFUSER_COMMIT}-d_$(basename "$DATASET_PATH")"

echo "DATASET_PATH: $DATASET_PATH"
echo "RESUME_PATH: $RESUME_PATH"

run_in_screen "train-interfuser" \
    "docker compose up --build"
