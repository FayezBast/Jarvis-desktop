import subprocess
import os
import logging
from pathlib import Path
from langchain.tools import tool
from .app_discovery import ApplicationDiscovery

logger = logging.getLogger(__name__)

class AppLauncher:
    def __init__(self):
        self.discovery = ApplicationDiscovery()
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure the application database exists, create if not"""
        if not self.discovery.app_database_path.exists():
            logger.info("📝 Application database not found, creating...")
            self.discovery.refresh_database()
    
    def open_application(self, app_name: str) -> str:
        """Open an application with intelligent lookup"""
        logger.info(f"🚀 Attempting to open: {app_name}")
        
        # Load the application database
        database = self.discovery.load_database()
        
        if not database:
            logger.warning("⚠️ Empty database, refreshing...")
            database = self.discovery.refresh_database()
        
        # Normalize the app name
        normalized_name = app_name.lower().strip()
        
        # Method 1: Direct lookup in database
        if normalized_name in database:
            app_info = database[normalized_name]
            success = self._try_open_app_by_info(app_info)
            if success:
                return f"✅ Successfully opened {app_info['display_name'] or app_info['name']}."
        
        # Method 2: Fuzzy search in database
        suggestions = self.discovery.get_app_suggestions(normalized_name, max_suggestions=5)
        
        if suggestions:
            # Try to open the best match
            best_match = suggestions[0]
            success = self._try_open_app_by_info(best_match)
            
            if success:
                return f"✅ Opened {best_match['display_name'] or best_match['name']} (best match for '{app_name}')."
            else:
                # Show alternatives if the best match failed
                alternatives = [app['display_name'] or app['name'] for app in suggestions[:3]]
                return f"❌ Failed to open {best_match['name']}. Try these alternatives: {', '.join(alternatives)}"
        
        # Method 3: Fallback to legacy search
        legacy_result = self._legacy_app_search(app_name)
        if legacy_result:
            return legacy_result
        
        # Method 4: Suggest database refresh and provide common apps
        return self._suggest_alternatives(app_name, database)
    
    def _try_open_app_by_info(self, app_info: dict) -> bool:
        """Try to open an app using the information from the database"""
        app_name = app_info['name']
        app_path = app_info['path']
        bundle_id = app_info['bundle_id']
        
        # Method 1: Try by exact path
        if os.path.exists(app_path):
            try:
                result = subprocess.run(
                    ["open", app_path], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"✅ Opened {app_name} by path")
                    return True
            except Exception as e:
                logger.debug(f"Failed to open by path: {e}")
        
        # Method 2: Try by bundle ID
        if bundle_id:
            try:
                result = subprocess.run(
                    ["open", "-b", bundle_id],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"✅ Opened {app_name} by bundle ID")
                    return True
            except Exception as e:
                logger.debug(f"Failed to open by bundle ID: {e}")
        
        # Method 3: Try by name
        try:
            result = subprocess.run(
                ["open", "-a", app_name], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"✅ Opened {app_name} by name")
                return True
        except Exception as e:
            logger.debug(f"Failed to open by name: {e}")
        
        return False
    
    def _legacy_app_search(self, app_name: str) -> str:
        """Fallback to manual search for apps not in database"""
        found_apps = self._search_installed_apps(app_name.lower())
        
        if found_apps:
            first_match = found_apps[0]
            success = self._try_open_app_simple(first_match)
            if success:
                return f"✅ Opened {first_match} (found via search)."
            else:
                return f"❌ Found {first_match} but failed to open. Available: {', '.join(found_apps[:3])}"
        
        return None
    
    def _search_installed_apps(self, search_term: str) -> list:
        """Search for installed apps that match the search term"""
        try:
            found_apps = []
            search_paths = ["/Applications", "/System/Applications"]
            
            for apps_dir in search_paths:
                if os.path.exists(apps_dir):
                    for item in os.listdir(apps_dir):
                        if item.endswith('.app'):
                            app_name = item[:-4]  # Remove .app extension
                            if search_term in app_name.lower():
                                found_apps.append(app_name)
            
            return found_apps[:5]  # Limit to 5 results
        except:
            return []
    
    def _try_open_app_simple(self, app_name: str) -> bool:
        """Simple app opening method"""
        try:
            result = subprocess.run(
                ["open", "-a", app_name], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _suggest_alternatives(self, app_name: str, database: dict) -> str:
        """Suggest alternatives when app is not found"""
        common_apps = []
        
        # Get some popular apps from each category
        categories = ['Browsers', 'Development', 'Communication', 'Media', 'Productivity']
        for app_key, app_info in database.items():
            if app_info.get('category') in categories:
                display_name = app_info.get('display_name') or app_info['name']
                if display_name not in common_apps and len(common_apps) < 10:
                    common_apps.append(display_name)
        
        suggestion_text = f"❌ App '{app_name}' not found."
        
        if common_apps:
            suggestion_text += f" Try these popular apps: {', '.join(common_apps[:5])}"
        
        suggestion_text += " You can also say 'refresh app database' to update the list of available apps."
        
        return suggestion_text

    def list_apps_by_category(self) -> str:
        """List available applications organized by category"""
        database = self.discovery.load_database()
        
        if not database:
            return "❌ No application database found. Say 'refresh app database' to create one."
        
        # Organize apps by category
        categorized_apps = {}
        unique_apps = set()  # To avoid duplicates
        
        for app_key, app_info in database.items():
            app_name = app_info.get('display_name') or app_info['name']
            category = app_info.get('category', 'Other')
            
            # Skip duplicates (same app with different aliases)
            if app_name not in unique_apps:
                unique_apps.add(app_name)
                if category not in categorized_apps:
                    categorized_apps[category] = []
                categorized_apps[category].append(app_name)
        
        # Sort apps within each category
        for category in categorized_apps:
            categorized_apps[category].sort()
        
        # Build the response
        result = f"📱 Available Applications ({len(unique_apps)} total):\n\n"
        
        # Define category order for better presentation
        category_order = ['System', 'Browsers', 'Development', 'Communication', 'Media', 
                         'Productivity', 'Gaming', 'Utilities', 'Other']
        
        for category in category_order:
            if category in categorized_apps:
                apps = categorized_apps[category]
                result += f"📂 **{category}** ({len(apps)}): {', '.join(apps[:8])}"
                if len(apps) > 8:
                    result += f" ... and {len(apps) - 8} more"
                result += "\n\n"
        
        result += "💡 Just say 'open [app name]' to launch any application!"
        return result
    
    def refresh_app_database(self) -> str:
        """Refresh the application database"""
        try:
            logger.info("🔄 Refreshing application database...")
            applications = self.discovery.refresh_database()
            
            # Count unique apps
            unique_apps = set()
            for app_info in applications.values():
                unique_apps.add(app_info['name'])
            
            return f"✅ Application database refreshed! Found {len(unique_apps)} applications with {len(applications)} total entries (including aliases)."
            
        except Exception as e:
            logger.error(f"❌ Error refreshing database: {e}")
            return f"❌ Failed to refresh application database: {str(e)}"

# Initialize the app launcher
app_launcher = AppLauncher()

@tool
def open_app(app_name: str) -> str:
    """Open a macOS application by name. I know about all apps installed on this Mac and can open them by name, nickname, or partial name. Examples: Safari, Chrome, Calculator, VS Code, Discord, Spotify, etc."""
    return app_launcher.open_application(app_name)

@tool
def list_available_apps() -> str:
    """List all applications available on this Mac, organized by category. Shows browsers, development tools, communication apps, media players, productivity apps, etc."""
    return app_launcher.list_apps_by_category()

@tool
def refresh_app_database() -> str:
    """Refresh the application database to discover newly installed apps or update app information. Run this if you've installed new applications recently."""
    return app_launcher.refresh_app_database()

