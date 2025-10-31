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
    version = "1.1.0"
    description = "Schedule EPG refreshes with cron expressions. Zero dependencies."
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
            epg_sources = self._get_epg_sources()
            
            if epg_sources:
                for epg in epg_sources:
                    # Default schedule
                    default_schedule = "0 3 * * *"
                    
                    # Truncate URL for display
                    url_display = epg.url[:50] + "..." if len(epg.url) > 50 else epg.url
                    
                    fields.extend([
                        {
                            "id": f"epg_{epg.id}_enabled",
                            "type": "boolean",
                            "label": f"Enable: {epg.name}",
                            "description": f"ID: {epg.id} | Source: {url_display}",
                            "default": False
                        },
                        {
                            "id": f"epg_{epg.id}_schedule",
                            "type": "text",
                            "label": f"  └─ Schedule",
                            "description": "Cron: minute hour day month day_of_week",
                            "default": default_schedule,
                            "placeholder": "0 3 * * *"
                        }
                    ])
            else:
                fields.append({
                    "id": "no_epgs",
                    "type": "info",
                    "label": "⚠️ No EPG Sources",
                    "description": "Add EPG sources in M3U & EPG Manager first."
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
    
    def _setup_schedules(self, context):
        """Set up schedules on load"""
        if not self.celery_app:
            return
            
        try:
            settings = context.get("settings", {})
            user_timezone = settings.get("timezone", "UTC")
            epg_sources = self._get_epg_sources()
            
            for epg in epg_sources:
                enabled = settings.get(f"epg_{epg.id}_enabled", False)
                schedule = settings.get(f"epg_{epg.id}_schedule", "")
                
                if enabled and schedule:
                    self._create_or_update_schedule(epg, schedule, user_timezone)
                    
        except Exception as e:
            self.logger.error(f"Error setting up schedules: {e}", exc_info=True)
    
    def _create_or_update_schedule(self, epg, cron_expr: str, user_timezone: str = "UTC"):
        """Create or update a Celery Beat schedule
        
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
            
            # Parse cron (minute hour day month day_of_week)
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                return
            
            minute, hour, day_of_month, month_of_year, day_of_week = parts
            
            # Convert time from user's timezone to UTC if needed
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
            self.logger.error(f"Error creating schedule: {e}", exc_info=True)
    
    def _validate_cron(self, cron_expr: str) -> bool:
        """Validate cron expression"""
        try:
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                return False
            
            minute, hour, day_of_month, month_of_year, day_of_week = parts
            
            # Valid characters
            valid_chars = set('0123456789*/-,')
            for part in parts:
                if not all(c in valid_chars for c in part):
                    return False
            
            # Basic range checks
            if minute.isdigit() and not (0 <= int(minute) <= 59):
                return False
            if hour.isdigit() and not (0 <= int(hour) <= 23):
                return False
            if day_of_month.isdigit() and not (1 <= int(day_of_month) <= 31):
                return False
            if month_of_year.isdigit() and not (1 <= int(month_of_year) <= 12):
                return False
            if day_of_week.isdigit() and not (0 <= int(day_of_week) <= 6):
                return False
            
            return True
        except:
            return False
    
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
            self.logger.error(f"Error deleting schedule: {e}", exc_info=True)
    
    def save_settings(self, settings: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Save settings and sync schedules"""
        try:
            self.logger.info(f"Saving settings: {settings}")
            
            # Get timezone setting
            user_timezone = settings.get("timezone", "UTC")
            
            epg_sources = self._get_epg_sources()
            synced = []
            removed = []
            
            for epg in epg_sources:
                enabled_key = f"epg_{epg.id}_enabled"
                schedule_key = f"epg_{epg.id}_schedule"
                
                # Get from submitted settings
                is_enabled = settings.get(enabled_key, False)
                if isinstance(is_enabled, str):
                    is_enabled = is_enabled.lower() in ('true', '1', 'yes', 'on')
                
                cron_schedule = settings.get(schedule_key, "").strip()
                
                self.logger.info(f"EPG {epg.name}: enabled={is_enabled}, schedule='{cron_schedule}', tz={user_timezone}")
                
                if is_enabled and cron_schedule:
                    if not self._validate_cron(cron_schedule):
                        return {
                            "success": False,
                            "message": f"Invalid cron for {epg.name}: {cron_schedule}"
                        }
                    self._create_or_update_schedule(epg, cron_schedule, user_timezone)
                    synced.append(epg.name)
                else:
                    self._delete_epg_schedule(epg.id)
                    if not is_enabled:
                        removed.append(epg.name)
            
            messages = [f"✅ Settings saved! (Timezone: {user_timezone})"]
            if synced:
                messages.append(f"✅ Activated {len(synced)}: {', '.join(synced)}")
            if removed:
                messages.append(f"🗑️ Deactivated {len(removed)}: {', '.join(removed)}")
            
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
            epg_sources = self._get_epg_sources()
            synced = []
            removed = []
            
            for epg in epg_sources:
                enabled = settings.get(f"epg_{epg.id}_enabled", False)
                schedule = settings.get(f"epg_{epg.id}_schedule", "").strip()
                
                logger.info(f"Syncing {epg.name}: enabled={enabled}, schedule='{schedule}', tz={user_timezone}")
                
                if enabled and schedule:
                    if self._validate_cron(schedule):
                        self._create_or_update_schedule(epg, schedule, user_timezone)
                        synced.append(epg.name)
                else:
                    self._delete_epg_schedule(epg.id)
                    removed.append(epg.name)
            
            messages = []
            if synced:
                messages.append(f"✅ Synced {len(synced)} ({user_timezone}): {', '.join(synced)}")
            if removed:
                messages.append(f"🗑️ Removed {len(removed)}: {', '.join(removed)}")
            if not synced and not removed:
                messages.append("ℹ️ No schedules configured")
            
            return {"success": True, "message": "\n".join(messages)}
            
        except Exception as e:
            logger.error(f"Error syncing: {e}", exc_info=True)
            return {"success": False, "message": f"Error: {str(e)}"}
    
    
    def _view_schedules(self, logger) -> Dict[str, Any]:
        """View active schedules"""
        try:
            from django_celery_beat.models import PeriodicTask
            
            schedules = []
            epg_sources = self._get_epg_sources()
            
            for epg in epg_sources:
                task_name = f"epg_refresh_scheduler_epg_{epg.id}"
                task = PeriodicTask.objects.filter(name=task_name, enabled=True).first()
                
                if task and task.crontab:
                    cron = task.crontab
                    cron_expr = f"{cron.minute} {cron.hour} {cron.day_of_month} {cron.month_of_year} {cron.day_of_week}"
                    schedules.append(f"• {epg.name}: {cron_expr}")
            
            if schedules:
                message = "Active Schedules:\n" + "\n".join(schedules)
            else:
                message = "No active schedules"
            
            return {"success": True, "message": message}
            
        except Exception as e:
            logger.error(f"Error viewing schedules: {e}", exc_info=True)
            return {"success": False, "message": f"Error: {str(e)}"}
