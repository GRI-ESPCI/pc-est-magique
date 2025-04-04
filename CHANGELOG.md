# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# v2.8.2 (2025-04-04)

### Fixed

- Club Q automatic email sending can be sent starting from a specific point in the list
- Hiding attribution for wishes in Club Q is now working correctly


# v2.8.1 (2025-03-06)

### Added

- In Club Q module, an option was added to hide places attribution to people while administration is still working on it

### Fixed

- Corrected shortcut for /theatre_posters/ path

- In Panier Bio module, creation of periods conditions are now functional
- In Panier Bio module, the button to manually create orders for admin is now functional

- In Club Q module, the excel export button for Spectacles was returning an error
- In Club Q module, the excel export route for one spectacle was misconfigured and returned all spectacles
- In Club Q module, the attribution algorithm was modifying whishes priorities in database
- In Club Q module, fixed the sending of e-mails for the attribution


# v2.8.0 (2024-09-29)

### Added

- Panier Bio page to order vegetables & fruits basket at the ESPCI

### Fixed

- Club Q fixes
- Bekks fixes

# v2.7.2 (2023-10-21)

### Added

- Integrated What You See Is What You Get (WYSIWYG) HTML editor with quill to allow club responsible to update their contents

### Changed

- Alcohol bar limit is now counted in grams

### Fixed

- Club Q pages visibility fix
- Club Q algorithm speed improved
- Bar stats number of clients

# v2.7.1 (2023-10-02)

### Added

- Club Q brochures for the current season and old ones
- Club Q spectacle image by website upload

### Changed

- Club Q images are now in a separated folder from /photos
- Club Q email template and reply-to address 

### Fixed

- Bekk PDF download with tokens
- Permissions misconfiguration for Club Q allowing users to modify whishes
- Subscription card was causing an error if the user never subscribed before

# v2.7.0 (2023-09-29)

### Added

- Bekk (ESPCI student newspaper) module. Read Bekks for user and tools for bekks administrators
- Compact version to reservation form for Club Q
- Bekk & Club Q cards for main page

### Changed

- Being a rezident is no longer required to access main page

### Fixed

- Fixed Club Q minimum places forms bug
- Background color bug for tables


# v2.6.1 (2023-09-18)

### Changed

- Minor fixes for Club Q


# v2.6.0 (2023-09-08)

### Added

- Managing tools for Club Q page (Attribution algorithm, e-mails sender, modules settings)
- Summary tables for better Club Q administration overview
- Interacting with the Club Q database through website

### Changed

- Club Q Booking page now takes in account was wishes were made before


# v2.5.0 (2023-04-17)

### Added

- ESPCI Club Q-ulture page
  - Booking page
  - List of spectacles
  - Club Q read permission

### Changed

- "Theatre ESPCI" was renamed "Club Théâtre"

# v2.4.5 (2023-04-16)

### Added

- Some documentation in README.md + table of contents

### Fixed

