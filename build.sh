#!/bin/bash

python resources.py > resources.yml && \
chalice package --merge-template resources.yml --template-format yaml dist
