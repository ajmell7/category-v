.PHONY: help setup update activate run daemon stop status logs clean

# Variables
ENV_NAME = category-v
ENV_FILE = environment.yml
LOG_DIR = logs
PID_FILE = $(LOG_DIR)/main.pid
TIMESTAMP = $(shell date +%Y%m%d_%H%M%S)
LOG_FILE = $(LOG_DIR)/main_$(TIMESTAMP).log

# Default target
help:
	@echo "Available targets:"
	@echo "  make setup     - Create conda environment from environment.yml"
	@echo "  make update    - Update conda environment from environment.yml"
	@echo "  make activate  - Activate conda environment (prints activation command)"
	@echo "  make run       - Run main.py normally (foreground)"
	@echo "  make daemon    - Run main.py as daemon (background)"
	@echo "  make stop      - Stop the daemon process"
	@echo "  make status    - Check if daemon is running"
	@echo "  make logs       - View latest log file (tail -f)"
	@echo "  make clean     - Remove log files and PID file"

# Create conda environment
setup:
	@echo "Creating conda environment '$(ENV_NAME)' from $(ENV_FILE)..."
	conda env create -f $(ENV_FILE)
	@echo "Environment created! Activate with: conda activate $(ENV_NAME)"

# Update conda environment
update:
	@echo "Updating conda environment '$(ENV_NAME)' from $(ENV_FILE)..."
	conda env update -f $(ENV_FILE) --prune
	@echo "Environment updated!"

# Show activation command
activate:
	@echo "To activate the environment, run:"
	@echo "  conda activate $(ENV_NAME)"

# Get conda Python path
CONDA_PYTHON = $(shell conda run -n $(ENV_NAME) which python)

# Run normally (foreground)
run:
	@echo "Running main.py in foreground..."
	@echo "Press Ctrl+C to stop"
	@conda run -n $(ENV_NAME) python -u main.py

# Run as daemon (background)
daemon:
	@echo "Starting main.py as daemon..."
	@mkdir -p $(LOG_DIR)
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Daemon is already running (PID: $$PID)"; \
			exit 1; \
		else \
			echo "Removing stale PID file..."; \
			rm -f $(PID_FILE); \
		fi; \
	fi
	@echo "Log file: $(LOG_FILE)"
	@echo "PID file: $(PID_FILE)"
	@echo "Starting process..."
	@bash -c "source $$(conda info --base)/etc/profile.d/conda.sh && \
		conda activate $(ENV_NAME) && \
		nohup python -u main.py > $(LOG_FILE) 2>&1 & \
		echo \$$! > $(PID_FILE)"
	@sleep 2
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Daemon started successfully (PID: $$PID)"; \
			echo "Monitor with: make logs"; \
			echo "Stop with: make stop"; \
			echo "First few lines of log:"; \
			head -5 $(LOG_FILE) 2>/dev/null || echo "Log file not yet created"; \
		else \
			echo "Failed to start daemon. Check log file: $(LOG_FILE)"; \
			echo "Last 20 lines of log:"; \
			tail -20 $(LOG_FILE) 2>/dev/null || echo "Log file empty or not found"; \
			rm -f $(PID_FILE); \
			exit 1; \
		fi; \
	else \
		echo "Failed to create PID file"; \
		exit 1; \
	fi

# Stop daemon
stop:
	@if [ ! -f $(PID_FILE) ]; then \
		echo "No PID file found. Daemon may not be running."; \
		exit 1; \
	fi
	@PID=$$(cat $(PID_FILE)); \
	if ps -p $$PID > /dev/null 2>&1; then \
		echo "Stopping daemon (PID: $$PID)..."; \
		kill $$PID; \
		sleep 1; \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Process still running, forcing kill..."; \
			kill -9 $$PID; \
		fi; \
		rm -f $(PID_FILE); \
		echo "Daemon stopped."; \
	else \
		echo "Process not running (stale PID file)."; \
		rm -f $(PID_FILE); \
	fi

# Check daemon status
status:
	@if [ ! -f $(PID_FILE) ]; then \
		echo "Daemon is not running (no PID file)"; \
		exit 0; \
	fi
	@PID=$$(cat $(PID_FILE)); \
	if ps -p $$PID > /dev/null 2>&1; then \
		echo "Daemon is running (PID: $$PID)"; \
		ps -p $$PID -o pid,etime,command; \
	else \
		echo "Daemon is not running (stale PID file)"; \
		rm -f $(PID_FILE); \
	fi

# View latest log file
logs:
	@LATEST_LOG=$$(ls -t $(LOG_DIR)/main_*.log 2>/dev/null | head -1); \
	if [ -z "$$LATEST_LOG" ]; then \
		echo "No log files found in $(LOG_DIR)/"; \
		exit 1; \
	fi; \
	echo "Viewing log: $$LATEST_LOG"; \
	echo "Press Ctrl+C to stop viewing"; \
	tail -f $$LATEST_LOG

# Clean log files and PID
clean:
	@echo "Cleaning log files and PID file..."
	@rm -f $(LOG_DIR)/*.log $(PID_FILE)
	@echo "Cleaned!"
