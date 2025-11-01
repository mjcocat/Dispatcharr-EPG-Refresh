# Changelog

All notable changes to the EPG Refresh Scheduler plugin will be documented in this file.

## [1.4.0] - 2025-10-31

### Added
- **🗑️ Remove All Schedules** action - Delete all plugin-created schedules before uninstalling
- **⏸️ Disable Built-in Refresh Intervals** action - Set all M3U and EPG refresh intervals to 0 to prevent conflicts
- Confirmation prompts for destructive actions

### Changed
- Improved action organization and descriptions

## [1.3.0] - 2025-10-31

### Added
- Automatic normalization of cron expressions (`0/X` → `*/X`)
- `_normalize_cron()` function to handle slash notation properly

### Changed
- Updated plugin description with example cron expression
- Description now: "Schedule M3U playlist and EPG data refreshes with cron expressions. Example \"0 3 * * *\" to run everyday at 3am."

### Fixed
- Slash notation in cron expressions (e.g., `0/2 * * * *`) now works correctly
- Plugin now converts `0/5 * * * *` to `*/5 * * * *` automatically

## [1.2.6] - 2025-10-31

### Fixed
- M3U task name corrected to `apps.m3u.tasks.refresh_single_m3u_account`
- M3U schedules now execute properly

### Changed
- M3U schedules use correct Dispatcharr task

## [1.2.5] - 2025-10-31

### Added
- M3U and EPG prefixes in labels (e.g., "M3U - Dream01", "EPG - Jessman-USFast")
- Automatic filtering of "custom" M3U account

### Removed
- Section headers (📡 M3U Accounts, 📺 EPG Sources)

### Changed
- Cleaner UI with prefixed account names
- Examples moved to individual item descriptions

## [1.2.4] - 2025-10-31

### Added
- Example cron expressions in section descriptions
- M3U examples: `0 2 * * * (2am daily) | 0 */12 * * * (every 12 hours)`
- EPG examples: `0 3 * * * (3am daily) | 0 */6 * * * (every 6 hours)`

### Removed
- Divider line between sections (was creating unwanted text box)

### Changed
- Simplified plugin description

## [1.2.3] - 2025-10-31

### Added
- Divider line between M3U and EPG sections

### Changed
- Section headers now display as labels without input fields
- Updated plugin description with more detailed example

### Removed
- Description boxes under section headers

## [1.2.2] - 2025-10-31

### Fixed
- M3UAccount URL attribute error - removed URL display from M3U accounts
- M3U accounts now show: `ID: X | Type: M3U` without URL

## [1.2.1] - 2025-10-31

### Fixed
- M3U attribute error - now safely checks for both `type` and `source_type` attributes
- Removed duplicate EPG field generation code
- Better error handling for missing attributes

## [1.2.0] - 2025-10-31

### Added
- **M3U Account scheduling support** - Schedule automatic M3U playlist refreshes
- `_get_m3u_accounts()` function
- `_create_or_update_m3u_schedule()` function
- `_delete_m3u_schedule()` function
- M3U section in settings UI
- Separate scheduling for M3U accounts and EPG sources

### Changed
- Plugin now handles both M3U accounts and EPG sources
- Improved settings organization with clear sections

## [1.1.1] - 2025-10-31

### Added
- `_normalize_cron()` function for handling cron expression variations
- Better error logging with detailed validation messages
- Timezone conversion logging for complex expressions

### Fixed
- Default schedule values not saving - removed default value, now uses placeholder
- Cron validation now more robust with detailed error messages

### Changed
- Schedule fields start empty (no default value)
- Description updated to include slash notation examples

## [1.1.0] - 2025-10-31

### Added
- Timezone dropdown with 33 timezone options
- Comprehensive timezone list (US, European, Asian, Australian)

### Changed
- Timezone field changed from text input to select dropdown
- Default timezone options displayed with descriptions

### Removed
- Text input for timezone (replaced with dropdown)

## [1.0.8] - 2025-10-31

### Added
- Initial release
- EPG source scheduling with cron expressions
- Timezone support (text input)
- Individual schedules per EPG source
- Celery Beat integration
- Schedule validation
- **🔄 Sync Schedules** action
- **▶️ Refresh All Now** action (later removed)
- **📅 View Active Schedules** action

### Features
- Cron expression validation
- Automatic UTC conversion
- Schedule management
- Real-time schedule creation/updating

---

## Version Format

Versions follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes or major feature additions
- **MINOR**: New features, non-breaking changes
- **PATCH**: Bug fixes and minor improvements

## Links

- [Current Release](https://github.com/yourusername/epg-refresh-scheduler/releases/latest)
- [All Releases](https://github.com/yourusername/epg-refresh-scheduler/releases)
- [Issues](https://github.com/yourusername/epg-refresh-scheduler/issues)
