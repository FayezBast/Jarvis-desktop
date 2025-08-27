#!/usr/bin/env python3
"""
Application Discovery Module for Jarvis
Automatically discovers and catalogs all available applications on macOS
"""

import os
import json
import subprocess
import plistlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ApplicationDiscovery:
    def __init__(self):
        self.app_database_path = Path(__file__).parent / "app_database.json"
        self.search_paths = [
            "/Applications",
            "/System/Applications", 
            "/System/Library/CoreServices",
            "/Applications/Utilities",
            "~/Applications",  # User applications
        ]
        
    def discover_all_applications(self) -> Dict[str, Dict]:
        """Discover all applications and return comprehensive database"""
        logger.info("🔍 Starting comprehensive application discovery...")
        
        applications = {}
        
        for search_path in self.search_paths:
            expanded_path = os.path.expanduser(search_path)
            if os.path.exists(expanded_path):
                logger.info(f"📂 Scanning {expanded_path}")
                apps_in_path = self._scan_directory(expanded_path)
                applications.update(apps_in_path)
        
        # Add manually discovered system utilities
        system_apps = self._get_system_applications()
        applications.update(system_apps)
        
        logger.info(f"✅ Discovered {len(applications)} applications")
        return applications
    
    def _scan_directory(self, directory: str) -> Dict[str, Dict]:
        """Scan a directory for .app bundles"""
        applications = {}
        
        try:
            for item in os.listdir(directory):
                if item.endswith('.app'):
                    app_path = os.path.join(directory, item)
                    app_info = self._extract_app_info(app_path)
                    if app_info:
                        # Create multiple key variations for easier lookup
                        app_name = app_info['name']
                        applications[app_name.lower()] = app_info
                        
                        # Add alternative names and aliases
                        alternatives = self._generate_alternatives(app_name)
                        for alt in alternatives:
                            applications[alt.lower()] = app_info
                            
        except PermissionError:
            logger.warning(f"⚠️ Permission denied accessing {directory}")
        except Exception as e:
            logger.error(f"❌ Error scanning {directory}: {e}")
            
        return applications
    
    def _extract_app_info(self, app_path: str) -> Optional[Dict]:
        """Extract detailed information about an application"""
        try:
            info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
            
            app_info = {
                'name': os.path.basename(app_path)[:-4],  # Remove .app extension
                'path': app_path,
                'bundle_id': None,
                'display_name': None,
                'version': None,
                'executable': None,
                'alternatives': [],
                'category': self._categorize_app(app_path)
            }
            
            # Try to read Info.plist for detailed information
            if os.path.exists(info_plist_path):
                try:
                    with open(info_plist_path, 'rb') as f:
                        plist_data = plistlib.load(f)
                        
                    app_info['bundle_id'] = plist_data.get('CFBundleIdentifier')
                    app_info['display_name'] = plist_data.get('CFBundleDisplayName') or plist_data.get('CFBundleName')
                    app_info['version'] = plist_data.get('CFBundleShortVersionString')
                    app_info['executable'] = plist_data.get('CFBundleExecutable')
                    
                except Exception as e:
                    logger.debug(f"Could not read plist for {app_path}: {e}")
            
            return app_info
            
        except Exception as e:
            logger.debug(f"Error extracting info for {app_path}: {e}")
            return None
    
    def _generate_alternatives(self, app_name: str) -> List[str]:
        """Generate alternative names and common abbreviations for an app"""
        alternatives = []
        
        # Common app name mappings
        name_mappings = {
            'Google Chrome': ['chrome', 'google chrome'],
            'Visual Studio Code': ['vscode', 'vs code', 'code'],
            'Microsoft Word': ['word', 'ms word'],
            'Microsoft Excel': ['excel', 'ms excel'],
            'Microsoft PowerPoint': ['powerpoint', 'ppt', 'ms powerpoint'],
            'Microsoft Outlook': ['outlook', 'ms outlook'],
            'Adobe Photoshop': ['photoshop', 'ps'],
            'Adobe Illustrator': ['illustrator', 'ai'],
            'Adobe Premiere Pro': ['premiere', 'premiere pro'],
            'Final Cut Pro': ['final cut', 'fcp'],
            'Logic Pro': ['logic', 'logic pro'],
            'System Preferences': ['preferences', 'settings', 'system settings'],
            'Activity Monitor': ['activity monitor', 'task manager'],
            'QuickTime Player': ['quicktime', 'qt'],
            'VLC media player': ['vlc', 'vlc player'],
            'Spotify': ['spotify music'],
            'Discord': ['discord app'],
            'Telegram': ['telegram messenger'],
            'WhatsApp': ['whatsapp messenger'],
            '1Password 7 - Password Manager': ['1password', 'password manager'],
            'TextEdit': ['text edit', 'notepad'],
            'Keychain Access': ['keychain', 'keychain access']
        }
        
        if app_name in name_mappings:
            alternatives.extend(name_mappings[app_name])
        
        # Generate common variations
        lower_name = app_name.lower()
        alternatives.append(lower_name)
        
        # Remove common suffixes
        for suffix in [' app', ' application', '.app']:
            if lower_name.endswith(suffix):
                alternatives.append(lower_name[:-len(suffix)])
        
        # Handle names with spaces
        if ' ' in app_name:
            # Add version without spaces
            alternatives.append(app_name.replace(' ', '').lower())
            # Add first word only
            alternatives.append(app_name.split()[0].lower())
        
        return list(set(alternatives))  # Remove duplicates
    
    def _categorize_app(self, app_path: str) -> str:
        """Categorize application based on path and name"""
        app_name = os.path.basename(app_path).lower()
        
        categories = {
            'System': ['/System/Applications', '/System/Library/CoreServices'],
            'Utilities': ['/Applications/Utilities'],
            'Development': ['xcode', 'visual studio', 'terminal', 'github'],
            'Browsers': ['chrome', 'safari', 'firefox', 'edge', 'brave'],
            'Communication': ['discord', 'slack', 'zoom', 'teams', 'telegram', 'whatsapp', 'signal'],
            'Media': ['spotify', 'vlc', 'quicktime', 'music', 'photos', 'netflix'],
            'Productivity': ['word', 'excel', 'powerpoint', 'notion', 'obsidian', 'notes'],
            'Gaming': ['steam', 'epic', 'minecraft'],
        }
        
        # Check by path first
        for category, paths in categories.items():
            if category in ['System', 'Utilities']:
                for path in paths:
                    if app_path.startswith(path):
                        return category
        
        # Check by name
        for category, keywords in categories.items():
            if category not in ['System', 'Utilities']:
                for keyword in keywords:
                    if keyword in app_name:
                        return category
        
        return 'Other'
    
    def _get_system_applications(self) -> Dict[str, Dict]:
        """Get system applications that might not be in standard locations"""
        system_apps = {}
        
        # Add some important system utilities
        special_apps = [
            {'name': 'Finder', 'path': '/System/Library/CoreServices/Finder.app'},
            {'name': 'Dock', 'path': '/System/Library/CoreServices/Dock.app'},
            {'name': 'Spotlight', 'path': '/System/Library/CoreServices/Search.bundle'},
        ]
        
        for app in special_apps:
            if os.path.exists(app['path']):
                app_info = {
                    'name': app['name'],
                    'path': app['path'],
                    'bundle_id': None,
                    'display_name': app['name'],
                    'version': None,
                    'executable': None,
                    'alternatives': [app['name'].lower()],
                    'category': 'System'
                }
                system_apps[app['name'].lower()] = app_info
        
        return system_apps
    
    def save_database(self, applications: Dict[str, Dict]) -> None:
        """Save the application database to a JSON file"""
        try:
            with open(self.app_database_path, 'w') as f:
                json.dump(applications, f, indent=2, sort_keys=True)
            logger.info(f"💾 Saved application database to {self.app_database_path}")
        except Exception as e:
            logger.error(f"❌ Error saving database: {e}")
    
    def load_database(self) -> Dict[str, Dict]:
        """Load the application database from JSON file"""
        try:
            if self.app_database_path.exists():
                with open(self.app_database_path, 'r') as f:
                    return json.load(f)
            else:
                logger.info("📝 No existing database found, will create new one")
                return {}
        except Exception as e:
            logger.error(f"❌ Error loading database: {e}")
            return {}
    
    def refresh_database(self) -> Dict[str, Dict]:
        """Refresh the application database"""
        logger.info("🔄 Refreshing application database...")
        applications = self.discover_all_applications()
        self.save_database(applications)
        return applications
    
    def get_app_suggestions(self, query: str, max_suggestions: int = 5) -> List[Dict]:
        """Get application suggestions based on query"""
        database = self.load_database()
        suggestions = []
        
        query_lower = query.lower().strip()
        
        # First, try exact matches
        if query_lower in database:
            suggestions.append(database[query_lower])
        
        # Then, try partial matches
        for app_key, app_info in database.items():
            if query_lower in app_key and app_info not in suggestions:
                suggestions.append(app_info)
            
            if len(suggestions) >= max_suggestions:
                break
        
        return suggestions[:max_suggestions]

def main():
    """Main function to refresh the application database"""
    logging.basicConfig(level=logging.INFO)
    
    discovery = ApplicationDiscovery()
    applications = discovery.refresh_database()
    
    print(f"\n✅ Application discovery complete!")
    print(f"📊 Found {len(applications)} total entries")
    
    # Show some statistics
    categories = {}
    for app_info in applications.values():
        category = app_info.get('category', 'Other')
        categories[category] = categories.get(category, 0) + 1
    
    print("\n📈 Applications by category:")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count}")
    
    print(f"\n💾 Database saved to: {discovery.app_database_path}")

if __name__ == "__main__":
    main()
