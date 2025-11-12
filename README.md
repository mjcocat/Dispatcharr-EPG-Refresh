# EPG Refresh Scheduler

Schedule M3U playlist and EPG data refreshes with cron expressions. Example "0 3 * * *" to run everyday at 3am.

#Quick setup

1. Disable Built-in Refresh Intervals
2. Update your timezone to you preferred timezone 
3. Enable individual M3U/EPG's that you want to configure for a schedule 
4. Add schedule to each M3U/EPG using a cron format (e.g "0 2 * * * = 2am)
5. Click Save Settings
6. Click Sync Schedules
7. Click View Active Schedules to validate the schedule is correct


## Changelog

v1.6.3 (Latest)

More TZ fixes

v1.6.0 

Fixed some TZ issues 

v1.4.0 

🗑️ Remove All Schedules action

⏸️ Disable Built-in Refresh Intervals action

Confirmation prompts for destructive actions

v1.3.0

Fixed slash notation (0/X → */X)

Auto-normalization of cron expressions

Updated description

## Features

- 📡 **M3U Account Scheduling** - Automatically refresh M3U playlists on schedule
- 📺 **EPG Source Scheduling** - Automatically refresh EPG data on schedule
- 🌍 **Timezone Support** - Set schedules in your timezone (33 timezones supported)
- ⏰ **Flexible Scheduling** - Use standard cron expressions
- 🔄 **Auto-normalization** - Converts `0/X` to `*/X` format automatically
- 🎯 **Individual Schedules** - Different schedule for each M3U/EPG source
- 📊 **Schedule Management** - View and sync active schedules

## Installation

1. Download `epg_refresh_scheduler.zip`
2. Go to Dispatcharr → Settings → Plugins
3. Click "Upload Plugin"
4. Select the ZIP file
5. Enable the plugin
6. Restart Dispatcharr: `docker restart dispatcharr`

## Configuration

### 1. Select Timezone
Choose your timezone from the dropdown (default: UTC). All schedule times will be converted to UTC automatically.

**Example timezones:**
- US/Central (CST/CDT) - Chicago
- US/Eastern (EST/EDT) - New York
- US/Pacific (PST/PDT) - Los Angeles
- Europe/London (GMT/BST)
- Asia/Tokyo (JST)

### 2. Schedule M3U Accounts

For each M3U account, check "Enable" and enter a cron expression:

**Format:** `minute hour day month day_of_week`

**Examples:**
- `0 2 * * *` - 2:00 AM daily
- `0 */12 * * *` - Every 12 hours
- `0 3 * * 0` - 3:00 AM on Sundays only
- `30 4 * * *` - 4:30 AM daily
- `*/5 * * * *` - Every 5 minutes

### 3. Schedule EPG Sources

Same process as M3U accounts - enable and set cron schedule.

**Examples:**
- `0 3 * * *` - 3:00 AM daily
- `0 */6 * * *` - Every 6 hours
- `30 2 * * *` - 2:30 AM daily

### 4. Save Settings

Click "Save Settings" to activate the schedules.

## Cron Expression Guide

Cron format: `minute hour day month day_of_week`

| Field | Values | Special |
|-------|--------|---------|
| minute | 0-59 | `*/5` = every 5 minutes |
| hour | 0-23 | `*/6` = every 6 hours |
| day | 1-31 | `*` = every day |
| month | 1-12 | `*` = every month |
| day_of_week | 0-6 (Sun-Sat) | `*` = every day |

**Special Characters:**
- `*` - Every value (any)
- `*/X` - Every X units
- `X-Y` - Range from X to Y
- `X,Y,Z` - Specific values

**Common Examples:**
- `0 3 * * *` - 3:00 AM every day
- `0 */6 * * *` - Every 6 hours (midnight, 6am, noon, 6pm)
- `*/30 * * * *` - Every 30 minutes
- `0 0 * * 0` - Midnight every Sunday
- `0 8 * * 1-5` - 8:00 AM Monday through Friday
- `0 2,14 * * *` - 2:00 AM and 2:00 PM daily

**Note:** The plugin automatically converts `0/X` to `*/X` format for compatibility.

## Timezone Conversion

When you select a timezone and use simple time expressions (like `0 3 * * *`), the plugin automatically converts them to UTC.

**Example with US/Central:**
- You enter: `0 22 * * *` (10:00 PM Central)
- Converts to: `0 3 * * *` (3:00 AM UTC, which is 10:00 PM Central - 5 hours during CDT)

**Complex expressions stay UTC-relative:**
- `*/6 * * * *` (every 6 hours) - No conversion, runs every 6 hours in UTC
- `0 */12 * * *` (every 12 hours) - No conversion, timezone-independent

This is intentional - expressions like "every 6 hours" are already timezone-independent!

## Actions

### 🔄 Sync Schedules
Reloads your settings and updates all Celery Beat schedules. Use this after making changes.

### 📅 View Active Schedules
Shows all active scheduled tasks in Celery Beat with their cron expressions (in UTC).

## Troubleshooting

### Schedules not running?

**Check logs:**
```bash
docker logs -f dispatcharr | grep -i epg_refresh_scheduler
```

**Verify schedules are created:**
```bash
docker exec dispatcharr python manage.py shell -c "from django_celery_beat.models import PeriodicTask; tasks = PeriodicTask.objects.filter(name__contains='epg_refresh_scheduler'); [print(f'{t.name}: {t.crontab}') for t in tasks]"
```

**Common issues:**
1. **Forgot to save settings** - Click "Save Settings" after making changes
2. **Invalid cron expression** - Check the format is correct
3. **Celery not running** - Restart Dispatcharr
4. **Wrong timezone** - Verify timezone is set correctly

### M3U schedules not executing?

Make sure you're on v1.3.0 or later. Earlier versions had the wrong task name.

### Slash notation not working?

Upgrade to v1.3.0 or later. The plugin now automatically converts `0/X` to `*/X`.

## How It Works

1. **You configure** schedules in your timezone
2. **Plugin converts** simple times to UTC
3. **Celery Beat** triggers tasks at scheduled times
4. **Tasks execute:**
   - M3U: `apps.m3u.tasks.refresh_single_m3u_account(m3u_id)`
   - EPG: `apps.epg.tasks.refresh_all_epg_data()`

## Version History

- **v1.3.0** - Fixed slash notation (0/X → */X), updated description
- **v1.2.6** - Fixed M3U task name to use correct task
- **v1.2.5** - Cleaner UI with prefixes, hidden "custom" account
- **v1.2.4** - Added examples in section headers
- **v1.2.3** - UI improvements, removed unnecessary fields
- **v1.2.2** - Fixed M3U URL error
- **v1.2.1** - Fixed M3U display error
- **v1.2.0** - Added M3U account scheduling
- **v1.1.1** - Fixed default values, improved validation
- **v1.1.0** - Timezone dropdown restored
- **v1.0.8** - Initial release with EPG scheduling

## Support

For issues or questions, please check the Dispatcharr documentation or community forums.

## License

Community Plugin - Free to use and modify
