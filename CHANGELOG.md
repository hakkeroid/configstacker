# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Fixed
- `YAMLFile` will use an empty dictionary instead of None when loading empty yaml files.
- `INIFile` now properly sets the default subsection token.

## [0.1.1] - 2019-07-20
### Added
- More metadata for the packaging index

## [0.1.0] - 2019-07-20
### Added
- Reimplementation of [layeredconfig's API](https://layeredconfig.readthedocs.io/)
- Usable stand-alone sources
- Custom type conversion
- Custom folding strategy for consecutive sources
