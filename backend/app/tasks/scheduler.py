"""
Nachos Replay for Guaca - Background Task Scheduler
Handles periodic tasks like file monitoring and cleanup.
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scan_new_replays():
    """Scan for new replay files from Guacamole."""
    logger.info("Starting replay scan...")
    
    try:
        from app.database import async_session_maker
        from app.services.replay_service import ReplayService
        
        async with async_session_maker() as db:
            service = ReplayService(db)
            imported = await service.scan_for_new_replays()
            
            if imported:
                logger.info(f"Imported {len(imported)} new replays")
                await db.commit()
            else:
                logger.debug("No new replays found")
                
    except Exception as e:
        logger.error(f"Error scanning replays: {e}")


async def archive_old_replays():
    """Archive replays older than retention period."""
    logger.info("Starting replay archival...")
    
    try:
        from app.database import async_session_maker
        from app.services.replay_service import ReplayService
        
        async with async_session_maker() as db:
            service = ReplayService(db)
            count = await service.archive_old_replays()
            
            if count > 0:
                logger.info(f"Archived {count} old replays")
                await db.commit()
                
    except Exception as e:
        logger.error(f"Error archiving replays: {e}")


async def cleanup_expired_tokens():
    """Clean up expired blacklisted tokens."""
    logger.info("Cleaning up expired tokens...")
    
    try:
        from sqlalchemy import delete
        from app.database import async_session_maker
        from app.models import TokenBlacklist
        
        async with async_session_maker() as db:
            result = await db.execute(
                delete(TokenBlacklist).where(
                    TokenBlacklist.expires_at < datetime.now(timezone.utc)
                )
            )
            
            if result.rowcount > 0:
                logger.info(f"Cleaned up {result.rowcount} expired tokens")
                await db.commit()
                
    except Exception as e:
        logger.error(f"Error cleaning up tokens: {e}")


def start_scheduler():
    """Start the background task scheduler."""
    # Scan for new replays every 5 minutes
    scheduler.add_job(
        scan_new_replays,
        trigger=IntervalTrigger(minutes=5),
        id="scan_replays",
        name="Scan for new replays",
        replace_existing=True
    )
    
    # Archive old replays daily at 2 AM
    scheduler.add_job(
        archive_old_replays,
        trigger=CronTrigger(hour=2, minute=0),
        id="archive_replays",
        name="Archive old replays",
        replace_existing=True
    )
    
    # Clean up expired tokens every hour
    scheduler.add_job(
        cleanup_expired_tokens,
        trigger=IntervalTrigger(hours=1),
        id="cleanup_tokens",
        name="Clean up expired tokens",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started with 3 jobs")


def stop_scheduler():
    """Stop the background task scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped")
