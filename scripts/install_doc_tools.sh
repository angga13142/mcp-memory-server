#!/bin/bash
# Install documentation tooling

set -e

npm install -g markdownlint-cli markdown-link-check
pip install markdown
sudo apt-get install -y aspell || true
