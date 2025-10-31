"""
EPG Refresh Scheduler Plugin for Dispatcharr
No external dependencies - uses built-in django-celery-beat
"""

import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Plugin:
    """EPG Refresh Scheduler Plugin"""
    
    # Plugin metadata
    key = "epg_refresh_scheduler"
    name = "EPG Refresh Scheduler"
    version = "1.3.0"
    description = "Schedule M3U playlist and EPG data refreshes with cron expressions. Example \"0 3 * * *\" to run everyday at 3am."
    author = "Community Plugin"
    
    def __init__(self):
        """Initialize the plugin"""
        self.logger = logger
        self.celery_app = None
        self.scheduled_tasks = {}
        
    @property
    def settings(self) -> Dict[str, Any]:
        """Plugin settings - returns empty dict as settings are managed by Dispatcharr"""
        return {}
    
    @property
    def fields(self) -> List[Dict[str, Any]]:
        """Configuration fields"""
        fields = [
            {
                "id": "timezone",
                "type": "select",
                "label": "Timezone",
                "description": "Select your timezone. Schedule times below will be converted to UTC.",
                "default": "UTC",
                "options": [
                    {"value": "UTC", "label": "UTC (Coordinated Universal Time)"},
                    {"value": "US/Eastern", "label": "US/Eastern (EST/EDT) - New York"},
                    {"value": "US/Central", "label": "US/Central (CST/CDT) - Chicago"},
                    {"value": "US/Mountain", "label": "US/Mountain (MST/MDT) - Denver"},
                    {"value": "US/Pacific", "label": "US/Pacific (PST/PDT) - Los Angeles"},
                    {"value": "America/Phoenix", "label": "America/Phoenix (MST - no DST)"},
                    {"value": "America/Anchorage", "label": "America/Anchorage (AKST/AKDT)"},
                    {"value": "Pacific/Honolulu", "label": "Pacific/Honolulu (HST)"},
                    {"value": "Europe/London", "label": "Europe/London (GMT/BST)"},
                    {"value": "Europe/Paris", "label": "Europe/Paris (CET/CEST)"},
                    {"value": "Europe/Berlin", "label": "Europe/Berlin (CET/CEST)"},
                    {"value": "Europe/Rome", "label": "Europe/Rome (CET/CEST)"},
                    {"value": "Europe/Madrid", "label": "Europe/Madrid (CET/CEST)"},
                    {"value": "Europe/Amsterdam", "label": "Europe/Amsterdam (CET/CEST)"},
                    {"value": "Europe/Brussels", "label": "Europe/Brussels (CET/CEST)"},
                    {"value": "Europe/Vienna", "label": "Europe/Vienna (CET/CEST)"},
                    {"value": "Europe/Warsaw", "label": "Europe/Warsaw (CET/CEST)"},
                    {"value": "Europe/Athens", "label": "Europe/Athens (EET/EEST)"},
                    {"value": "Europe/Helsinki", "label": "Europe/Helsinki (EET/EEST)"},
                    {"value": "Europe/Istanbul", "label": "Europe/Istanbul (TRT)"},
                    {"value": "Europe/Moscow", "label": "Europe/Moscow (MSK)"},
                    {"value": "Asia/Dubai", "label": "Asia/Dubai (GST)"},
                    {"value": "Asia/Kolkata", "label": "Asia/Kolkata (IST)"},
                    {"value": "Asia/Shanghai", "label": "Asia/Shanghai (CST)"},
                    {"value": "Asia/Tokyo", "label": "Asia/Tokyo (JST)"},
                    {"value": "Asia/Seoul", "label": "Asia/Seoul (KST)"},
                    {"value": "Asia/Singapore", "label": "Asia/Singapore (SGT)"},
                    {"value": "Asia/Hong_Kong", "label": "Asia/Hong_Kong (HKT)"},
                    {"value": "Australia/Sydney", "label": "Australia/Sydney (AEDT/AEST)"},
                    {"value": "Australia/Melbourne", "label": "Australia/Melbourne (AEDT/AEST)"},
                    {"value": "Australia/Brisbane", "label": "Australia/Brisbane (AEST)"},
                    {"value": "Australia/Perth", "label": "Australia/Perth (AWST)"},
                    {"value": "Pacific/Auckland", "label": "Pacific/Auckland (NZDT/NZST)"}
                ]
            }
        ]
        
        try:
            # Add M3U Accounts (no header)
            m3u_accounts = self._get_m3u_accounts()
            if m3u_accounts:
                for m3u in m3u_accounts:
                    # Skip "custom" account
                    if m3u.name.lower() == 'custom':
                        continue
                    
                    # Get type safely
                    m3u_type = getattr(m3u, 'type', getattr(m3u, 'source_type', 'M3U'))
                    
                    fields.extend([
                        {
                            "id": f"m3u_{m3u.id}_enabled",
                            "type": "boolean",
                            "label": f"M3U - {m3u.name}",
                            "description": f"ID: {m3u.id} | Type: {m3u_type} | Examples: 0 2 * * * (2am) | 0 */12 * * * (every 12h)",
                            "default": False
                        },
                        {
                            "id": f"m3u_{m3u.id}_schedule",
                            "type": "text",
                            "label": f"  └─ Schedule",
                            "description": "Cron format: minute hour day month day_of_week",
                            "placeholder": "0 2 * * *"
                        }
                    ])
            
            # Add EPG Sources (no header)
            epg_sources = self._get_epg_sources()
            if epg_sources:
                for epg in epg_sources:
                    # Truncate URL for display
                    url_display = epg.url[:50] + "..." if len(epg.url) > 50 else epg.url
                    
                    fields.extend([
                        {
                            "id": f"epg_{epg.id}_enabled",
                            "type": "boolean",
                            "label": f"EPG - {epg.name}",
                            "description": f"ID: {epg.id} | Source: {url_display} | Examples: 0 3 * * * (3am) | 0 */6 * * * (every 6h)",
                            "default": False
                        },
                        {
                            "id": f"epg_{epg.id}_schedule",
                            "type": "text",
                            "label": f"  └─ Schedule",
                            "description": "Cron format: minute hour day month day_of_week",
                            "placeholder": "0 3 * * *"
                        }
                    ])
            
            # Show warning if nothing found
            if not m3u_accounts and not epg_sources:
                fields.append({
                    "id": "no_sources",
                    "type": "info",
                    "label": "⚠️ No Sources Found",
                    "description": "Add M3U accounts or EPG sources in M3U & EPG Manager first."
                })
                
        except Exception as e:
            self.logger.error(f"Error generating fields: {e}", exc_info=True)
            fields.append({
                "id": "error",
                "type": "info",
                "label": "❌ Error",
                "description": f"Could not load EPG sources: {str(e)}"
            })
        
        return fields
    
    @property
    def actions(self) -> List[Dict[str, Any]]:
        """Available actions"""
        return [
            {
                "id": "sync_schedules",
                "label": "🔄 Sync Schedules",
                "description": "Reload and sync all schedules from settings"
            },
            {
                "id": "view_schedules",
                "label": "📅 View Active Schedules",
                "description": "Show active Celery Beat schedules"
            }
        ]
        
    def on_load(self, context: Dict[str, Any]) -> None:
        """Called when plugin is loaded"""
        self.logger.info(f"Loading {self.name} v{self.version}")
        self.celery_app = context.get("celery_app")
        self._setup_schedules(context)
        
    def on_unload(self) -> None:
        """Called when plugin is unloaded"""
        self.logger.info(f"Unloading {self.name}")
        self._cleanup_schedules()
        
    def _get_epg_sources(self):
        """Get all active non-dummy EPG sources"""
        try:
            from apps.epg.models import EPGSource
            return EPGSource.objects.exclude(source_type='dummy').filter(is_active=True)
        except Exception as e:
            self.logger.error(f"Error fetching EPG sources: {e}")
            return []
    
    def _get_m3u_accounts(self):
        """Get all active M3U accounts"""
        try:
            from apps.m3u.models import M3UAccount
            return M3UAccount.objects.filter(is_active=True)
        except Exception as e:
            self.logger.error(f"Error fetching M3U accounts: {e}")
            return []
    
    def _get_m3u_accounts(self):
        """Get all active M3U accounts"""
        try:
            from apps.m3u.models import M3UAccount
            return M3UAccount.objects.filter(is_active=True).order_by('name')
        except Exception as e:
            self.logger.error(f"Error fetching M3U accounts: {e}")
            return []
    
    def _setup_schedules(self, context):
        """Set up schedules on load"""
        if not self.celery_app:
            return
            
        try:
            settings = context.get("settings", {})
            user_timezone = settings.get("timezone", "UTC")
            
            # Setup M3U account schedules
            m3u_accounts = self._get_m3u_accounts()
            for m3u in m3u_accounts:
                enabled = settings.get(f"m3u_{m3u.id}_enabled", False)
                schedule = settings.get(f"m3u_{m3u.id}_schedule", "")
                
                if enabled and schedule:
                    self._create_or_update_m3u_schedule(m3u, schedule, user_timezone)
            
            # Setup EPG schedules
            epg_sources = self._get_epg_sources()
            for epg in epg_sources:
                enabled = settings.get(f"epg_{epg.id}_enabled", False)
                schedule = settings.get(f"epg_{epg.id}_schedule", "")
                
                if enabled and schedule:
                    self._create_or_update_epg_schedule(epg, schedule, user_timezone)
                    
        except Exception as e:
            self.logger.error(f"Error setting up schedules: {e}", exc_info=True)
    
    def _create_or_update_epg_schedule(self, epg, cron_expr: str, user_timezone: str = "UTC"):
        """Create or update a Celery Beat schedule for EPG refresh
        
        Args:
            epg: EPG source object
            cron_expr: Cron expression in user's timezone
            user_timezone: User's timezone (default UTC)
        """
        try:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule
            from django.db import transaction
            import json
            import pytz
            from datetime import datetime, time as dt_time
            
            # Validate cron
            if not self._validate_cron(cron_expr):
                self.logger.error(f"Invalid cron: {cron_expr}")
                return
            
            # Normalize cron expression (convert 0/X to */X)
            cron_expr = self._normalize_cron(cron_expr)
            
            # Parse cron (minute hour day month day_of_week)
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                return
            
            minute, hour, day_of_month, month_of_year, day_of_week = parts
            
            # Convert time from user's timezone to UTC if needed
            # Note: Only converts when hour and minute are simple numbers
            # Expressions like */6 or 0,12 stay as-is (no conversion)
            if user_timezone != "UTC" and minute.isdigit() and hour.isdigit():
                try:
                    user_tz = pytz.timezone(user_timezone)
                    utc_tz = pytz.utc
                    
                    # Create a datetime in user's timezone
                    user_time = datetime.now(user_tz).replace(
                        hour=int(hour),
                        minute=int(minute),
                        second=0,
                        microsecond=0
                    )
                    
                    # Convert to UTC
                    utc_time = user_time.astimezone(utc_tz)
                    
                    # Extract UTC hour and minute
                    minute = str(utc_time.minute)
                    hour = str(utc_time.hour)
                    
                    self.logger.info(
                        f"Converted schedule for {epg.name}: "
                        f"{cron_expr} ({user_timezone}) → "
                        f"{minute} {hour} {day_of_month} {month_of_year} {day_of_week} (UTC)"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Timezone conversion failed: {e}, using original times")
            elif user_timezone != "UTC" and (not minute.isdigit() or not hour.isdigit()):
                self.logger.info(
                    f"Schedule for {epg.name} uses complex expression: {cron_expr}. "
                    f"No timezone conversion applied (stays UTC-relative)"
                )
            
            with transaction.atomic():
                # Create crontab schedule in UTC
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute=minute,
                    hour=hour,
                    day_of_month=day_of_month,
                    month_of_year=month_of_year,
                    day_of_week=day_of_week,
                    timezone='UTC'
                )
                
                # Create periodic task
                task_name = f"epg_refresh_scheduler_epg_{epg.id}"
                
                task, created = PeriodicTask.objects.update_or_create(
                    name=task_name,
                    defaults={
                        'crontab': schedule,
                        'task': 'apps.epg.tasks.refresh_all_epg_data',
                        'args': json.dumps([]),
                        'enabled': True,
                        'description': f'Refresh triggered by: {epg.name} ({user_timezone})'
                    }
                )
                
                action = "Created" if created else "Updated"
                self.logger.info(f"{action} schedule for {epg.name}: {minute} {hour} * * * UTC")
                self.scheduled_tasks[epg.id] = task_name
                
        except Exception as e:
            self.logger.error(f"Error creating EPG schedule: {e}", exc_info=True)
    
    def _create_or_update_m3u_schedule(self, m3u, cron_expr: str, user_timezone: str = "UTC"):
        """Create or update a Celery Beat schedule for M3U refresh
        
        Args:
            m3u: M3U account object
            cron_expr: Cron expression in user's timezone
            user_timezone: User's timezone (default UTC)
        """
        try:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule
            from django.db import transaction
            import json
            import pytz
            from datetime import datetime, time as dt_time
            
            # Validate cron
            if not self._validate_cron(cron_expr):
                self.logger.error(f"Invalid cron: {cron_expr}")
                return
            
            # Normalize cron expression (convert 0/X to */X)
            cron_expr = self._normalize_cron(cron_expr)
            
            # Parse cron (minute hour day month day_of_week)
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                return
            
            minute, hour, day_of_month, month_of_year, day_of_week = parts
            
            # Convert time from user's timezone to UTC if needed
            # Note: Only converts when hour and minute are simple numbers
            # Expressions like */6 or 0,12 stay as-is (no conversion)
            if user_timezone != "UTC" and minute.isdigit() and hour.isdigit():
                try:
                    user_tz = pytz.timezone(user_timezone)
                    utc_tz = pytz.utc
                    
                    # Create a datetime in user's timezone
                    user_time = datetime.now(user_tz).replace(
                        hour=int(hour),
                        minute=int(minute),
                        second=0,
                        microsecond=0
                    )
                    
                    # Convert to UTC
                    utc_time = user_time.astimezone(utc_tz)
                    
                    # Extract UTC hour and minute
                    minute = str(utc_time.minute)
                    hour = str(utc_time.hour)
                    
                    self.logger.info(
                        f"Converted M3U schedule for {m3u.name}: "
                        f"{cron_expr} ({user_timezone}) → "
                        f"{minute} {hour} {day_of_month} {month_of_year} {day_of_week} (UTC)"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Timezone conversion failed: {e}, using original times")
            elif user_timezone != "UTC" and (not minute.isdigit() or not hour.isdigit()):
                self.logger.info(
                    f"M3U schedule for {m3u.name} uses complex expression: {cron_expr}. "
                    f"No timezone conversion applied (stays UTC-relative)"
                )
            
            with transaction.atomic():
                # Create crontab schedule in UTC
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute=minute,
                    hour=hour,
                    day_of_month=day_of_month,
                    month_of_year=month_of_year,
                    day_of_week=day_of_week,
                    timezone='UTC'
                )
                
                # Create periodic task for M3U refresh
                task_name = f"epg_refresh_scheduler_m3u_{m3u.id}"
                
                task, created = PeriodicTask.objects.update_or_create(
                    name=task_name,
                    defaults={
                        'crontab': schedule,
                        'task': 'apps.m3u.tasks.refresh_single_m3u_account',
                        'args': json.dumps([m3u.id]),
                        'enabled': True,
                        'description': f'M3U refresh triggered by scheduler: {m3u.name} ({user_timezone})'
                    }
                )
                
                action = "Created" if created else "Updated"
                self.logger.info(f"{action} M3U schedule for {m3u.name}: {minute} {hour} * * * UTC")
                self.scheduled_tasks[f"m3u_{m3u.id}"] = task_name
                
        except Exception as e:
            self.logger.error(f"Error creating M3U schedule: {e}", exc_info=True)
    
    def _validate_cron(self, cron_expr: str) -> bool:
        """Validate cron expression"""
        try:
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                self.logger.error(f"Cron must have 5 parts, got {len(parts)}: '{cron_expr}'")
                return False
            
            minute, hour, day_of_month, month_of_year, day_of_week = parts
            
            # Valid characters: digits, *, /, -, ,
            valid_chars = set('0123456789*/-,')
            for i, part in enumerate(parts):
                invalid_chars = set(part) - valid_chars
                if invalid_chars:
                    self.logger.error(f"Invalid characters in cron part {i}: {invalid_chars} in '{part}'")
                    return False
            
            # Basic range checks (only for simple digit values)
            try:
                if minute.isdigit() and not (0 <= int(minute) <= 59):
                    self.logger.error(f"Minute must be 0-59, got {minute}")
                    return False
                if hour.isdigit() and not (0 <= int(hour) <= 23):
                    self.logger.error(f"Hour must be 0-23, got {hour}")
                    return False
                if day_of_month.isdigit() and not (1 <= int(day_of_month) <= 31):
                    self.logger.error(f"Day must be 1-31, got {day_of_month}")
                    return False
                if month_of_year.isdigit() and not (1 <= int(month_of_year) <= 12):
                    self.logger.error(f"Month must be 1-12, got {month_of_year}")
                    return False
                if day_of_week.isdigit() and not (0 <= int(day_of_week) <= 6):
                    self.logger.error(f"Day of week must be 0-6, got {day_of_week}")
                    return False
            except ValueError as e:
                self.logger.error(f"Invalid numeric value in cron: {e}")
                return False
            
            self.logger.debug(f"Cron expression validated: '{cron_expr}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating cron '{cron_expr}': {e}")
            return False
    
    def _normalize_cron(self, cron_expr: str) -> str:
        """Normalize cron expression (convert 0/X to */X)"""
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return cron_expr
        
        normalized = []
        for part in parts:
            # Convert 0/X to */X (e.g., 0/5 becomes */5)
            if part.startswith('0/'):
                normalized.append('*' + part[1:])
            else:
                normalized.append(part)
        
        result = ' '.join(normalized)
        if result != cron_expr:
            self.logger.info(f"Normalized cron: '{cron_expr}' → '{result}'")
        
        return result
    
    def _cleanup_schedules(self):
        """Clean up all scheduled tasks"""
        try:
            from django_celery_beat.models import PeriodicTask
            
            for task_name in self.scheduled_tasks.values():
                PeriodicTask.objects.filter(name=task_name).delete()
                self.logger.info(f"Deleted task: {task_name}")
                
            self.scheduled_tasks.clear()
            
        except Exception as e:
            self.logger.error(f"Error cleaning up: {e}", exc_info=True)
    
    def _delete_epg_schedule(self, epg_id: int):
        """Delete schedule for specific EPG"""
        try:
            from django_celery_beat.models import PeriodicTask
            
            task_name = f"epg_refresh_scheduler_epg_{epg_id}"
            deleted = PeriodicTask.objects.filter(name=task_name).delete()[0]
            
            if deleted > 0:
                self.logger.info(f"Deleted schedule for EPG {epg_id}")
                if epg_id in self.scheduled_tasks:
                    del self.scheduled_tasks[epg_id]
                    
        except Exception as e:
            self.logger.error(f"Error deleting EPG schedule: {e}", exc_info=True)
    
    def _delete_m3u_schedule(self, m3u_id: int):
        """Delete schedule for specific M3U account"""
        try:
            from django_celery_beat.models import PeriodicTask
            
            task_name = f"epg_refresh_scheduler_m3u_{m3u_id}"
            deleted = PeriodicTask.objects.filter(name=task_name).delete()[0]
            
            if deleted > 0:
                self.logger.info(f"Deleted M3U schedule for account {m3u_id}")
                key = f"m3u_{m3u_id}"
                if key in self.scheduled_tasks:
                    del self.scheduled_tasks[key]
                    
        except Exception as e:
            self.logger.error(f"Error deleting M3U schedule: {e}", exc_info=True)
    
    def save_settings(self, settings: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Save settings and sync schedules"""
        try:
            self.logger.info(f"Saving settings: {settings}")
            
            # Get timezone setting
            user_timezone = settings.get("timezone", "UTC")
            
            m3u_synced = []
            m3u_removed = []
            epg_synced = []
            epg_removed = []
            
            # Process M3U accounts
            m3u_accounts = self._get_m3u_accounts()
            for m3u in m3u_accounts:
                enabled_key = f"m3u_{m3u.id}_enabled"
                schedule_key = f"m3u_{m3u.id}_schedule"
                
                is_enabled = settings.get(enabled_key, False)
                if isinstance(is_enabled, str):
                    is_enabled = is_enabled.lower() in ('true', '1', 'yes', 'on')
                
                cron_schedule = settings.get(schedule_key, "").strip()
                
                self.logger.info(f"M3U {m3u.name}: enabled={is_enabled}, schedule='{cron_schedule}', tz={user_timezone}")
                
                if is_enabled and cron_schedule:
                    if not self._validate_cron(cron_schedule):
                        return {
                            "success": False,
                            "message": f"Invalid cron for M3U '{m3u.name}': {cron_schedule}"
                        }
                    self._create_or_update_m3u_schedule(m3u, cron_schedule, user_timezone)
                    m3u_synced.append(m3u.name)
                else:
                    self._delete_m3u_schedule(m3u.id)
                    if not is_enabled:
                        m3u_removed.append(m3u.name)
            
            # Process EPG sources
            epg_sources = self._get_epg_sources()
            for epg in epg_sources:
                enabled_key = f"epg_{epg.id}_enabled"
                schedule_key = f"epg_{epg.id}_schedule"
                
                is_enabled = settings.get(enabled_key, False)
                if isinstance(is_enabled, str):
                    is_enabled = is_enabled.lower() in ('true', '1', 'yes', 'on')
                
                cron_schedule = settings.get(schedule_key, "").strip()
                
                self.logger.info(f"EPG {epg.name}: enabled={is_enabled}, schedule='{cron_schedule}', tz={user_timezone}")
                
                if is_enabled and cron_schedule:
                    if not self._validate_cron(cron_schedule):
                        return {
                            "success": False,
                            "message": f"Invalid cron for EPG '{epg.name}': {cron_schedule}"
                        }
                    self._create_or_update_epg_schedule(epg, cron_schedule, user_timezone)
                    epg_synced.append(epg.name)
                else:
                    self._delete_epg_schedule(epg.id)
                    if not is_enabled:
                        epg_removed.append(epg.name)
            
            # Build success message
            messages = [f"✅ Settings saved! (Timezone: {user_timezone})"]
            if m3u_synced:
                messages.append(f"📺 M3U Activated ({len(m3u_synced)}): {', '.join(m3u_synced)}")
            if m3u_removed:
                messages.append(f"📺 M3U Deactivated ({len(m3u_removed)}): {', '.join(m3u_removed)}")
            if epg_synced:
                messages.append(f"📅 EPG Activated ({len(epg_synced)}): {', '.join(epg_synced)}")
            if epg_removed:
                messages.append(f"📅 EPG Deactivated ({len(epg_removed)}): {', '.join(epg_removed)}")
            
            return {
                "success": True,
                "message": "\n".join(messages)
            }
            
        except Exception as e:
            self.logger.error(f"Error saving: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def run(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action"""
        logger = context.get("logger", self.logger)
        settings = context.get("settings", {})
        
        try:
            if action == "sync_schedules":
                return self._sync_schedules(settings, logger)
            elif action == "view_schedules":
                return self._view_schedules(logger)
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in action {action}: {e}", exc_info=True)
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def _sync_schedules(self, settings: Dict[str, Any], logger) -> Dict[str, Any]:
        """Sync schedules from settings"""
        try:
            user_timezone = settings.get("timezone", "UTC")
            m3u_synced = []
            m3u_removed = []
            epg_synced = []
            epg_removed = []
            
            # Sync M3U accounts
            m3u_accounts = self._get_m3u_accounts()
            for m3u in m3u_accounts:
                enabled = settings.get(f"m3u_{m3u.id}_enabled", False)
                schedule = settings.get(f"m3u_{m3u.id}_schedule", "").strip()
                
                logger.info(f"Syncing M3U {m3u.name}: enabled={enabled}, schedule='{schedule}', tz={user_timezone}")
                
                if enabled and schedule:
                    if self._validate_cron(schedule):
                        self._create_or_update_m3u_schedule(m3u, schedule, user_timezone)
                        m3u_synced.append(m3u.name)
                else:
                    self._delete_m3u_schedule(m3u.id)
                    m3u_removed.append(m3u.name)
            
            # Sync EPG sources
            epg_sources = self._get_epg_sources()
            for epg in epg_sources:
                enabled = settings.get(f"epg_{epg.id}_enabled", False)
                schedule = settings.get(f"epg_{epg.id}_schedule", "").strip()
                
                logger.info(f"Syncing EPG {epg.name}: enabled={enabled}, schedule='{schedule}', tz={user_timezone}")
                
                if enabled and schedule:
                    if self._validate_cron(schedule):
                        self._create_or_update_epg_schedule(epg, schedule, user_timezone)
                        epg_synced.append(epg.name)
                else:
                    self._delete_epg_schedule(epg.id)
                    epg_removed.append(epg.name)
            
            messages = []
            if m3u_synced:
                messages.append(f"📺 M3U Synced ({len(m3u_synced)}, {user_timezone}): {', '.join(m3u_synced)}")
            if m3u_removed:
                messages.append(f"📺 M3U Removed ({len(m3u_removed)}): {', '.join(m3u_removed)}")
            if epg_synced:
                messages.append(f"📅 EPG Synced ({len(epg_synced)}, {user_timezone}): {', '.join(epg_synced)}")
            if epg_removed:
                messages.append(f"📅 EPG Removed ({len(epg_removed)}): {', '.join(epg_removed)}")
            if not m3u_synced and not m3u_removed and not epg_synced and not epg_removed:
                messages.append("ℹ️ No schedules configured")
            
            return {"success": True, "message": "\n".join(messages)}
            
        except Exception as e:
            logger.error(f"Error syncing: {e}", exc_info=True)
            return {"success": False, "message": f"Error: {str(e)}"}
    
    
    def _view_schedules(self, logger) -> Dict[str, Any]:
        """View active schedules"""
        try:
            from django_celery_beat.models import PeriodicTask
            
            m3u_schedules = []
            epg_schedules = []
            
            # Get M3U schedules
            m3u_accounts = self._get_m3u_accounts()
            for m3u in m3u_accounts:
                task_name = f"epg_refresh_scheduler_m3u_{m3u.id}"
                task = PeriodicTask.objects.filter(name=task_name, enabled=True).first()
                
                if task and task.crontab:
                    cron = task.crontab
                    cron_expr = f"{cron.minute} {cron.hour} {cron.day_of_month} {cron.month_of_year} {cron.day_of_week}"
                    m3u_schedules.append(f"  • {m3u.name}: {cron_expr} UTC")
            
            # Get EPG schedules
            epg_sources = self._get_epg_sources()
            for epg in epg_sources:
                task_name = f"epg_refresh_scheduler_epg_{epg.id}"
                task = PeriodicTask.objects.filter(name=task_name, enabled=True).first()
                
                if task and task.crontab:
                    cron = task.crontab
                    cron_expr = f"{cron.minute} {cron.hour} {cron.day_of_month} {cron.month_of_year} {cron.day_of_week}"
                    epg_schedules.append(f"  • {epg.name}: {cron_expr} UTC")
            
            messages = []
            if m3u_schedules:
                messages.append("📺 M3U Account Schedules:")
                messages.extend(m3u_schedules)
            if epg_schedules:
                if m3u_schedules:
                    messages.append("")  # Blank line separator
                messages.append("📅 EPG Source Schedules:")
                messages.extend(epg_schedules)
            
            if not m3u_schedules and not epg_schedules:
                message = "No active schedules"
            else:
                message = "\n".join(messages)
            
            return {"success": True, "message": message}
            
        except Exception as e:
            logger.error(f"Error viewing schedules: {e}", exc_info=True)
            return {"success": False, "message": f"Error: {str(e)}"}
