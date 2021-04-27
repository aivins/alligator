#!/bin/bash

python resources.py > resources.json && \
chalice package --merge-template resources.json --template-format json dist
