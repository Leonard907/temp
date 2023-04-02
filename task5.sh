#!/usr/bin/env bash

echo /bin/cat /task5/secret.txt | env -i SHELL=/bin/sh \
    python3 task5.py
