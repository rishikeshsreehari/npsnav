.PHONY: install build serve clean dev deploy update

# Install dependencies
install:
	uv sync

# Build the static site
build:
	uv run scripts/build.py

# Serve the site locally
serve:
	uv run scripts/serve_local.py

# Clean build artifacts
clean:
	rm -rf public

# Default development flow: build and serve
dev: build serve

# Deploy to Cloudflare
deploy:
	npx wrangler pages deploy public

# Update content: fetch new data, build, and deploy
update:
	uv run scripts/fetch.py
	$(MAKE) build
	$(MAKE) deploy
