.PHONY: requirements bootstrap clean doc tests bin

BUILD_DIR = build


# put #: in front of a command to provide help for it
help:
	@grep -E '#:' -A1 Makefile | \
		sed -rn '/^#:/ { N; s|^#: (.*)\n(.*):.*|\2 - \1|p }'



#: remove any build and python artifacts
clean: clean-pyc clean-build


#: clean up build directories
clean-build:
	rm -rf $(BUILD_DIR)/
	@echo "--> clear distribution done"
	@echo


#: remove any python artifacts
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

