#!/bin/bash
cat 5000.txt.utf-8.txt | python mapper.py | sort -k1,1 | python reducer.py
