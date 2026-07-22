#!/bin/bash
set -e

# ── Construction Safety AI Agent — Start Script ──────────────────────────────

# 1. Check Python version (3.10+)
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
  echo "ERROR: Python not found. Install Python 3.10+ and try again."
  exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "ERROR: Python 3.10+ required. Found Python $PY_VERSION."
  exit 1
fi

echo "Python $PY_VERSION found."

# 2. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON -m venv venv
fi

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# 5. Check for .env and API key
if [ ! -f ".env" ]; then
  echo ""
  echo "ERROR: .env file not found."
  echo "Create one with your Anthropic API key:"
  echo ""
  echo "  echo 'ANTHROPIC_API_KEY=your-key-here' > .env"
  echo ""
  exit 1
fi

if grep -q "your-key-here\|your-anthropic-api-key-here" .env 2>/dev/null; then
  echo ""
  echo "ERROR: API key placeholder detected in .env."
  echo "Open .env and replace the placeholder with your actual Anthropic API key."
  echo "Get one at: https://console.anthropic.com"
  echo ""
  exit 1
fi

if ! grep -q "ANTHROPIC_API_KEY=" .env 2>/dev/null; then
  echo ""
  echo "ERROR: ANTHROPIC_API_KEY not found in .env."
  echo "Add this line to your .env file:"
  echo ""
  echo "  ANTHROPIC_API_KEY=your-key-here"
  echo ""
  exit 1
fi

# 6. Start backend in background
echo ""
echo "Starting backend on http://localhost:8000 ..."
uvicorn api.main:app --port 8000 > /tmp/uvicorn.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready (up to 10 seconds)
echo "Waiting for backend to be ready..."
for i in $(seq 1 10); do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is up."
    break
  fi
  if [ $i -eq 10 ]; then
    echo "ERROR: Backend failed to start. Check /tmp/uvicorn.log for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
  fi
  sleep 1
done

# 7. Clean up backend on exit
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID 2>/dev/null" EXIT

# 8. Start frontend (foreground — this keeps the script running)
echo "Starting chat UI on http://localhost:8501 ..."
echo ""
echo "────────────────────────────────────────────────"
echo "  Agent is running. Open http://localhost:8501  "
echo "  Press Ctrl+C to stop.                        "
echo "────────────────────────────────────────────────"
echo ""

streamlit run frontend/app.py
