# EPG Refresh Scheduler for Dispatcharr

A powerful plugin that enables flexible, cron-based scheduling for EPG (Electronic Program Guide) refreshes in Dispatcharr. Instead of relying solely on fixed refresh intervals, you can now schedule EPG updates at specific times using familiar cron expressions.

## Features

- ✅ **Flexible Scheduling** - Use cron expressions to schedule EPG refreshes at exact times
- ✅ **Individual EPG Control** - Configure separate schedules for each EPG source
- ✅ **Advanced Cron Support** - Full support for `/` (step values) and `,` (lists) operators
- ✅ **Automatic Management** - Schedules are automatically created and managed via Celery Beat
- ✅ **Real-time Validation** - Validates cron expressions before saving
- ✅ **Next Run Preview** - See when each EPG is scheduled to refresh next
- ✅ **Active EPG Detection** - Only shows non-dummy, active EPG sources

## Installation

### 1. Download the Plugin

Download the plugin as a ZIP file or clone this repository.

### 2. Upload to Dispatcharr

1. Navigate to **Settings → Plugins**
2. Click **Import Plugin**
3. Upload the ZIP file
4. Enable the plugin when prompted

### 3. Restart Dispatcharr

**IMPORTANT:** You must restart the Dispatcharr container after installation:

```bash
docker restart dispatcharr
```

## Configuration

### Cron Expression Format

Cron expressions use 5 fields: `minute hour day month day_of_week`

#### Field Values

| Field | Values | Special Characters |
|-------|--------|-------------------|
| Minute | 0-59 | `*` `,` `-` `/` |
| Hour | 0-23 | `*` `,` `-` `/` |
| Day of Month | 1-31 | `*` `,` `-` `/` |
| Month | 1-12 | `*` `,` `-` `/` |
| Day of Week | 0-6 (0=Sunday) | `*` `,` `-` `/` |

#### Special Characters

- `*` - Any value (every minute, hour, etc.)
- `,` - List of values (e.g., `1,3,5` = 1st, 3rd, and 5th)
- `-` - Range of values (e.g., `1-5` = 1 through 5)
- `/` - Step values (e.g., `*/5` = every 5th value)

### Common Examples

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every day at 3:00 AM | `0 3 * * *` | Standard daily refresh |
| Every 4 hours | `0 */4 * * *` | Frequent updates |
| Twice daily (midnight & noon) | `0 0,12 * * *` | Morning and evening |
| Weekdays at 8:30 AM | `30 8 * * 1-5` | Business days only |
| Mon/Wed/Fri at 6:00 PM | `0 18 * * 1,3,5` | Specific weekdays |
| Every 15 minutes | `*/15 * * * *` | Very frequent updates |
| First day of month at midnight | `0 0 1 * *` | Monthly refresh |
| Every 6 hours starting at 2 AM | `0 2-23/6 * * *` | 2 AM, 8 AM, 2 PM, 8 PM |

## Usage

### Setting Up Schedules

1. Navigate to **Settings → Plugins → EPG Refresh Scheduler → Settings**
2. For each EPG source you want to schedule:
   - Enable the schedule by checking **Enable Schedule for: [EPG Name]**
   - Enter a cron expression in **Schedule for: [EPG Name]**
3. Click **Save Settings**

### Available Actions

Navigate to **Settings → Plugins → EPG Refresh Scheduler** and use these actions:

#### 🔄 Refresh All Scheduled EPGs Now
Immediately triggers a refresh for all EPG sources that have schedules enabled. Useful for testing or forcing an update.

#### 📅 View Active Schedules
Displays all currently active EPG refresh schedules with their cron expressions.

#### ✓ Validate All Schedules
Checks if all configured cron expressions are valid. Helps identify configuration errors.

#### ⏰ Show Next Run Times
Shows the next scheduled run time for each EPG, including how long until the next refresh.

## How It Works

### Celery Beat Integration

