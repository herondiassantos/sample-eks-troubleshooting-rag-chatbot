#!/bin/bash

# Export environment variables from .env file for local testing
# Usage: source export_env.sh

if [ -f .env ]; then
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^# ]] && [[ -n "$line" ]]; then
            # Remove quotes from the value
            line=$(echo "$line" | sed 's/="/=/' | sed 's/"$//')
            export "$line"
        fi
    done < .env
    echo "Environment variables exported from .env file successfully!"
else
    echo "Error: .env file not found"
fi