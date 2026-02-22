#!/bin/bash
# Build OS: Stop services for a built project
# Usage: ./scripts/stop.sh [output-project-path]

PROJECT_PATH="${1:-output}"

# Find the first project in output/
if [ -d "$PROJECT_PATH" ] && [ ! -f "$PROJECT_PATH/.backend.pid" ]; then
  FIRST_PROJECT=$(ls -d "$PROJECT_PATH"/*/ 2>/dev/null | head -1)
  if [ -n "$FIRST_PROJECT" ]; then
    PROJECT_PATH="$FIRST_PROJECT"
  fi
fi

STOPPED=0

if [ -f "$PROJECT_PATH/.backend.pid" ]; then
  kill "$(cat "$PROJECT_PATH/.backend.pid")" 2>/dev/null
  rm "$PROJECT_PATH/.backend.pid"
  echo "Stopped backend"
  STOPPED=1
fi

if [ -f "$PROJECT_PATH/.frontend.pid" ]; then
  kill "$(cat "$PROJECT_PATH/.frontend.pid")" 2>/dev/null
  rm "$PROJECT_PATH/.frontend.pid"
  echo "Stopped frontend"
  STOPPED=1
fi

if [ "$STOPPED" -eq 0 ]; then
  echo "No running services found at $PROJECT_PATH"
fi
