.PHONY: clean publish check-env

DIST_DIR = dist
BUILD_DIR = build
DOCS_BUILD_DIR = docs/build


# put #: in front of a command to provide help for it
help:
	@grep -E '#:' -A1 Makefile | \
		sed -rn '/^#:/ { N; s|^#: (.*)\n(.*):.*|\2 - \1|p }'


#: remove any build and python artifacts
clean: clean-pyc clean-build clean-dist

#: clean up dist directories
clean-dist:
	@rm -rf $(DIST_DIR)/

#: clean up build directories
clean-build:
	@rm -rf $(BUILD_DIR)/
	@rm -rf $(DOCS_BUILD_DIR)/

#: remove any python artifacts
clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +
