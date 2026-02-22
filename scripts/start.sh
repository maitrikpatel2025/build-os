#!/bin/bash
# Build OS: Start services for a built project
# Usage: ./scripts/start.sh [output-project-path]

set -e

PROJECT_PATH="${1:-output}"

# Find the first project in output/
if [ -d "$PROJECT_PATH" ] && [ ! -f "$PROJECT_PATH/scripts/start.sh" ]; then
  FIRST_PROJECT=$(ls -d "$PROJECT_PATH"/*/ 2>/dev/null | head -1)
  if [ -n "$FIRST_PROJECT" ]; then
    PROJECT_PATH="$FIRST_PROJECT"
  fi
fi

if [ ! -d "$PROJECT_PATH" ]; then
  echo "Error: Project not found at $PROJECT_PATH"
  echo "Usage: ./scripts/start.sh [output/project-name]"
  exit 1
fi

echo "Starting project at: $PROJECT_PATH"

# Load port configuration
if [ -f "$PROJECT_PATH/.ports.env" ]; then
  source "$PROJECT_PATH/.ports.env"
fi

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# Start backend
echo "Starting backend on port $BACKEND_PORT..."
cd "$PROJECT_PATH/app/server"
uv run uvicorn server:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on port $FRONTEND_PORT..."
cd "$PROJECT_PATH/app/client"
FRONTEND_PORT=$FRONTEND_PORT npm run dev &
FRONTEND_PID=$!

echo ""
echo "Services started:"
echo "  Backend:  http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"
echo "  Frontend: http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)"
echo ""
echo "Press Ctrl+C to stop both services"

# Save PIDs
echo "$BACKEND_PID" > "$PROJECT_PATH/.backend.pid"
echo "$FRONTEND_PID" > "$PROJECT_PATH/.frontend.pid"

wait
