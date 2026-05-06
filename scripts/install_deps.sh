#!/bin/bash
set -e
VENV=/home/administrator/.hermes/hermes-agent/venv/bin/python
$VENV -m pip install fastapi uvicorn pymupdf python-docx pydantic python-multipart 2>&1 | tail -30
echo "=== Checking imports ==="
$VENV -c "import fastapi; print('fastapi OK')"
$VENV -c "import fitz; print('pymupdf OK')"  
$VENV -c "import docx; print('python-docx OK')"
$VENV -c "import uvicorn; print('uvicorn OK')"
echo "=== DONE ==="
