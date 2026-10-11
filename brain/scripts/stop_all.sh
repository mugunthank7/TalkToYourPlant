#!/usr/bin/env bash
pkill -f "uvicorn plantsim.api" ; pkill -f "brain/app/api.py"; pkill -f "brain/app/dashboard.py"; pkill -f "brain/app/monitor.py"; pkill -f "vite"; echo stopped
