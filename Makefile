.PHONY: help install update activate run clean

# Variables
ENV_NAME = category-v
ENV_FILE = environment.yml
STREAMLIT_FILE = home_install.py

# Default target
help:
	@echo "Available targets:"
	@echo "  make install   - Create conda environment from environment.yml"
	@echo "  make update    - Update conda environment from environment.yml"
	@echo "  make activate  - Print shell commands to activate conda env in your shell"
	@echo "  make run       - Run Streamlit app (foreground)"
	@echo "  make clean     - Remove log files"
	@echo ""
	@echo "Activation usage:"
	@echo "  eval \"$$(make activate)\""

# Create conda environment
install:
	@echo "Creating conda environment '$(ENV_NAME)' from $(ENV_FILE)..."
	conda env create -f $(ENV_FILE)
	@echo "Environment created! Activate with: make activate"

# Update conda environment
update:
	@echo "Updating conda environment '$(ENV_NAME)' from $(ENV_FILE)..."
	conda env update -f $(ENV_FILE) --prune
	@echo "Environment updated!"

# Print shell commands to activate conda environment (must be eval'd by the caller)
# Usage: eval "$$(make activate)"
activate:
	@if conda env list | awk '{print $$1}' | grep -qx "$(ENV_NAME)"; then \
		echo "# NOTE: 'make activate' cannot activate your CURRENT shell by itself."; \
		echo "# Run this in your shell to activate:"; \
		echo "conda activate $(ENV_NAME)"; \
	else \
		echo "Error: Conda environment '$(ENV_NAME)' does not exist."; \
		echo "Please create it first by running: make install"; \
		exit 1; \
	fi

# Run Streamlit app (foreground)
run:
	@if [ -z "$$CONDA_DEFAULT_ENV" ]; then \
		echo "Error: No conda environment is currently active."; \
		echo "Please activate the environment first:"; \
		echo "  conda activate $(ENV_NAME)"; \
		exit 1; \
	elif [ "$$CONDA_DEFAULT_ENV" != "$(ENV_NAME)" ]; then \
		echo "Error: Current conda environment is '$$CONDA_DEFAULT_ENV', but expected '$(ENV_NAME)'."; \
		echo "Please activate the correct environment:"; \
		echo "  conda activate $(ENV_NAME)"; \
		exit 1; \
	else \
		echo "Running Streamlit app in active environment '$(ENV_NAME)'..."; \
		echo "Press Ctrl+C to stop"; \
		streamlit run $(STREAMLIT_FILE); \
	fi

# Clean log files
clean:
	@echo "Cleaning log files..."
	@rm -f logs/*.log
	@echo "Cleaned!"
