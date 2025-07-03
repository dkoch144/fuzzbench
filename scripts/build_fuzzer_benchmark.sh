#!/bin/bash

export FUZZER_NAME=$1
export BENCHMARK_NAME=$2

make build-$FUZZER_NAME-$BENCHMARK_NAME
