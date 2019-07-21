# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
- Source loaders can now enable and disable the caching functionality on the fly
  with `Source.enable_cache()` and `Source.disable_cache()`.

### Changed
- `auto_subsection` does not add subsections for private variables anymore.
- `DictSource` now updates the original dictionary as expected.

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
