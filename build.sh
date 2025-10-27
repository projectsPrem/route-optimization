#!/bin/bash
echo "Zipping Flask app..."
zip -r app.zip app.py requirements.txt
echo "✅ Build complete: app.zip created"
