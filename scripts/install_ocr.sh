#!/bin/bash
set -e
echo "=== 安装 Tesseract OCR ==="
sudo apt-get update -qq && sudo apt-get install -y -qq tesseract-ocr tesseract-ocr-chi-sim 2>&1 | tail -5
echo "=== 安装 pytesseract ==="
/home/administrator/.hermes/hermes-agent/venv/bin/pip install pytesseract Pillow 2>&1 | tail -5
echo "=== 验证 ==="
tesseract --version 2>&1 | head -2
tesseract --list-langs 2>&1
/home/administrator/.hermes/hermes-agent/venv/bin/python -c "import pytesseract; print('pytesseract OK')"
echo "=== DONE ==="
