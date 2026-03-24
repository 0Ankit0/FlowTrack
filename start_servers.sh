#!/bin/bash
# tmux is required for this to work

tmux new-session -d -s flowtrack 'cd backend && source .venv/bin/activate && task start'
tmux split-window -h -t flowtrack 'cd frontend && bun run dev'
tmux attach -t flowtrack