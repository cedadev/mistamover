#!/bin/bash
export PATH=../../../../../src:$PATH
sphinx-apidoc -o modules ../../lib
sphinx-build -b html . ../html
