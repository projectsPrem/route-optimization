#!/bin/bash
set -e

echo "🧩 Building Flask app for deployment..."

# Clean any old zip
rm -f app.zip

# Create new zip file with everything needed
zip -r app.zip app.py requirements.txt

echo "✅ Build complete: app.zip created successfully."
