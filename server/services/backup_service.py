"""
Database backup service for automatic daily backups
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List
import glob

logger = logging.getLogger(__name__)


class BackupService:
    """Service for automated database backups"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.backup_dir = os.path.join(os.path.dirname(database_path), 'backups')
        self._ensure_backup_directory()
    
    def _ensure_backup_directory(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logger.info(f"Created backup directory: {self.backup_dir}")
    
    def create_backup(self) -> Dict[str, Any]:
        """Create a backup of the database"""
        try:
            if not os.path.exists(self.database_path):
                return {
                    'success': False,
                    'message': f'Database file not found: {self.database_path}'
                }
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"crypto_analyser_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Get record count before backup
            conn = sqlite3.connect(self.database_path)
            record_count = conn.execute("SELECT COUNT(*) FROM bitcoin_prices").fetchone()[0]
            conn.close()
            
            # Create backup using shutil.copy2 to preserve metadata
            shutil.copy2(self.database_path, backup_path)
            
            # Verify backup
            backup_conn = sqlite3.connect(backup_path)
            backup_count = backup_conn.execute("SELECT COUNT(*) FROM bitcoin_prices").fetchone()[0]
            backup_conn.close()
            
            if backup_count == record_count:
                logger.info(f"Database backup created successfully: {backup_filename}")
                return {
                    'success': True,
                    'message': f'Backup created successfully',
                    'backup_file': backup_filename,
                    'backup_path': backup_path,
                    'record_count': record_count,
                    'timestamp': timestamp
                }
            else:
                logger.error(f"Backup verification failed: {record_count} != {backup_count}")
                return {
                    'success': False,
                    'message': 'Backup verification failed - record count mismatch'
                }
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return {
                'success': False,
                'message': f'Backup failed: {str(e)}'
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        try:
            backup_pattern = os.path.join(self.backup_dir, "crypto_analyser_backup_*.db")
            backup_files = glob.glob(backup_pattern)
            
            backups = []
            for backup_file in sorted(backup_files, reverse=True):  # Most recent first
                try:
                    filename = os.path.basename(backup_file)
                    # Extract timestamp from filename
                    timestamp_str = filename.replace('crypto_analyser_backup_', '').replace('.db', '')
                    backup_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    # Get file size
                    file_size = os.path.getsize(backup_file)
                    
                    # Get record count
                    conn = sqlite3.connect(backup_file)
                    record_count = conn.execute("SELECT COUNT(*) FROM bitcoin_prices").fetchone()[0]
                    conn.close()
                    
                    backups.append({
                        'filename': filename,
                        'path': backup_file,
                        'timestamp': backup_time.isoformat(),
                        'age_hours': (datetime.now() - backup_time).total_seconds() / 3600,
                        'file_size_mb': round(file_size / (1024 * 1024), 2),
                        'record_count': record_count
                    })
                    
                except Exception as e:
                    logger.warning(f"Error processing backup file {backup_file}: {e}")
                    continue
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def cleanup_old_backups(self, keep_days: int = 30) -> Dict[str, Any]:
        """Remove backups older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            backups = self.list_backups()
            
            deleted_count = 0
            deleted_files = []
            
            for backup in backups:
                backup_time = datetime.fromisoformat(backup['timestamp'])
                if backup_time < cutoff_date:
                    try:
                        os.remove(backup['path'])
                        deleted_files.append(backup['filename'])
                        deleted_count += 1
                        logger.info(f"Deleted old backup: {backup['filename']}")
                    except Exception as e:
                        logger.error(f"Error deleting backup {backup['filename']}: {e}")
            
            return {
                'success': True,
                'message': f'Cleanup complete',
                'deleted_count': deleted_count,
                'deleted_files': deleted_files,
                'kept_days': keep_days
            }
            
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
            return {
                'success': False,
                'message': f'Cleanup failed: {str(e)}'
            }
    
    def restore_from_backup(self, backup_filename: str) -> Dict[str, Any]:
        """Restore database from a specific backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'message': f'Backup file not found: {backup_filename}'
                }
            
            # Create a backup of current database before restore
            current_backup = self.create_backup()
            if not current_backup['success']:
                return {
                    'success': False,
                    'message': f'Failed to backup current database before restore'
                }
            
            # Verify backup before restore
            backup_conn = sqlite3.connect(backup_path)
            backup_count = backup_conn.execute("SELECT COUNT(*) FROM bitcoin_prices").fetchone()[0]
            backup_conn.close()
            
            # Restore from backup
            shutil.copy2(backup_path, self.database_path)
            
            # Verify restore
            conn = sqlite3.connect(self.database_path)
            restored_count = conn.execute("SELECT COUNT(*) FROM bitcoin_prices").fetchone()[0]
            conn.close()
            
            if restored_count == backup_count:
                logger.info(f"Database restored successfully from {backup_filename}")
                return {
                    'success': True,
                    'message': f'Database restored successfully',
                    'backup_used': backup_filename,
                    'record_count': restored_count,
                    'current_backup': current_backup['backup_file']
                }
            else:
                logger.error(f"Restore verification failed")
                return {
                    'success': False,
                    'message': 'Restore verification failed'
                }
                
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return {
                'success': False,
                'message': f'Restore failed: {str(e)}'
            }


def get_backup_service(database_path: str = None) -> BackupService:
    """Factory function to get backup service instance"""
    if database_path is None:
        # Default database path
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        database_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
    
    return BackupService(database_path)