- A lot of small things backported from fixes applied directly to production server (don't do that)

# v2.4.4 (2023-03-17)

### Added

- Practical information about theatre piece at ESPCI

# v2.4.3 (2023-02-28)

### Added

- Link for after sales service for the theatre page


# v2.4.2 (2023-02-16)

### Changed

- Corrected texts

# v2.4.1 (2023-02-13)

### Added

- Database for the theatre page
  - List of spectacles
  - List of representations linked to spectacles

### Changed

- Images for the theatre page are now saved locally
- License

### Deleted

- the /static/img/theatre directory

# v2.4.0 (2023-01-24)

### Added

- Static page for the ESPCI Theatre Club 2023 season
  - Informations & description for all the plays
  - Access throught the navbar
  - Partially translated in english

# v2.3.1 (2022-12-30)

### Fixed

- `update_sub_states` script crashed for users with access to IntraRez but without devices

# v2.3.0 (2022-12-30)

### Added

- Extensive photos management system:
  - Create albums;
  - Upload photos from app (with automatic thumbnail creation and metadata extraction);
  - Edit / star / delete photos from album view.
- New "public permission" system:
  - New role `_PUBLIC` that applies to all users, logged in or not;
  - New classmethod `PCeen.has_public_permission` checking this role.
- New annual script automating changes:
  - Replace "Student" role by "Alumni" role for leaving students (sending a mail);
  - Create entering promotion collection and role.
- New `showToast` JS function allowing to "create" a new toast through JS, after page loading;
- Running `flask script` without argument now list all existing scripts.

### Changed

- Access to the photo module are no longer restricted (but collections still are!);
- Collections are now ordered from most recent to oldest;
- Collection and albums cannot be marked visible if they are empty.

### Removed

- Photo edit / star buttons in the upper ribbon of the gallery; use album view instead.

# v2.2.1 (2022-10-29)

### Changed

- PCéens with permission read/bar_stats are now reported in the Bar users list.

### Fixed

- Bar user page crashed when no quick access item was selected ;
- Global settings were not saved to base and had a weired behavior ;
- Errors when trying to upload a Bar avatar were not correctly handled.

### Removed

- One-shot Bar data migration script.

# v2.2.0 (2022-10-15)

Fusion of the ESPCI Bar site (https://github.com/GRI-ESPCI/espci-bar-web-app) into this project.

_This project had no versioning and no changelog._

### Added

- New Bar module:
  - Tables `BarItem`, `BarTransaction`, `BarDailyData` and enum `BarTransactionType`;
  - Columns `PCeen.bar_nickname`, `PCeen.bar_deposit` and `PCeen.bar_balance`;
  - Blueprint `bar` with 9 new routes;
  - Corresponding templates;
  - Main page info card;
  - Nginx location `/bar_avatars` to securely serve users avatars (stored in photos directory);
  - New roles and permissions creation in script `update_roles.py`:
  - One-shot script `import_bar_data` to import current Bar data in new tables.
- New generic API system:
  - Blueprint `api`;
  - Sub-blueprint `api.bar` with 6 new routes;
  - New `js/api.js` functions.
- New "global settings" system:
  - Table `GlobalSetting`;
  - `app.utils.global_settings` module;
  - New Babel global variable `Settings`;
- Split PCéens management page into 4 different views;
- New column `PCeen.activated` denoting accounts that logged in at least once (not created automatically);
- New permissions routes context manager `context.any_permission_only`.

### Changed

- Moved role-granting utilities to new module `app.utils.roles`;
- Moved Nginx token handling to new module `app.utils.nginx`;
- Moved roles / permissions add / remove utilities to `api.gris` sub-blueprint;
- Moved main navbar and footer to specific templates `main/navbar.html`/`main/footer.html`;
- Bumped to Bootstrap 5.0.

### Fixed

- SAML identity provider fallback mechanism did not worked.

# v2.1.3 (2022-09-17)

### Changed

- Grant automatically Rezident role when connecting from the internal network.

# v2.1.2 (2022-08-23)

### Fixed

- Scripts did not log errors to Discord ;
- `update_sub_states` script crashed because of PCeens without IntraRez access.

# v2.1.1 (2022-07-18)

### Changed

- Index profile card: number of devices replaced by roles list.

### Fixed

- Fixed missing permissions restrictions:
  - Rooms / devices / payments routes: restrict access to `read`/`intrarez` permission;
  - Photos routes: restrict collection / album / photo modification to corresponding `write` permission ;
- Fix corresponding information shown:
  - Profile page: only show room and device cards in `read`/`intrarez` permission;
  - Photos pages: show edit buttons and load edit forms only if `write`/`photos` permission.

# v2.1.0 (2022-07-17)

### Added

- Authentication with ESPCI SSO
  - New :mod:`routes.auth.saml` blueprint;
  - Column :attr:`models.PCeen._password_hash` is now nullable;
  - New column :attr:`models.PCeen.espci_sso_enabled`;
  - Adapted login / sign-in pages;
  - New config variables `SAML_IDP_METADATA_URL`, `SAML_IDP_METADATA_FALLBACK_URL`,
    `SAML_CERTIFICATE_PRIVATE_KEY_FILE`, `SAML_CERTIFICATE_PUBLIC_KEY_FILE`.
- Automatically grand `Rezident` role when registrating from the Rez network;

### Changed

- Updated legal mentions page.

### Fixed

- GRI PCéens list was missing subscribtion information and modals.

# v2.0.1 (2022-07-06)

Test of SAML implementation.

# v2.0.0 (2022-07-04)

Fusion of IntraRez (https://github.com/GRI-ESPCI/intrarez) into this project.

Since IntraRez had its own version and was in v1.6.3, this project is
directly bumped from v0.2.1 to v2.0.0.

See original IntraRez changelog in `INTRAREZ_CHANGELOG.MD`.

# v0.2.1 (2022-05-14)

### Added

- Permissions add/removal in GRI menu.

### Changed

- Photos are now sorted by timestamp;
- Collections/albums cover photo are now in high resolution;
- Localized photos timestamp format.

# v0.2.0 (2022-03-09)

### Added

- :class:`.models.Role` and :class:`.models.Permission` system, with
  - Enums :class:`.enums.PermissionType` and
    :class:`.enums.PermissionScope`;
  - Permission check method :class:`.models.PCeen.has_permission`,
    context functions :func:`.context.has_permission`,
    :func:`.context.check_permission`,
    :func:`.context.check_any_permission`,
    :func:`.context.check_all_permissions` and decorator
    :func:`.context.permission_only`;
- GRI menu (from IntraRez) with PCeens and roles management pages.

### Changed

- Photos access is now restricted to some permissions;
- Main page message.

# v0.1.1 (2022-02-23)

### Added

- Added "masked collection/album" badges on photos pages.
- `fix_photos.py` script to re-generate thubs and gzipped versions.

### Changed

- Forced IP was written in hard (now `FORCE_IP` environment variable);

### Fixed

- Fixed `README.md`, `model.env` and `nginx.conf`.

# v0.1.0 (2022-02-22)

### Added

- Photos (blueprint, models, pages, script, env variables, nginx conf,
  metadata extraction, thumbs/gzipped versions, lightgallery, edit/report
  modals, featuring, defered loading, URL anchors...)

## v0.0.1 - 2022-02-11

First working application, with Flask structure derived from IntraRez.
No PC est magique-specific features.
