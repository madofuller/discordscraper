#!/bin/bash
# Run batch historical export for all Discord channels

cd "$(dirname "$0")/.."

echo "Starting Discord Historical Batch Export..."
echo "Output will be saved to: batch_export.log"
echo ""

# Run in background and redirect output to log file
nohup python scripts/batch_historical_export.py > batch_export.log 2>&1 &

echo ""
echo "Export started in background! (PID: $!)"
echo "To check progress: tail -f batch_export.log"
echo ""




