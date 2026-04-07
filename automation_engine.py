import logging
import time
import gevent
from datetime import datetime
from extensions import db

logger = logging.getLogger(__name__)

class AutomationEngine:
    """
    The Temporal Engine.
    Manages reminders, scheduled reports, and background system maintenance.
    """
    def __init__(self):
        self.task_queue = []
        self.is_running = True
        logger.info("Automation Engine: Temporal sync active.")

    def start(self):
        """Spawns the background monitor using Gevent."""
        gevent.spawn(self._monitor_tasks)

    def create_task(self, task_type, payload, trigger_time):
        """
        Schedules a new intelligence task.
        :param task_type: 'email_report', 'cleanup', 'reminder'
        :param payload: Dictionary of data needed for the task
        :param trigger_time: datetime object for when to execute
        """
        task = {
            "type": task_type,
            "payload": payload,
            "trigger_time": trigger_time,
            "id": int(time.time() * 1000)
        }
        self.task_queue.append(task)
        logger.info(f"Task {task['id']} queued for {trigger_time}")

    def _monitor_tasks(self):
        """The main loop that checks for pending actions."""
        from email_service import email_service # Local import to avoid loops
        
        while self.is_running:
            now = datetime.now()
            # Find tasks ready to execute
            executable_tasks = [t for t in self.task_queue if t['trigger_time'] <= now]
            
            for task in executable_tasks:
                try:
                    logger.info(f"Executing task: {task['type']}")
                    if task['type'] == 'email_report':
                        email_service.send_email(
                            recipient=task['payload']['email'],
                            subject="Automated Reminder",
                            body=task['payload']['content']
                        )
                    # Remove from queue after success
                    self.task_queue.remove(task)
                except Exception as e:
                    logger.error(f"Task Execution Error: {e}")
            
            gevent.sleep(10) # Wait 10 seconds between checks (Gevent friendly)

# Global Singleton
automation_engine = AutomationEngine()