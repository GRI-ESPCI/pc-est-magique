# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


# v2.0.0 (unreleased)

Fusion of IntraRez (https://github.com/GRI-ESPCI/intrarez) into this project.

Since IntraRez had its own version and was in v1.6.3, this project is 
directly bumped from v0.2.1 to v2.0.0.

See original IntraRez changelog in `INTRAREZ_CHANGELOG.MD`.


# v0.2.1 (2022-05-14)

### Added

  * Permissions add/removal in GRI menu.

### Changed

  * Photos are now sorted by timestamp;
  * Collections/albums cover photo are now in high resolution;
  * Localized photos timestamp format.


# v0.2.0 (2022-03-09)

### Added

  * :class:`.models.Role` and :class:`.models.Permission` system, with
      * Enums :class:`.enums.PermissionType` and
        :class:`.enums.PermissionScope`;
      * Permission check method :class:`.models.PCeen.has_permission`,
        context functions :func:`.context.has_permission`,
        :func:`.context.check_permission`,
        :func:`.context.check_any_permission`,
        :func:`.context.check_all_permissions` and decorator
        :func:`.context.permission_only`;
  * GRI menu (from IntraRez) with PCeens and roles management pages.

### Changed

  * Photos access is now restricted to some permissions;
  * Main page message.


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
