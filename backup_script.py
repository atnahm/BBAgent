"""
Automated Backup Script
Backup database and configuration files.
"""
import shutil
import sys
from pathlib import Path
from datetime import datetime
import tarfile
import json

class BackupManager:
    """Manage system backups."""
    
    def __init__(self, backup_dir='backups'):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def backup_database(self):
        """Backup SQLite database."""
        print("💾 Backing up database...")
        
        db_path = Path('data/biz_agent.db')
        
        if not db_path.exists():
            print("   ⚠️  Database not found")
            return None
        
        backup_path = self.backup_dir / f'biz_agent_{self.timestamp}.db'
        shutil.copy2(db_path, backup_path)
        
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ Database backed up: {backup_path} ({size_mb:.2f}MB)")
        
        return backup_path
    
    def backup_vector_db(self):
        """Backup ChromaDB."""
        print("🔍 Backing up vector database...")
        
        chroma_path = Path('data/chroma_db')
        
        if not chroma_path.exists():
            print("   ⚠️  Vector database not found")
            return None
        
        backup_path = self.backup_dir / f'chroma_{self.timestamp}.tar.gz'
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            tar.add(chroma_path, arcname='chroma_db')
        
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ Vector DB backed up: {backup_path} ({size_mb:.2f}MB)")
        
        return backup_path
    
    def backup_config(self):
        """Backup configuration files."""
        print("⚙️  Backing up configuration...")
        
        config_files = [
            'backend/config.yaml',
            'backend/.env'
        ]
        
        backup_path = self.backup_dir / f'config_{self.timestamp}.tar.gz'
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            for config_file in config_files:
                if Path(config_file).exists():
                    tar.add(config_file)
        
        size_kb = backup_path.stat().st_size / 1024
        print(f"   ✅ Config backed up: {backup_path} ({size_kb:.2f}KB)")
        
        return backup_path
    
    def create_backup_manifest(self, backups):
        """Create manifest file with backup details."""
        manifest = {
            'timestamp': self.timestamp,
            'date': datetime.now().isoformat(),
            'backups': {}
        }
        
        for name, path in backups.items():
            if path and path.exists():
                manifest['backups'][name] = {
                    'path': str(path),
                    'size_bytes': path.stat().st_size,
                    'size_mb': path.stat().st_size / (1024 * 1024)
                }
        
        manifest_path = self.backup_dir / f'manifest_{self.timestamp}.json'
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\n📋 Manifest created: {manifest_path}")
        
        return manifest_path
    
    def cleanup_old_backups(self, keep_days=30):
        """Remove backups older than specified days."""
        print(f"\n🧹 Cleaning up backups older than {keep_days} days...")
        
        cutoff = datetime.now().timestamp() - (keep_days * 24 * 3600)
        removed_count = 0
        
        for backup_file in self.backup_dir.iterdir():
            if backup_file.stat().st_mtime < cutoff:
                backup_file.unlink()
                removed_count += 1
                print(f"   🗑️  Removed: {backup_file.name}")
        
        if removed_count == 0:
            print(f"   ✅ No old backups to remove")
        else:
            print(f"   ✅ Removed {removed_count} old backups")
    
    def run_backup(self, cleanup=True, keep_days=30):
        """Run complete backup process."""
        print("="*60)
        print("BACKUP PROCESS STARTED")
        print("="*60)
        print(f"Timestamp: {self.timestamp}\n")
        
        backups = {
            'database': self.backup_database(),
            'vector_db': self.backup_vector_db(),
            'config': self.backup_config()
        }
        
        # Create manifest
        manifest = self.create_backup_manifest(backups)
        
        # Cleanup old backups
        if cleanup:
            self.cleanup_old_backups(keep_days)
        
        # Summary
        total_size = sum(
            path.stat().st_size 
            for path in backups.values() 
            if path and path.exists()
        ) / (1024 * 1024)
        
        print("\n" + "="*60)
        print("BACKUP COMPLETE")
        print("="*60)
        print(f"Total Size: {total_size:.2f}MB")
        print(f"Location: {self.backup_dir.absolute()}")
        print("="*60)
        
        return backups

class RestoreManager:
    """Restore from backups."""
    
    def __init__(self, backup_dir='backups'):
        self.backup_dir = Path(backup_dir)
    
    def list_backups(self):
        """List available backups."""
        print("📦 Available Backups:\n")
        
        manifests = sorted(self.backup_dir.glob('manifest_*.json'), reverse=True)
        
        if not manifests:
            print("   No backups found")
            return []
        
        backups = []
        
        for manifest_file in manifests:
            with open(manifest_file) as f:
                manifest = json.load(f)
            
            print(f"Backup: {manifest['timestamp']}")
            print(f"Date: {manifest['date']}")
            
            total_size = sum(
                b['size_mb'] 
                for b in manifest['backups'].values()
            )
            
            print(f"Size: {total_size:.2f}MB")
            print(f"Files: {', '.join(manifest['backups'].keys())}")
            print()
            
            backups.append(manifest)
        
        return backups
    
    def restore_backup(self, timestamp):
        """Restore from specific backup."""
        print(f"🔄 Restoring backup: {timestamp}")
        
        # Find manifest
        manifest_file = self.backup_dir / f'manifest_{timestamp}.json'
        
        if not manifest_file.exists():
            print(f"❌ Backup not found: {timestamp}")
            return False
        
        with open(manifest_file) as f:
            manifest = json.load(f)
        
        # Restore database
        if 'database' in manifest['backups']:
            db_backup = Path(manifest['backups']['database']['path'])
            if db_backup.exists():
                shutil.copy2(db_backup, 'data/biz_agent.db')
                print("   ✅ Database restored")
        
        # Restore vector DB
        if 'vector_db' in manifest['backups']:
            vdb_backup = Path(manifest['backups']['vector_db']['path'])
            if vdb_backup.exists():
                with tarfile.open(vdb_backup, 'r:gz') as tar:
                    tar.extractall('data/')
                print("   ✅ Vector DB restored")
        
        # Restore config
        if 'config' in manifest['backups']:
            config_backup = Path(manifest['backups']['config']['path'])
            if config_backup.exists():
                with tarfile.open(config_backup, 'r:gz') as tar:
                    tar.extractall('.')
                print("   ✅ Config restored")
        
        print("\n✅ Restore complete!")
        return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup/Restore Manager')
    parser.add_argument('action', choices=['backup', 'restore', 'list'], help='Action to perform')
    parser.add_argument('--timestamp', help='Backup timestamp for restore')
    parser.add_argument('--keep-days', type=int, default=30, help='Days to keep backups')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup of old backups')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        manager = BackupManager()
        manager.run_backup(cleanup=not args.no_cleanup, keep_days=args.keep_days)
    
    elif args.action == 'list':
        manager = RestoreManager()
        manager.list_backups()
    
    elif args.action == 'restore':
        if not args.timestamp:
            print("❌ --timestamp required for restore")
            sys.exit(1)
        
        manager = RestoreManager()
        manager.restore_backup(args.timestamp)
