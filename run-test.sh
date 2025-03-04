#!/bin/bash
set -e

echo 'Waiting...'
sleep 10s

echo 'Runing tests'
pytest . -s

echo 'Successful!'