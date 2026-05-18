# cicd-cli Makefile
PREFIX ?= $(HOME)/.cicd-cli
BINDIR ?= $(PREFIX)/bin
PYTHON ?= python3

.PHONY: install uninstall test clean help

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install cicd-cli
	@echo "Installing cicd-cli..."
	@mkdir -p $(PREFIX) $(BINDIR)
	@cp -r core commands shortcuts skills config bin $(PREFIX)/
	@cp requirements.txt pyproject.toml AGENTS.md README.md $(PREFIX)/
	@$(PYTHON) -m pip install -r requirements.txt -q 2>/dev/null || echo "Warning: run manually: $(PYTHON) -m pip install -r requirements.txt"
	@echo '#!/usr/bin/env bash' > $(BINDIR)/cicd-cli
	@echo 'exec $(PYTHON) "$(PREFIX)/core/cli.py" "$$@"' >> $(BINDIR)/cicd-cli
	@chmod +x $(BINDIR)/cicd-cli
	@mkdir -p $(HOME)/.cicd-cli/config $(HOME)/.cicd-cli/secrets
	@echo ""
	@echo "Done! Add to PATH:"
	@echo "  export PATH=\"$(BINDIR):$$PATH\""
	@echo "  then run: cicd-cli config init"

uninstall: ## Uninstall cicd-cli
	@echo "Uninstalling cicd-cli..."
	@rm -rf $(PREFIX)/core $(PREFIX)/commands $(PREFIX)/shortcuts $(PREFIX)/skills $(PREFIX)/config $(PREFIX)/bin
	@rm -f $(PREFIX)/requirements.txt $(PREFIX)/pyproject.toml $(PREFIX)/AGENTS.md $(PREFIX)/README.md
	@echo "Done (config kept in ~/.cicd-cli/config/)"

test: ## Run tests
	@$(PYTHON) -m pytest tests/ -v

clean: ## Clean temp files
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@rm -rf .pytest_cache
	@echo "Done"