This plugin integrates with Celery Beat (Dispatcharr's task scheduler) to manage EPG refresh schedules:

1. **Schedule Creation** - When you enable a schedule, the plugin creates a `CrontabSchedule` entry and a `PeriodicTask` that calls `apps.epg.tasks.refresh_epg_source`
2. **Automatic Execution** - Celery Beat monitors the schedules and automatically triggers EPG refreshes at the specified times
3. **Background Processing** - All refreshes run in the background without blocking the UI
4. **Cleanup** - When you disable a schedule or unload the plugin, all tasks are automatically removed

### Task Naming

Scheduled tasks are named: `epg_refresh_scheduler_epg_{epg_id}`

You can view these tasks in the Django admin if needed (requires superuser access).

## Troubleshooting

### Schedule Not Running

**Problem:** EPG doesn't refresh at the scheduled time

**Solutions:**
1. Verify the schedule is enabled in plugin settings
2. Check that the EPG source itself is active (not disabled in M3U & EPG Manager)
3. Validate the cron expression using the "Validate All Schedules" action
4. Check Celery Beat logs: `docker logs dispatcharr | grep celery`
5. Ensure Celery Beat is running: `docker exec dispatcharr ps aux | grep beat`

### Invalid Cron Expression

**Problem:** Error when saving settings

**Solutions:**
1. Verify your cron expression has exactly 5 fields separated by spaces
2. Check that values are within valid ranges
3. Use the "Validate All Schedules" action to identify the problematic expression
4. Refer to the cron examples above

### Plugin Not Visible

**Problem:** Plugin doesn't appear in the Plugins page

**Solutions:**
1. Ensure the plugin folder is in `/data/plugins/epg_refresh_scheduler/`
2. Check that `plugin.py` exists and contains the `Plugin` class
3. Restart Dispatcharr: `docker restart dispatcharr`
4. Check logs for import errors: `docker logs dispatcharr`

### Schedules Not Persisting

**Problem:** Schedules disappear after restart

**Solutions:**
1. Ensure the plugin is **enabled** (toggle switch on the plugin card)
2. Verify settings are saved (click Save Settings after changes)
3. Check database connectivity
4. Review Dispatcharr logs for errors

## Advanced Usage

### Staggered Refreshes

To avoid refreshing all EPGs simultaneously (which can cause load spikes), stagger your schedules:

```
EPG 1: 0 3 * * *   (3:00 AM)
EPG 2: 0 4 * * *   (4:00 AM)
EPG 3: 0 5 * * *   (5:00 AM)
```

Or use minute offsets:

```
EPG 1: 0 3 * * *   (3:00 AM)
EPG 2: 15 3 * * *  (3:15 AM)
EPG 3: 30 3 * * *  (3:30 AM)
```

### High-Frequency Updates

For EPGs that update frequently (like sports channels):

```
*/30 * * * *    (Every 30 minutes)
*/15 * * * *    (Every 15 minutes)
0,30 * * * *    (On the hour and half-hour)
```

### Combining with Built-in Intervals

You can use both:
- **This plugin** for scheduled refreshes at specific times
- **Built-in refresh interval** as a fallback or for different purposes

However, be aware that both will trigger refreshes, so you may want to disable the built-in interval if using this plugin.

## Best Practices

1. **Test First** - Use "Show Next Run Times" to verify schedules before relying on them
2. **Stagger Updates** - Don't schedule all EPGs at the same time
3. **Consider Time Zones** - All times are in UTC (Dispatcharr's default)
4. **Monitor Performance** - Very frequent updates can impact performance
5. **Backup Settings** - Document your cron expressions in case you need to reconfigure
6. **Use Validation** - Always validate expressions before saving

## Technical Details

### Dependencies

- `croniter` - For parsing and validating cron expressions
- `django-celery-beat` - For managing Celery Beat schedules (already included in Dispatcharr)

### Database Tables Used

- `apps_epg_epgsource` - EPG source data
- `apps_plugins_pluginsettings` - Plugin configuration
- `django_celery_beat_periodictask` - Scheduled tasks
- `django_celery_beat_crontabschedule` - Cron schedules

### API Integration

The plugin calls `apps.epg.tasks.refresh_epg_source` which is Dispatcharr's built-in task for refreshing individual EPG sources.

## Version History

### v1.0.0 (Initial Release)
- Cron-based scheduling for EPG refreshes
- Support for `/` and `,` operators
- Individual schedules per EPG source
- Real-time schedule validation
- Next run time preview
- Manual refresh trigger
- Active schedule viewer

## Contributing

Found a bug or have a suggestion? Please submit an issue or pull request!

## License

This plugin follows the same license as Dispatcharr:
**CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike 4.0)

- ✅ Share and adapt the plugin
- ✅ Give appropriate credit
- ❌ No commercial use
- ✅ Share modifications under the same license

## Credits

- **Dispatcharr Team** - For creating an excellent IPTV management platform
- **Backup Plugin Author (mjcocat)** - For the scheduling reference implementation
- **Community Contributors** - For testing and feedback

## Support

- **Dispatcharr Documentation:** https://dispatcharr.github.io/Dispatcharr-Docs/
- **Dispatcharr GitHub:** https://github.com/Dispatcharr/Dispatcharr
- **Discord:** Join the Dispatcharr community

---

Made with ❤️ for the Dispatcharr community

**Note:** This plugin requires Dispatcharr v0.9.0 or higher with the plugin framework enabled.
