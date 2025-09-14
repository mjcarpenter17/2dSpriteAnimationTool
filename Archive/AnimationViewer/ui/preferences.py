"""
Settings and Preferences System for the Sprite Animation Tool.
This implements Phase 1.7 with JSON-based preferences storage and a tabbed settings dialog.
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import copy


class PreferencesManager:
    """Centralized preferences management with JSON persistence."""
    
    def __init__(self):
        """Initialize the preferences manager."""
        self.config_dir = self._get_config_directory()
        self.preferences_file = os.path.join(self.config_dir, "preferences.json")
        self.backup_file = os.path.join(self.config_dir, "preferences_backup.json")
        
        # Default preferences
        self.defaults = {
            # General settings
            "general": {
                "default_export_dir": os.path.expanduser("~/Documents/Animations"),
                "animation_naming_pattern": "{sheet_name}_{animation_type}",
                "auto_save_interval": 300,  # seconds
                "recent_files_limit": 10,
                "remember_window_state": True,
                "show_tooltips": True
            },
            
            # Display preferences
            "display": {
                "grid_color": "#808080",
                "grid_opacity": 0.5,
                "selection_color": "#4CAF50",
                "selection_opacity": 0.3,
                "background_color": "#F0F0F0",
                "ui_theme": "default",
                "show_frame_numbers": True,
                "show_tile_info": True
            },
            
            # File management
            "file_management": {
                "last_sprite_dir": os.path.expanduser("~/Documents"),
                "last_export_dir": os.path.expanduser("~/Documents/Animations"),
                "recent_sprite_sheets": [],
                "auto_cleanup_orphaned": True,
                "backup_animations": True
            },
            
            # Window layout
            "layout": {
                "window_width": 1400,
                "window_height": 900,
                "window_x": -1,  # -1 means center
                "window_y": -1,  # -1 means center
                "left_panel_width": 250,
                "right_panel_width": 300,
                "animation_panel_height": 200
            },
            
            # Advanced settings
            "advanced": {
                "memory_limit_mb": 512,
                "enable_debug_logging": False,
                "max_undo_levels": 50,
                "tile_cache_size": 1000,
                "background_processing": True,
                # Aseprite integration toggle (Phase 1)
                "use_aseprite_json": False
            }
        }
        
        # Current preferences (loaded from file or defaults)
        self.preferences = copy.deepcopy(self.defaults)
        self.load_preferences()
        
        # Observers for preference changes
        self.observers = []
    
    def _get_config_directory(self) -> str:
        """Get the application configuration directory."""
        if sys.platform == "win32":
            config_dir = os.path.join(os.environ.get("APPDATA", ""), "SpriteAnimationTool")
        elif sys.platform == "darwin":
            config_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "SpriteAnimationTool")
        else:
            config_dir = os.path.join(os.path.expanduser("~"), ".config", "SpriteAnimationTool")
        
        # Create directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        return config_dir
    
    def load_preferences(self) -> bool:
        """Load preferences from file."""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    loaded_prefs = json.load(f)
                
                # Merge with defaults to handle new settings
                self._merge_preferences(loaded_prefs)
                return True
        except Exception as e:
            print(f"Failed to load preferences: {e}")
            # Try backup file
            if self._load_backup():
                return True
            # Fall back to defaults
            self.preferences = copy.deepcopy(self.defaults)
        
        return False
    
    def _load_backup(self) -> bool:
        """Try to load from backup file."""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r') as f:
                    loaded_prefs = json.load(f)
                self._merge_preferences(loaded_prefs)
                return True
        except Exception:
            pass
        return False
    
    def _merge_preferences(self, loaded_prefs: Dict[str, Any]):
        """Merge loaded preferences with defaults."""
        for category, settings in self.defaults.items():
            if category in loaded_prefs:
                for key, default_value in settings.items():
                    if key in loaded_prefs[category]:
                        self.preferences[category][key] = loaded_prefs[category][key]
    
    def save_preferences(self) -> bool:
        """Save preferences to file."""
        try:
            # Create backup of current file
            if os.path.exists(self.preferences_file):
                # Remove existing backup if it exists
                if os.path.exists(self.backup_file):
                    os.remove(self.backup_file)
                os.rename(self.preferences_file, self.backup_file)
            
            # Save new preferences
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to save preferences: {e}")
            return False
    
    def get(self, category: str, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        try:
            return self.preferences[category][key]
        except KeyError:
            return default
    
    def set(self, category: str, key: str, value: Any):
        """Set a preference value."""
        if category not in self.preferences:
            self.preferences[category] = {}
        
        old_value = self.preferences[category].get(key)
        self.preferences[category][key] = value
        
        # Notify observers if value changed
        if old_value != value:
            self._notify_observers(category, key, value)
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all preferences in a category."""
        return self.preferences.get(category, {})
    
    def set_category(self, category: str, values: Dict[str, Any]):
        """Set multiple preferences in a category."""
        if category not in self.preferences:
            self.preferences[category] = {}
        
        for key, value in values.items():
            self.set(category, key, value)
    
    def reset_to_defaults(self):
        """Reset all preferences to default values."""
        self.preferences = copy.deepcopy(self.defaults)
        self.save_preferences()
        self._notify_observers("*", "*", None)  # Notify all observers
    
    def export_preferences(self, file_path: str) -> bool:
        """Export preferences to a file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            return True
        except Exception:
            return False
    
    def import_preferences(self, file_path: str) -> bool:
        """Import preferences from a file."""
        try:
            with open(file_path, 'r') as f:
                imported_prefs = json.load(f)
            
            self._merge_preferences(imported_prefs)
            self.save_preferences()
            self._notify_observers("*", "*", None)  # Notify all observers
            return True
        except Exception:
            return False
    
    def add_observer(self, callback):
        """Add an observer for preference changes."""
        self.observers.append(callback)
    
    def remove_observer(self, callback):
        """Remove an observer."""
        if callback in self.observers:
            self.observers.remove(callback)
    
    def _notify_observers(self, category: str, key: str, value: Any):
        """Notify observers of preference changes."""
        for observer in self.observers:
            try:
                observer(category, key, value)
            except Exception as e:
                print(f"Error notifying preference observer: {e}")
    
    def add_recent_file(self, file_path: str):
        """Add a file to the recent files list."""
        recent_files = self.get("file_management", "recent_sprite_sheets", [])
        
        # Remove if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to front
        recent_files.insert(0, file_path)
        
        # Limit list size
        limit = self.get("general", "recent_files_limit", 10)
        recent_files = recent_files[:limit]
        
        self.set("file_management", "recent_sprite_sheets", recent_files)
        self.save_preferences()
    
    def get_recent_files(self) -> List[str]:
        """Get the list of recent files."""
        recent_files = self.get("file_management", "recent_sprite_sheets", [])
        # Filter out non-existent files
        existing_files = [f for f in recent_files if os.path.exists(f)]
        if len(existing_files) != len(recent_files):
            self.set("file_management", "recent_sprite_sheets", existing_files)
            self.save_preferences()
        return existing_files


class SettingsDialog:
    """Tabbed settings dialog for user preferences."""
    
    def __init__(self, parent, preferences_manager: PreferencesManager):
        """Initialize the settings dialog."""
        self.parent = parent
        self.prefs = preferences_manager
        self.temp_prefs = copy.deepcopy(preferences_manager.preferences)
        
        # Create dialog window
        self.dialog = tk.Toplevel()
        self.dialog.title("Preferences")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent if parent else None)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.dialog.winfo_screenwidth() // 2 - 250,
            self.dialog.winfo_screenheight() // 2 - 200
        ))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the settings dialog UI."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_general_tab()
        self.create_display_tab()
        self.create_file_management_tab()
        self.create_advanced_tab()
        
        # Buttons frame
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        # Buttons
        tk.Button(button_frame, text="Reset to Defaults", 
                 command=self.reset_to_defaults).pack(side="left")
        
        tk.Frame(button_frame).pack(side="left", expand=True)  # Spacer
        
        tk.Button(button_frame, text="Cancel", 
                 command=self.cancel).pack(side="right", padx=5)
        tk.Button(button_frame, text="OK", 
                 command=self.ok).pack(side="right")
    
    def create_general_tab(self):
        """Create the general settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="General")
        
        # Default export directory
        tk.Label(frame, text="Default Export Directory:").grid(row=0, column=0, sticky="w", pady=5)
        self.export_dir_var = tk.StringVar(value=self.temp_prefs["general"]["default_export_dir"])
        export_frame = tk.Frame(frame)
        export_frame.grid(row=0, column=1, sticky="ew", padx=10)
        tk.Entry(export_frame, textvariable=self.export_dir_var, width=30).pack(side="left", fill="x", expand=True)
        tk.Button(export_frame, text="Browse", command=self.browse_export_dir).pack(side="right")
        
        # Animation naming pattern
        tk.Label(frame, text="Animation Naming Pattern:").grid(row=1, column=0, sticky="w", pady=5)
        self.naming_pattern_var = tk.StringVar(value=self.temp_prefs["general"]["animation_naming_pattern"])
        tk.Entry(frame, textvariable=self.naming_pattern_var, width=30).grid(row=1, column=1, sticky="ew", padx=10)
        
        # Auto-save interval
        tk.Label(frame, text="Auto-save Interval (seconds):").grid(row=2, column=0, sticky="w", pady=5)
        self.autosave_var = tk.IntVar(value=self.temp_prefs["general"]["auto_save_interval"])
        tk.Spinbox(frame, from_=60, to=3600, textvariable=self.autosave_var, width=10).grid(row=2, column=1, sticky="w", padx=10)
        
        # Recent files limit
        tk.Label(frame, text="Recent Files Limit:").grid(row=3, column=0, sticky="w", pady=5)
        self.recent_limit_var = tk.IntVar(value=self.temp_prefs["general"]["recent_files_limit"])
        tk.Spinbox(frame, from_=5, to=20, textvariable=self.recent_limit_var, width=10).grid(row=3, column=1, sticky="w", padx=10)
        
        # Checkboxes
        self.remember_window_var = tk.BooleanVar(value=self.temp_prefs["general"]["remember_window_state"])
        tk.Checkbutton(frame, text="Remember window size and position", 
                      variable=self.remember_window_var).grid(row=4, columnspan=2, sticky="w", pady=5)
        
        self.show_tooltips_var = tk.BooleanVar(value=self.temp_prefs["general"]["show_tooltips"])
        tk.Checkbutton(frame, text="Show tooltips", 
                      variable=self.show_tooltips_var).grid(row=5, columnspan=2, sticky="w", pady=5)
        
        frame.columnconfigure(1, weight=1)
    
    def create_display_tab(self):
        """Create the display settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Display")
        
        # Grid color
        tk.Label(frame, text="Grid Color:").grid(row=0, column=0, sticky="w", pady=5)
        self.grid_color_var = tk.StringVar(value=self.temp_prefs["display"]["grid_color"])
        color_frame = tk.Frame(frame)
        color_frame.grid(row=0, column=1, sticky="ew", padx=10)
        self.grid_color_button = tk.Button(color_frame, text="    ", 
                                         bg=self.grid_color_var.get(),
                                         command=lambda: self.choose_color(self.grid_color_var, self.grid_color_button))
        self.grid_color_button.pack(side="left")
        tk.Entry(color_frame, textvariable=self.grid_color_var, width=10).pack(side="left", padx=5)
        
        # Selection color
        tk.Label(frame, text="Selection Color:").grid(row=1, column=0, sticky="w", pady=5)
        self.selection_color_var = tk.StringVar(value=self.temp_prefs["display"]["selection_color"])
        color_frame2 = tk.Frame(frame)
        color_frame2.grid(row=1, column=1, sticky="ew", padx=10)
        self.selection_color_button = tk.Button(color_frame2, text="    ", 
                                              bg=self.selection_color_var.get(),
                                              command=lambda: self.choose_color(self.selection_color_var, self.selection_color_button))
        self.selection_color_button.pack(side="left")
        tk.Entry(color_frame2, textvariable=self.selection_color_var, width=10).pack(side="left", padx=5)
        
        # UI Theme
        tk.Label(frame, text="UI Theme:").grid(row=2, column=0, sticky="w", pady=5)
        self.theme_var = tk.StringVar(value=self.temp_prefs["display"]["ui_theme"])
        theme_combo = ttk.Combobox(frame, textvariable=self.theme_var, values=["default", "dark", "light"])
        theme_combo.grid(row=2, column=1, sticky="w", padx=10)
        theme_combo.state(['readonly'])
        
        # Checkboxes
        self.show_frame_numbers_var = tk.BooleanVar(value=self.temp_prefs["display"]["show_frame_numbers"])
        tk.Checkbutton(frame, text="Show frame numbers", 
                      variable=self.show_frame_numbers_var).grid(row=3, columnspan=2, sticky="w", pady=5)
        
        self.show_tile_info_var = tk.BooleanVar(value=self.temp_prefs["display"]["show_tile_info"])
        tk.Checkbutton(frame, text="Show tile information", 
                      variable=self.show_tile_info_var).grid(row=4, columnspan=2, sticky="w", pady=5)
        
        frame.columnconfigure(1, weight=1)
    
    def create_file_management_tab(self):
        """Create the file management tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="File Management")
        
        # Checkboxes
        self.auto_cleanup_var = tk.BooleanVar(value=self.temp_prefs["file_management"]["auto_cleanup_orphaned"])
        tk.Checkbutton(frame, text="Automatically cleanup orphaned animation files", 
                      variable=self.auto_cleanup_var).grid(row=0, columnspan=2, sticky="w", pady=5)
        
        self.backup_animations_var = tk.BooleanVar(value=self.temp_prefs["file_management"]["backup_animations"])
        tk.Checkbutton(frame, text="Create backup copies of animation files", 
                      variable=self.backup_animations_var).grid(row=1, columnspan=2, sticky="w", pady=5)
        
        # Recent files management
        tk.Label(frame, text="Recent Files:").grid(row=2, column=0, sticky="nw", pady=10)
        recent_frame = tk.Frame(frame)
        recent_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=10)
        
        # Recent files listbox with scrollbar
        listbox_frame = tk.Frame(recent_frame)
        listbox_frame.pack(fill="both", expand=True)
        
        self.recent_listbox = tk.Listbox(listbox_frame, height=6)
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=self.recent_listbox.yview)
        self.recent_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.recent_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate recent files list
        for file_path in self.prefs.get_recent_files():
            self.recent_listbox.insert(tk.END, os.path.basename(file_path))
        
        # Recent files buttons
        button_frame = tk.Frame(recent_frame)
        button_frame.pack(fill="x", pady=5)
        tk.Button(button_frame, text="Clear All", command=self.clear_recent_files).pack(side="right")
        
        frame.columnconfigure(1, weight=1)
    
    def create_advanced_tab(self):
        """Create the advanced settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Advanced")
        
        # Memory limit
        tk.Label(frame, text="Memory Limit (MB):").grid(row=0, column=0, sticky="w", pady=5)
        self.memory_limit_var = tk.IntVar(value=self.temp_prefs["advanced"]["memory_limit_mb"])
        tk.Spinbox(frame, from_=256, to=2048, textvariable=self.memory_limit_var, width=10).grid(row=0, column=1, sticky="w", padx=10)
        
        # Max undo levels
        tk.Label(frame, text="Maximum Undo Levels:").grid(row=1, column=0, sticky="w", pady=5)
        self.undo_levels_var = tk.IntVar(value=self.temp_prefs["advanced"]["max_undo_levels"])
        tk.Spinbox(frame, from_=10, to=100, textvariable=self.undo_levels_var, width=10).grid(row=1, column=1, sticky="w", padx=10)
        
        # Tile cache size
        tk.Label(frame, text="Tile Cache Size:").grid(row=2, column=0, sticky="w", pady=5)
        self.cache_size_var = tk.IntVar(value=self.temp_prefs["advanced"]["tile_cache_size"])
        tk.Spinbox(frame, from_=100, to=5000, textvariable=self.cache_size_var, width=10).grid(row=2, column=1, sticky="w", padx=10)
        
        # Checkboxes
        self.debug_logging_var = tk.BooleanVar(value=self.temp_prefs["advanced"]["enable_debug_logging"])
        tk.Checkbutton(frame, text="Enable debug logging", 
                      variable=self.debug_logging_var).grid(row=3, columnspan=2, sticky="w", pady=5)
        
        self.background_processing_var = tk.BooleanVar(value=self.temp_prefs["advanced"]["background_processing"])
        tk.Checkbutton(frame, text="Enable background processing", 
                      variable=self.background_processing_var).grid(row=4, columnspan=2, sticky="w", pady=5)

        # Aseprite JSON usage toggle (after background processing)
        self.use_aseprite_json_var = tk.BooleanVar(value=self.temp_prefs["advanced"].get("use_aseprite_json", False))
        ttk.Checkbutton(frame, text="Use Aseprite JSON Data (auto-detect .json next to .png)", 
                        variable=self.use_aseprite_json_var).grid(row=5, columnspan=2, sticky="w", pady=5)
        # Adjust following rows indices (+1)
        button_frame = tk.Frame(frame)
        button_frame.grid(row=6, columnspan=2, sticky="ew", pady=20)
        tk.Button(button_frame, text="Export Preferences", command=self.export_preferences).pack(side="left")
        tk.Button(button_frame, text="Import Preferences", command=self.import_preferences).pack(side="left", padx=10)
        frame.columnconfigure(1, weight=1)
    
    def browse_export_dir(self):
        """Browse for export directory."""
        directory = filedialog.askdirectory(initialdir=self.export_dir_var.get())
        if directory:
            self.export_dir_var.set(directory)
    
    def choose_color(self, color_var: tk.StringVar, button: tk.Button):
        """Choose a color using color picker."""
        color = colorchooser.askcolor(color=color_var.get())
        if color[1]:  # If a color was selected
            color_var.set(color[1])
            button.config(bg=color[1])
    
    def clear_recent_files(self):
        """Clear the recent files list."""
        if messagebox.askyesno("Clear Recent Files", "Are you sure you want to clear all recent files?"):
            self.recent_listbox.delete(0, tk.END)
            self.temp_prefs["file_management"]["recent_sprite_sheets"] = []
    
    def export_preferences(self):
        """Export preferences to a file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Preferences",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            if self.prefs.export_preferences(file_path):
                messagebox.showinfo("Success", "Preferences exported successfully!")
            else:
                messagebox.showerror("Error", "Failed to export preferences.")
    
    def import_preferences(self):
        """Import preferences from a file."""
        file_path = filedialog.askopenfilename(
            title="Import Preferences",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            if self.prefs.import_preferences(file_path):
                messagebox.showinfo("Success", "Preferences imported successfully!\nRestart the application to see all changes.")
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to import preferences.")
    
    def reset_to_defaults(self):
        """Reset all preferences to defaults."""
        if messagebox.askyesno("Reset Preferences", "Are you sure you want to reset all preferences to defaults?"):
            self.temp_prefs = copy.deepcopy(self.prefs.defaults)
            self.update_ui_from_prefs()
    
    def update_ui_from_prefs(self):
        """Update UI controls from temporary preferences."""
        # General tab
        self.export_dir_var.set(self.temp_prefs["general"]["default_export_dir"])
        self.naming_pattern_var.set(self.temp_prefs["general"]["animation_naming_pattern"])
        self.autosave_var.set(self.temp_prefs["general"]["auto_save_interval"])
        self.recent_limit_var.set(self.temp_prefs["general"]["recent_files_limit"])
        self.remember_window_var.set(self.temp_prefs["general"]["remember_window_state"])
        self.show_tooltips_var.set(self.temp_prefs["general"]["show_tooltips"])
        
        # Display tab
        self.grid_color_var.set(self.temp_prefs["display"]["grid_color"])
        self.grid_color_button.config(bg=self.grid_color_var.get())
        self.selection_color_var.set(self.temp_prefs["display"]["selection_color"])
        self.selection_color_button.config(bg=self.selection_color_var.get())
        self.theme_var.set(self.temp_prefs["display"]["ui_theme"])
        self.show_frame_numbers_var.set(self.temp_prefs["display"]["show_frame_numbers"])
        self.show_tile_info_var.set(self.temp_prefs["display"]["show_tile_info"])
        
        # File management tab
        self.auto_cleanup_var.set(self.temp_prefs["file_management"]["auto_cleanup_orphaned"])
        self.backup_animations_var.set(self.temp_prefs["file_management"]["backup_animations"])
        
        # Advanced tab
        self.memory_limit_var.set(self.temp_prefs["advanced"]["memory_limit_mb"])
        self.undo_levels_var.set(self.temp_prefs["advanced"]["max_undo_levels"])
        self.cache_size_var.set(self.temp_prefs["advanced"]["tile_cache_size"])
        self.debug_logging_var.set(self.temp_prefs["advanced"]["enable_debug_logging"])
        self.background_processing_var.set(self.temp_prefs["advanced"]["background_processing"])
        if "use_aseprite_json" not in self.temp_prefs["advanced"]:
            self.temp_prefs["advanced"]["use_aseprite_json"] = False
        self.use_aseprite_json_var.set(self.temp_prefs["advanced"]["use_aseprite_json"])
    
    def collect_ui_values(self):
        """Collect values from UI controls into temporary preferences."""
        # General
        self.temp_prefs["general"]["default_export_dir"] = self.export_dir_var.get()
        self.temp_prefs["general"]["animation_naming_pattern"] = self.naming_pattern_var.get()
        self.temp_prefs["general"]["auto_save_interval"] = self.autosave_var.get()
        self.temp_prefs["general"]["recent_files_limit"] = self.recent_limit_var.get()
        self.temp_prefs["general"]["remember_window_state"] = self.remember_window_var.get()
        self.temp_prefs["general"]["show_tooltips"] = self.show_tooltips_var.get()
        
        # Display
        self.temp_prefs["display"]["grid_color"] = self.grid_color_var.get()
        self.temp_prefs["display"]["selection_color"] = self.selection_color_var.get()
        self.temp_prefs["display"]["ui_theme"] = self.theme_var.get()
        self.temp_prefs["display"]["show_frame_numbers"] = self.show_frame_numbers_var.get()
        self.temp_prefs["display"]["show_tile_info"] = self.show_tile_info_var.get()
        
        # File management
        self.temp_prefs["file_management"]["auto_cleanup_orphaned"] = self.auto_cleanup_var.get()
        self.temp_prefs["file_management"]["backup_animations"] = self.backup_animations_var.get()
        
        # Advanced
        self.temp_prefs["advanced"]["memory_limit_mb"] = self.memory_limit_var.get()
        self.temp_prefs["advanced"]["max_undo_levels"] = self.undo_levels_var.get()
        self.temp_prefs["advanced"]["tile_cache_size"] = self.cache_size_var.get()
        self.temp_prefs["advanced"]["enable_debug_logging"] = self.debug_logging_var.get()
        self.temp_prefs["advanced"]["background_processing"] = self.background_processing_var.get()
        # Commit advanced tab values (ensure key exists)
        self.temp_prefs["advanced"]["use_aseprite_json"] = self.use_aseprite_json_var.get()
    
    def ok(self):
        """Apply changes and close dialog."""
        self.collect_ui_values()
        self.prefs.preferences = self.temp_prefs
        self.prefs.save_preferences()
        self.dialog.destroy()
    
    def cancel(self):
        """Close dialog without applying changes."""
        self.dialog.destroy()


def show_preferences_dialog(parent, preferences_manager: PreferencesManager):
    """Show the preferences dialog."""
    SettingsDialog(parent, preferences_manager)
