"""
Enhanced file operations with native dialogs and improved user experience.
This implements Phase 1.8 Enhanced File Operations with cross-platform support.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional, Tuple
import json
from pathlib import Path


class EnhancedFileOperations:
    """Enhanced file operations with native dialogs and better UX."""
    
    def __init__(self, preferences_manager=None):
        """Initialize the enhanced file operations system."""
        # Hide the main tkinter window
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Store reference to preferences manager
        self.preferences = preferences_manager
        
        # Get application directory (where main.py is located)
        self.app_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Initialize default directories with smart defaults
        self._init_default_directories()
        
        # Supported file types
        self.sprite_filetypes = [
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("BMP files", "*.bmp"),
            ("All image files", "*.png *.jpg *.jpeg *.bmp"),
            ("All files", "*.*")
        ]
        
        self.json_filetypes = [
            ("JSON files", "*.json"),
            ("All files", "*.*")
        ]
    
    def _init_default_directories(self):
        """Initialize default directories with smart defaults and preference loading."""
        # Load last used directories from preferences if available
        if self.preferences:
            file_prefs = self.preferences.get_category("file_management")
            self.last_sprite_dir = file_prefs.get("last_sprite_dir", "")
            self.last_export_dir = file_prefs.get("last_export_dir", "")
        else:
            self.last_sprite_dir = ""
            self.last_export_dir = ""
        
        # If no saved directory or saved directory doesn't exist, use smart defaults
        if not self.last_sprite_dir or not os.path.exists(self.last_sprite_dir):
            # First check for Assets/Assests folder in app directory
            assets_dir = os.path.join(self.app_directory, "Assets")
            assests_dir = os.path.join(self.app_directory, "Assests")  # Handle typo in original
            
            if os.path.exists(assets_dir):
                self.last_sprite_dir = assets_dir
            elif os.path.exists(assests_dir):
                self.last_sprite_dir = assests_dir
            else:
                # Fall back to app directory itself
                self.last_sprite_dir = self.app_directory
        
        # Default export directory to app directory if not set
        if not self.last_export_dir or not os.path.exists(self.last_export_dir):
            self.last_export_dir = self.app_directory
    
    def _save_directory_preference(self, dir_type: str, directory: str):
        """Save directory preference for future use."""
        if self.preferences and directory:
            if dir_type == "sprite":
                self.preferences.set("file_management", "last_sprite_dir", directory)
            elif dir_type == "export":
                self.preferences.set("file_management", "last_export_dir", directory)
            self.preferences.save_preferences()
    
    def open_sprite_sheet_dialog(self, multiple: bool = False) -> Optional[List[str]]:
        """
        Show native file dialog to open sprite sheet(s) with smart directory handling.
        
        Args:
            multiple: If True, allow multiple file selection
            
        Returns:
            List of selected file paths, or None if cancelled
        """
        try:
            if multiple:
                files = filedialog.askopenfilenames(
                    title="Open Sprite Sheets",
                    initialdir=self.last_sprite_dir,
                    filetypes=self.sprite_filetypes
                )
                if files:
                    # Update last used directory and save to preferences
                    self.last_sprite_dir = os.path.dirname(files[0])
                    self._save_directory_preference("sprite", self.last_sprite_dir)
                    return list(files)
            else:
                file = filedialog.askopenfilename(
                    title="Open Sprite Sheet",
                    initialdir=self.last_sprite_dir,
                    filetypes=self.sprite_filetypes
                )
                if file:
                    # Update last used directory and save to preferences
                    self.last_sprite_dir = os.path.dirname(file)
                    self._save_directory_preference("sprite", self.last_sprite_dir)
                    return [file]
            
            return None
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file dialog: {str(e)}")
            return None
    
    def save_animation_dialog(self, default_name: str = "animation", 
                            suggested_dir: str = None) -> Optional[Tuple[str, str]]:
        """
        Show save dialog for animation export with smart directory handling.
        
        Args:
            default_name: Default animation name
            suggested_dir: Suggested directory path
            
        Returns:
            Tuple of (file_path, animation_name) or None if cancelled
        """
        try:
            # Use suggested directory or last export directory
            initial_dir = suggested_dir or self.last_export_dir
            
            # Ensure directory exists
            if not os.path.exists(initial_dir):
                initial_dir = self.last_export_dir
            
            file_path = filedialog.asksaveasfilename(
                title="Save Animation",
                initialdir=initial_dir,
                initialfile=f"{default_name}.json",
                filetypes=self.json_filetypes,
                defaultextension=".json"
            )
            
            if file_path:
                # Update last used directory and save to preferences
                self.last_export_dir = os.path.dirname(file_path)
                self._save_directory_preference("export", self.last_export_dir)
                # Extract animation name from filename
                animation_name = os.path.splitext(os.path.basename(file_path))[0]
                return file_path, animation_name
            
            return None
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open save dialog: {str(e)}")
            return None
    
    def confirm_overwrite(self, file_path: str) -> bool:
        """
        Show confirmation dialog for file overwrite.
        
        Args:
            file_path: Path to the file that would be overwritten
            
        Returns:
            True if user confirms overwrite, False otherwise
        """
        if not os.path.exists(file_path):
            return True
            
        filename = os.path.basename(file_path)
        return messagebox.askyesno(
            "Confirm Overwrite",
            f"The file '{filename}' already exists.\n\nDo you want to overwrite it?",
            icon="warning"
        )
    
    def show_export_success(self, animation_name: str, export_paths: List[str]):
        """
        Show export success notification with details.
        
        Args:
            animation_name: Name of the exported animation
            export_paths: List of exported file paths
        """
        files_text = "\n".join(f"• {os.path.basename(path)}" for path in export_paths)
        export_dir = os.path.dirname(export_paths[0]) if export_paths else ""
        
        result = messagebox.askquestion(
            "Export Successful",
            f"Animation '{animation_name}' exported successfully!\n\nFiles created:\n{files_text}\n\nWould you like to open the export folder?",
            icon="question"
        )
        
        if result == 'yes' and export_dir:
            self.open_folder(export_dir)
    
    def show_error(self, title: str, message: str):
        """Show error dialog."""
        messagebox.showerror(title, message)
    
    def show_warning(self, title: str, message: str) -> bool:
        """Show warning dialog with OK/Cancel."""
        return messagebox.askokcancel(title, message, icon="warning")
    
    def show_info(self, title: str, message: str):
        """Show information dialog."""
        messagebox.showinfo(title, message)
    
    def open_folder(self, folder_path: str):
        """Open folder in system file explorer."""
        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                os.system(f"open '{folder_path}'")
            else:
                os.system(f"xdg-open '{folder_path}'")
        except Exception as e:
            print(f"Could not open folder: {e}")
    
    def get_recent_files(self, max_files: int = 10) -> List[str]:
        """
        Get list of recent sprite sheet files.
        
        Args:
            max_files: Maximum number of recent files to return
            
        Returns:
            List of recent file paths
        """
        # This would be loaded from preferences in a full implementation
        # For now, return empty list
        return []
    
    def add_to_recent(self, file_path: str):
        """
        Add file to recent files list.
        
        Args:
            file_path: Path to add to recent files
        """
        # This would save to preferences in a full implementation
        pass
    
    def validate_sprite_sheet(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate sprite sheet file before loading.
        
        Args:
            file_path: Path to the sprite sheet file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        if not os.path.isfile(file_path):
            return False, "Path is not a file"
        
        # Check file extension
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in valid_extensions:
            return False, f"Unsupported file type: {ext}"
        
        # Check file size (warn for very large files)
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > 50:  # 50MB warning threshold
                return True, f"Warning: Large file ({size_mb:.1f}MB) - loading may be slow"
        except OSError:
            return False, "Could not access file"
        
        return True, ""
    
    def cleanup(self):
        """Clean up resources."""
        if self.root:
            self.root.destroy()


class ExportProgressDialog:
    """Progress dialog for export operations."""
    
    def __init__(self, title: str = "Exporting Animation"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x150")
        self.root.resizable(False, False)
        
        # Center the dialog
        self.root.transient()
        self.root.grab_set()
        
        # Progress information
        self.status_var = tk.StringVar(value="Initializing...")
        self.progress_var = tk.StringVar(value="0%")
        
        self._setup_ui()
        self.cancelled = False
    
    def _setup_ui(self):
        """Set up the progress dialog UI."""
        # Status label
        status_label = tk.Label(self.root, textvariable=self.status_var, 
                               font=("Arial", 10))
        status_label.pack(pady=20)
        
        # Progress label
        progress_label = tk.Label(self.root, textvariable=self.progress_var,
                                 font=("Arial", 10, "bold"))
        progress_label.pack(pady=10)
        
        # Cancel button
        cancel_button = tk.Button(self.root, text="Cancel", 
                                 command=self._cancel, width=10)
        cancel_button.pack(pady=10)
    
    def update_status(self, status: str, progress: float = None):
        """Update the progress dialog status."""
        self.status_var.set(status)
        if progress is not None:
            self.progress_var.set(f"{progress:.0f}%")
        self.root.update()
    
    def _cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        self.close()
    
    def close(self):
        """Close the progress dialog."""
        if self.root:
            self.root.destroy()
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self.cancelled
