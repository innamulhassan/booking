#!/bin/bash
echo "🩺 Therapy Booking Bot - Quick POC Start"
echo "====================================="

echo "📦 Installing requirements..."
pip install -r requirements.txt

echo "🚀 Starting server..."
echo ""
echo "🌐 Demo will be available at: http://localhost:8000/demo"
echo "⏹️  Press Ctrl+C to stop"
echo ""

python main.py
