#!/bin/sh
sudo python3 emulation.py -lp examples/network-with-demands.yaml | tee ./examples/lp/run.lp && glpsol --lp ./examples/lp/run.lp --output ./examples/lp/run.out
