# Quick Installation Guide

## Step 1: Upload Plugin

1. Download the plugin ZIP file
2. Navigate to **Settings → Plugins** in Dispatcharr
3. Click **Import Plugin**
4. Select the ZIP file
5. Enable the plugin when prompted

## Step 2: Restart Dispatcharr

**CRITICAL:** Restart the container for the plugin to fully activate:

```bash
docker restart dispatcharr
```

## Step 3: Configure

1. Go to **Settings → Plugins → EPG Refresh Scheduler → Settings**
2. Select your timezone
3. Enable schedules for your EPG sources
4. Enter cron expressions for each EPG
5. Click **Save Settings**

## Step 4: Verify

Use the **Show Next Run Times** action to verify your schedules are configured correctly.

## Example Configuration

For an EPG that should refresh every day at 3:00 AM in your local timezone:

1. Select your timezone (e.g., "America/New_York")
2. Check **Enable Schedule for: [Your EPG Name]**
3. Enter: `0 3 * * *`
4. Save Settings

## No Dependencies Required!

This plugin uses django-celery-beat which is already included in Dispatcharr. No additional packages need to be installed!

## Troubleshooting

If the plugin doesn't appear after installation:
1. Check that the folder structure is correct: `/data/plugins/epg_refresh_scheduler/plugin.py`
2. Restart Dispatcharr
3. Check logs: `docker logs dispatcharr`

Need help? Refer to the full README.md for detailed documentation.
