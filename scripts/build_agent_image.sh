#!/bin/bash
set -e

echo "Building OMC Agent Base Image..."
docker build -t omc-agent-base:latest -f agent.Dockerfile .
echo "Build Complete. Tag: omc-agent-base:latest"
