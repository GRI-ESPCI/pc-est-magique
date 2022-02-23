# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


# v0.1.1 (2022-02-23)

### Added

  * Added "masked collection/album" badges on photos pages.
  * ``fix_photos.py`` script to re-generate thubs and gzipped versions.

### Changed

  * Forced IP was written in hard (now ``FORCE_IP`` environment variable);

### Fixed

  * Fixed ``README.md``, ``model.env`` and ``nginx.conf``.


# v0.1.0 (2022-02-22)

### Added

  * Photos (blueprint, models, pages, script, env variables, nginx conf,
    metadata extraction, thumbs/gzipped versions, lightgallery, edit/report
    modals, featuring, defered loading, URL anchors...)


## v0.0.1 - 2022-02-11

First working application, with Flask structure derived from IntraRez.
No PC est magique-specific features.
