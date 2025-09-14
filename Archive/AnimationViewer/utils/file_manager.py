"""
File management utilities for the sprite animation tool.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional, Tuple


class FileManager:
    """
    Handles file operations with native dialogs and cross-platform compatibility.
    """
    
    def __init__(self):
        """Initialize file manager."""
        # Initialize tkinter root for dialogs (hidden)
        self._tk_root = None
        self._last_directories = {
            'sprite_sheet': '',
            'animation': '',
            'project': '',
            'export': ''
        }
    
    def _ensure_tk_root(self):
        """Ensure tkinter root exists for dialogs."""
        if self._tk_root is None:
            self._tk_root = tk.Tk()
            self._tk_root.withdraw()  # Hide the root window
            
    def open_sprite_sheet_dialog(self, multiple: bool = False) -> Optional[List[str]]:
        """
        Open file dialog for sprite sheet selection.
        
        Args:
            multiple: Allow multiple file selection
            
        Returns:
            List of selected file paths or None if cancelled
        """
        self._ensure_tk_root()
        
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tga"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*")
        ]
        
        initial_dir = self._last_directories.get('sprite_sheet', os.getcwd())
        
        try:
            if multiple:
                filenames = filedialog.askopenfilenames(
                    title="Open Sprite Sheet(s)",
                    initialdir=initial_dir,
                    filetypes=filetypes
                )
                if filenames:
                    self._last_directories['sprite_sheet'] = os.path.dirname(filenames[0])
                    return list(filenames)
            else:
                filename = filedialog.askopenfilename(
                    title="Open Sprite Sheet",
                    initialdir=initial_dir,
                    filetypes=filetypes
                )
                if filename:
                    self._last_directories['sprite_sheet'] = os.path.dirname(filename)
                    return [filename]
        except Exception as e:
            print(f"File dialog error: {e}")
        
        return None
    
    def save_animation_dialog(self, default_name: str = "animation") -> Optional[str]:
        """
        Open save dialog for animation export.
        
        Args:
            default_name: Default filename
            
        Returns:
            Selected file path or None if cancelled
        """
        self._ensure_tk_root()
        
        filetypes = [
            ("JSON files", "*.json"),
            ("Python files", "*.py"),
            ("All files", "*.*")
        ]
        
        initial_dir = self._last_directories.get('animation', os.getcwd())
        
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Animation",
                initialdir=initial_dir,
                initialfile=f"{default_name}.json",
                filetypes=filetypes,
                defaultextension=".json"
            )
            if filename:
                self._last_directories['animation'] = os.path.dirname(filename)
                return filename
        except Exception as e:
            print(f"File dialog error: {e}")
        
        return None
    
    def open_project_dialog(self) -> Optional[str]:
        """
        Open dialog for project file selection.
        
        Returns:
            Selected project file path or None if cancelled
        """
        self._ensure_tk_root()
        
        filetypes = [
            ("Project files", "*.sap"),  # Sprite Animation Project
            ("JSON files", "*.json"),
            ("All files", "*.*")
        ]
        
        initial_dir = self._last_directories.get('project', os.getcwd())
        
        try:
            filename = filedialog.askopenfilename(
                title="Open Project",
                initialdir=initial_dir,
                filetypes=filetypes
            )
            if filename:
                self._last_directories['project'] = os.path.dirname(filename)
                return filename
        except Exception as e:
            print(f"File dialog error: {e}")
        
        return None
    
    def save_project_dialog(self, default_name: str = "project") -> Optional[str]:
        """
        Open save dialog for project.
        
        Args:
            default_name: Default filename
            
        Returns:
            Selected file path or None if cancelled
        """
        self._ensure_tk_root()
        
        filetypes = [
            ("Project files", "*.sap"),
            ("JSON files", "*.json"),
            ("All files", "*.*")
        ]
        
        initial_dir = self._last_directories.get('project', os.getcwd())
        
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Project",
                initialdir=initial_dir,
                initialfile=f"{default_name}.sap",
                filetypes=filetypes,
                defaultextension=".sap"
            )
            if filename:
                self._last_directories['project'] = os.path.dirname(filename)
                return filename
        except Exception as e:
            print(f"File dialog error: {e}")
        
        return None
    
    def choose_export_directory(self) -> Optional[str]:
        """
        Open dialog for export directory selection.
        
        Returns:
            Selected directory path or None if cancelled
        """
        self._ensure_tk_root()
        
        initial_dir = self._last_directories.get('export', os.getcwd())
        
        try:
            dirname = filedialog.askdirectory(
                title="Choose Export Directory",
                initialdir=initial_dir
            )
            if dirname:
                self._last_directories['export'] = dirname
                return dirname
        except Exception as e:
            print(f"Directory dialog error: {e}")
        
        return None
    
    def show_error_dialog(self, title: str, message: str):
        """
        Show an error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        self._ensure_tk_root()
        try:
            messagebox.showerror(title, message)
        except Exception as e:
            print(f"Error dialog failed: {e}")
            print(f"Original error - {title}: {message}")
    
    def show_warning_dialog(self, title: str, message: str):
        """
        Show a warning dialog.
        
        Args:
            title: Dialog title
            message: Warning message
        """
        self._ensure_tk_root()
        try:
            messagebox.showwarning(title, message)
        except Exception as e:
            print(f"Warning dialog failed: {e}")
            print(f"Original warning - {title}: {message}")
    
    def show_info_dialog(self, title: str, message: str):
        """
        Show an information dialog.
        
        Args:
            title: Dialog title
            message: Information message
        """
        self._ensure_tk_root()
        try:
            messagebox.showinfo(title, message)
        except Exception as e:
            print(f"Info dialog failed: {e}")
            print(f"Original info - {title}: {message}")
    
    def confirm_dialog(self, title: str, message: str) -> bool:
        """
        Show a confirmation dialog.
        
        Args:
            title: Dialog title
            message: Confirmation message
            
        Returns:
            True if user confirmed, False otherwise
        """
        self._ensure_tk_root()
        try:
            return messagebox.askyesno(title, message)
        except Exception as e:
            print(f"Confirm dialog failed: {e}")
            print(f"Original question - {title}: {message}")
            return False
    
    def validate_file_path(self, filepath: str) -> Tuple[bool, str]:
        """
        Validate a file path.
        
        Args:
            filepath: File path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filepath:
            return False, "File path is empty"
        
        if not os.path.exists(filepath):
            return False, f"File does not exist: {filepath}"
        
        if not os.path.isfile(filepath):
            return False, f"Path is not a file: {filepath}"
        
        if not os.access(filepath, os.R_OK):
            return False, f"File is not readable: {filepath}"
        
        return True, ""
    
    def validate_directory_path(self, dirpath: str) -> Tuple[bool, str]:
        """
        Validate a directory path.
        
        Args:
            dirpath: Directory path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not dirpath:
            return False, "Directory path is empty"
        
        if not os.path.exists(dirpath):
            return False, f"Directory does not exist: {dirpath}"
        
        if not os.path.isdir(dirpath):
            return False, f"Path is not a directory: {dirpath}"
        
        if not os.access(dirpath, os.R_OK):
            return False, f"Directory is not readable: {dirpath}"
        
        return True, ""
    
    def get_file_size(self, filepath: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            filepath: File path
            
        Returns:
            File size in bytes, or 0 if error
        """
        try:
            return os.path.getsize(filepath)
        except Exception:
            return 0
    
    def get_relative_path(self, filepath: str, base_path: str) -> str:
        """
        Get relative path from base path.
        
        Args:
            filepath: File path
            base_path: Base path for relative calculation
            
        Returns:
            Relative path
        """
        try:
            return os.path.relpath(filepath, base_path)
        except Exception:
            return filepath
    
    def cleanup(self):
        """Cleanup resources."""
        if self._tk_root:
            try:
                self._tk_root.destroy()
            except Exception:
                pass
            self._tk_root = None
