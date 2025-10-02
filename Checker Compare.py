import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
import os
import glob
from pathlib import Path
import hashlib
import datetime

class ImageViewer:
    def __init__(self, parent, image_path, image_type):
        self.parent = parent
        self.image_path = image_path
        self.image_type = image_type
        self.zoom_factor = 1.0
        self.original_image = None
        self.current_image = None
        self.photo = None
        self.notebook = None
        self.hex_image_data = None
        self.image_scale_factor = 1.0
        
        self.setup_viewer()
        
    def setup_viewer(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"Image Viewer - {self.image_type}")
        self.window.geometry("1200x900")
        
        # Create main frames
        control_frame = ttk.Frame(self.window)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        content_frame = ttk.Frame(self.window)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        ttk.Button(control_frame, text="Zoom In (+)", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Zoom Out (-)", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Reset Zoom", command=self.reset_zoom).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Fit to Window", command=self.fit_to_window).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Show Properties", command=self.show_properties).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Show Hex", command=self.show_hex_editor).pack(side=tk.LEFT, padx=2)
        
        # Toggle hex hover feature
        self.hex_hover_var = tk.BooleanVar(value=False)
        hex_hover_cb = ttk.Checkbutton(control_frame, text="Hex Hover", variable=self.hex_hover_var, 
                                      command=self.toggle_hex_hover)
        hex_hover_cb.pack(side=tk.LEFT, padx=10)
        
        self.zoom_label = ttk.Label(control_frame, text="Zoom: 100%")
        self.zoom_label.pack(side=tk.LEFT, padx=10)
        
        # Create notebook for image, properties, hex editor, and hex overlay
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Image frame with scrollbars
        image_frame = ttk.Frame(self.notebook)
        self.notebook.add(image_frame, text="Image")
        
        self.canvas = tk.Canvas(image_frame, bg='white')
        v_scrollbar = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Properties frame
        properties_frame = ttk.Frame(self.notebook)
        self.notebook.add(properties_frame, text="Properties")
        
        self.properties_text = scrolledtext.ScrolledText(properties_frame, wrap=tk.WORD, font=('Consolas', 10))
        self.properties_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Hex Editor frame
        hex_frame = ttk.Frame(self.notebook)
        self.notebook.add(hex_frame, text="Hex Editor")
        
        # Hex editor controls
        hex_controls = ttk.Frame(hex_frame)
        hex_controls.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(hex_controls, text="Bytes to show:").pack(side=tk.LEFT, padx=(0, 5))
        self.bytes_var = tk.StringVar(value="1024")
        bytes_entry = ttk.Entry(hex_controls, textvariable=self.bytes_var, width=10)
        bytes_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(hex_controls, text="Start offset:").pack(side=tk.LEFT, padx=(10, 5))
        self.offset_var = tk.StringVar(value="0")
        offset_entry = ttk.Entry(hex_controls, textvariable=self.offset_var, width=10)
        offset_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(hex_controls, text="Refresh", command=self.refresh_hex).pack(side=tk.LEFT, padx=10)
        ttk.Button(hex_controls, text="Search Pattern", command=self.search_pattern).pack(side=tk.LEFT, padx=5)
        
        # Pattern search
        search_frame = ttk.Frame(hex_frame)
        search_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(search_frame, text="Pattern (hex):").pack(side=tk.LEFT, padx=(0, 5))
        self.pattern_var = tk.StringVar(value="FF D8 FF")  # JPEG header example
        pattern_entry = ttk.Entry(search_frame, textvariable=self.pattern_var, width=20)
        pattern_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        self.hex_text = scrolledtext.ScrolledText(hex_frame, wrap=tk.NONE, font=('Consolas', 9))
        self.hex_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # NEW: Hex Overlay frame
        hex_overlay_frame = ttk.Frame(self.notebook)
        self.notebook.add(hex_overlay_frame, text="Hex Overlay")
        
        # Create paned window for hex overlay
        hex_paned = ttk.PanedWindow(hex_overlay_frame, orient=tk.HORIZONTAL)
        hex_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side: Image with hex interaction
        left_frame = ttk.Frame(hex_paned)
        hex_paned.add(left_frame, weight=2)
        
        # Image canvas for hex interaction
        self.hex_image_canvas = tk.Canvas(left_frame, bg='white')
        hex_v_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.hex_image_canvas.yview)
        hex_h_scrollbar = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.hex_image_canvas.xview)
        self.hex_image_canvas.configure(yscrollcommand=hex_v_scrollbar.set, xscrollcommand=hex_h_scrollbar.set)
        
        hex_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        hex_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.hex_image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right side: Pixel info and mini hex view
        right_frame = ttk.Frame(hex_paned)
        hex_paned.add(right_frame, weight=1)
        
        # Pixel info display
        info_label = ttk.Label(right_frame, text="Pixel Information", font=('Arial', 12, 'bold'))
        info_label.pack(pady=(0, 5))
        
        self.pixel_info_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=10, font=('Consolas', 9))
        self.pixel_info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.pixel_info_text.insert(tk.END, "Hover over image to see pixel hex data")
        
        # Reset button for hex overlay
        reset_button = ttk.Button(right_frame, text="Reset View", command=self.reset_hex_image_view)
        reset_button.pack(pady=5)
        
        # Load and display image
        self.load_image()
        self.load_hex_image()  # Load image for hex interaction
        self.update_display()
        
        # Bind mouse events for panning (main canvas)
        self.canvas.bind("<Button-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)
        self.canvas.bind("<MouseWheel>", self.mouse_zoom)
        
        # Bind mouse events for hex hovering (when enabled)
        self.setup_hex_hover_bindings()
        
        # Bind keyboard shortcuts
        self.window.bind("<Key>", self.keyboard_shortcuts)
        self.window.focus_set()
        
    def toggle_hex_hover(self):
        """Toggle hex hover functionality on main image"""
        if self.hex_hover_var.get():
            self.setup_hex_hover_bindings()
        else:
            self.remove_hex_hover_bindings()
    
    def setup_hex_hover_bindings(self):
        """Setup hex hover bindings on main canvas"""
        self.canvas.bind("<Motion>", self.on_main_canvas_hover)
        self.canvas.bind("<Leave>", self.on_main_canvas_leave)
        
    def remove_hex_hover_bindings(self):
        """Remove hex hover bindings from main canvas"""
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<Leave>")
    
    def on_main_canvas_hover(self, event):
        """Handle hover on main canvas with hex info"""
        if not self.hex_hover_var.get() or not self.original_image:
            return
            
        try:
            # Get canvas coordinates and convert to image coordinates
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            # Convert to original image coordinates considering zoom
            img_x = int(canvas_x / self.zoom_factor)
            img_y = int(canvas_y / self.zoom_factor)
            
            # Check if coordinates are within image bounds
            if 0 <= img_x < self.original_image.width and 0 <= img_y < self.original_image.height:
                # Get pixel info
                pixel_info = self.get_pixel_hex_info(img_x, img_y, self.original_image)
                
                # Create tooltip-style display
                self.show_hex_tooltip(event.x, event.y, pixel_info, img_x, img_y)
        except Exception as e:
            pass  # Silently handle errors during hover
    
    def on_main_canvas_leave(self, event):
        """Handle mouse leaving main canvas"""
        self.hide_hex_tooltip()
    
    def show_hex_tooltip(self, canvas_x, canvas_y, pixel_info, img_x, img_y):
        """Show hex information as tooltip"""
        # Remove existing tooltip
        self.hide_hex_tooltip()
        
        if 'error' in pixel_info:
            return
        
        # Create tooltip text
        tooltip_text = f"({img_x}, {img_y})\n"
        
        if pixel_info['mode'] == 'RGBA':
            r, g, b, a = pixel_info['rgb']
            tooltip_text += f"RGBA: {r},{g},{b},{a}\nHex: {pixel_info['hex_rgb']}"
        elif pixel_info['mode'] == 'L':
            gray = pixel_info['rgb'][0]
            tooltip_text += f"Gray: {gray}\nHex: {gray:02X}"
        else:
            r, g, b = pixel_info['rgb']
            tooltip_text += f"RGB: {r},{g},{b}\nHex: {pixel_info['hex_rgb']}"
        
        if pixel_info.get('hex_offset') is not None:
            tooltip_text += f"\nOffset: 0x{pixel_info['hex_offset']:08X}"
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.canvas)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.configure(bg='lightyellow', relief='solid', borderwidth=1)
        
        label = tk.Label(self.tooltip, text=tooltip_text, bg='lightyellow', 
                        font=('Consolas', 9), justify='left')
        label.pack()
        
        # Position tooltip near cursor
        root_x = self.canvas.winfo_rootx() + canvas_x + 10
        root_y = self.canvas.winfo_rooty() + canvas_y - 10
        self.tooltip.geometry(f"+{root_x}+{root_y}")
    
    def hide_hex_tooltip(self):
        """Hide hex tooltip"""
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        
    def load_image(self):
        try:
            self.original_image = Image.open(self.image_path)
            self.current_image = self.original_image.copy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            
    def update_display(self):
        if not self.current_image:
            return
            
        # Calculate new size based on zoom factor
        new_width = int(self.original_image.width * self.zoom_factor)
        new_height = int(self.original_image.height * self.zoom_factor)
        
        # Resize image
        if self.zoom_factor < 1:
            resample = Image.Resampling.LANCZOS
        else:
            resample = Image.Resampling.NEAREST  # Better for pixel-level inspection when zoomed in
            
        display_image = self.original_image.resize((new_width, new_height), resample)
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(display_image)
        
        # Clear canvas and add image
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Update zoom label
        self.zoom_label.config(text=f"Zoom: {int(self.zoom_factor * 100)}%")
        
    def zoom_in(self):
        self.zoom_factor *= 1.5
        if self.zoom_factor > 10:  # Max zoom limit
            self.zoom_factor = 10
        self.update_display()
        
    def zoom_out(self):
        self.zoom_factor /= 1.5
        if self.zoom_factor < 0.1:  # Min zoom limit
            self.zoom_factor = 0.1
        self.update_display()
        
    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.update_display()
        
    def fit_to_window(self):
        if not self.original_image:
            return
            
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Make sure canvas is initialized
            zoom_x = canvas_width / self.original_image.width
            zoom_y = canvas_height / self.original_image.height
            self.zoom_factor = min(zoom_x, zoom_y) * 0.9  # 90% to leave some margin
            self.update_display()
    
    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
        
    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        
    def mouse_zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
            
    def keyboard_shortcuts(self, event):
        if event.keysym == 'plus' or event.keysym == 'equal':
            self.zoom_in()
        elif event.keysym == 'minus':
            self.zoom_out()
        elif event.keysym == '0':
            self.reset_zoom()
        elif event.keysym == 'f':
            self.fit_to_window()
        elif event.keysym == 'h':
            self.hex_hover_var.set(not self.hex_hover_var.get())
            self.toggle_hex_hover()
            
    def show_properties(self):
        try:
            properties = self.get_image_properties()
            self.properties_text.delete(1.0, tk.END)
            self.properties_text.insert(tk.END, properties)
            
            # Switch to properties tab
            if self.notebook:
                self.notebook.select(1)  # Properties tab is index 1
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract properties: {str(e)}")
    
    def show_hex_editor(self):
        try:
            self.refresh_hex()
            
            # Switch to hex editor tab
            if self.notebook:
                self.notebook.select(2)  # Hex tab is index 2
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open hex editor: {str(e)}")
    
    def refresh_hex(self):
        try:
            bytes_to_read = int(self.bytes_var.get())
            start_offset = int(self.offset_var.get())
            
            with open(self.image_path, 'rb') as f:
                f.seek(start_offset)
                data = f.read(bytes_to_read)
            
            hex_content = self.format_hex_data(data, start_offset)
            self.hex_text.delete(1.0, tk.END)
            self.hex_text.insert(tk.END, hex_content)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number format")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {str(e)}")
    
    def format_hex_data(self, data, start_offset=0):
        lines = []
        lines.append(f"Hex view of {os.path.basename(self.image_path)}")
        lines.append(f"Starting at offset: 0x{start_offset:08X} ({start_offset})")
        lines.append(f"Showing {len(data)} bytes")
        lines.append("-" * 80)
        lines.append("Offset    00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  ASCII")
        lines.append("-" * 80)
        
        for i in range(0, len(data), 16):
            offset = start_offset + i
            chunk = data[i:i+16]
            
            # Format hex bytes
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            hex_part = hex_part.ljust(47)  # Pad to align ASCII
            
            # Format ASCII representation
            ascii_part = ""
            for b in chunk:
                if 32 <= b <= 126:  # Printable ASCII
                    ascii_part += chr(b)
                else:
                    ascii_part += "."
            
            lines.append(f"{offset:08X}  {hex_part}  {ascii_part}")
        
        # Add pattern analysis
        lines.append("\n" + "=" * 80)
        lines.append("PATTERN ANALYSIS")
        lines.append("=" * 80)
        
        # Check for common file signatures
        signatures = {
            b'\xFF\xD8\xFF': "JPEG image",
            b'\x89PNG\r\n\x1a\n': "PNG image",
            b'BM': "BMP image",
            b'GIF8': "GIF image",
            b'RIFF': "RIFF container (WAV/AVI)",
            b'%PDF': "PDF document",
            b'PK\x03\x04': "ZIP/JAR archive",
            b'\x50\x4B\x03\x04': "ZIP archive",
            b'\x7F\x45\x4C\x46': "ELF executable"
        }
        
        found_signatures = []
        for sig, desc in signatures.items():
            if sig in data:
                pos = data.find(sig)
                found_signatures.append(f"Found {desc} signature at offset +{pos} (0x{start_offset + pos:08X})")
        
        if found_signatures:
            lines.append("File signatures found:")
            lines.extend(found_signatures)
        else:
            lines.append("No known file signatures found in this range")
        
        # Entropy analysis (simple)
        if len(data) > 0:
            byte_counts = [0] * 256
            for b in data:
                byte_counts[b] += 1
            
            # Calculate simple entropy indicator
            unique_bytes = sum(1 for count in byte_counts if count > 0)
            entropy_indicator = unique_bytes / 256.0
            
            lines.append(f"\nEntropy indicator: {entropy_indicator:.3f}")
            lines.append(f"Unique bytes: {unique_bytes}/256")
            
            if entropy_indicator > 0.8:
                lines.append("High entropy - possible compressed/encrypted data")
            elif entropy_indicator < 0.3:
                lines.append("Low entropy - repetitive data pattern")
            else:
                lines.append("Medium entropy - mixed data")
        
        return "\n".join(lines)
    
    def load_hex_image(self):
        """Load image for hex overlay interaction"""
        try:
            # Load image data for hex mapping
            with open(self.image_path, 'rb') as f:
                self.hex_image_data = f.read()
            
            # Load PIL image for display
            pil_image = Image.open(self.image_path)
            
            # Scale image to reasonable size for interaction
            max_size = 600
            if pil_image.width > max_size or pil_image.height > max_size:
                self.image_scale_factor = min(max_size / pil_image.width, max_size / pil_image.height)
                new_size = (int(pil_image.width * self.image_scale_factor), 
                           int(pil_image.height * self.image_scale_factor))
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            else:
                self.image_scale_factor = 1.0
            
            # Convert to PhotoImage
            self.hex_image_photo = ImageTk.PhotoImage(pil_image)
            
            # Display on canvas
            self.hex_image_canvas.delete("all")
            self.hex_image_canvas.create_image(0, 0, anchor=tk.NW, image=self.hex_image_photo)
            self.hex_image_canvas.configure(scrollregion=self.hex_image_canvas.bbox("all"))
            
            # Bind mouse events for pixel inspection
            self.hex_image_canvas.bind("<Motion>", self.on_mouse_move_hex)
            self.hex_image_canvas.bind("<Button-1>", self.on_click_hex_image)
            self.hex_image_canvas.bind("<Leave>", self.on_mouse_leave_hex)
            
        except Exception as e:
            print(f"Error loading hex image: {e}")
    
    def on_mouse_move_hex(self, event):
        """Handle mouse movement over hex image"""
        try:
            # Get canvas coordinates
            canvas_x = self.hex_image_canvas.canvasx(event.x)
            canvas_y = self.hex_image_canvas.canvasy(event.y)
            
            # Convert to image coordinates (accounting for scaling)
            img_x = int(canvas_x / self.image_scale_factor) if self.image_scale_factor > 0 else int(canvas_x)
            img_y = int(canvas_y / self.image_scale_factor) if self.image_scale_factor > 0 else int(canvas_y)
            
            # Get original image dimensions
            with Image.open(self.image_path) as orig_img:
                img_width, img_height = orig_img.size
                
                if 0 <= img_x < img_width and 0 <= img_y < img_height:
                    # Calculate pixel data and hex offset
                    pixel_info = self.get_pixel_hex_info(img_x, img_y, orig_img)
                    self.display_pixel_info(pixel_info, img_x, img_y)
                    
                    # Highlight hex in the hex viewer
                    if pixel_info.get('hex_offset') is not None:
                        self.highlight_hex_bytes(pixel_info['hex_offset'], pixel_info.get('bytes_per_pixel', 3))
                        
        except Exception as e:
            pass  # Silently handle errors during mouse movement
    
    def on_click_hex_image(self, event):
        """Handle click on hex image"""
        try:
            # Get canvas coordinates
            canvas_x = self.hex_image_canvas.canvasx(event.x)
            canvas_y = self.hex_image_canvas.canvasy(event.y)
            
            # Convert to image coordinates
            img_x = int(canvas_x / self.image_scale_factor) if self.image_scale_factor > 0 else int(canvas_x)
            img_y = int(canvas_y / self.image_scale_factor) if self.image_scale_factor > 0 else int(canvas_y)
            
            with Image.open(self.image_path) as orig_img:
                img_width, img_height = orig_img.size
                
                if 0 <= img_x < img_width and 0 <= img_y < img_height:
                    pixel_info = self.get_pixel_hex_info(img_x, img_y, orig_img)
                    
                    # Jump to hex offset
                    if pixel_info.get('hex_offset') is not None:
                        hex_offset = pixel_info['hex_offset']
                        self.offset_var.set(str(max(0, hex_offset - 64)))  # Show some context
                        self.refresh_hex()
                        # Switch to hex editor tab
                        self.notebook.select(2)
                        
        except Exception as e:
            pass
    
    def on_mouse_leave_hex(self, event):
        """Handle mouse leaving hex image"""
        self.pixel_info_text.delete(1.0, tk.END)
        self.pixel_info_text.insert(tk.END, "Hover over image to see pixel hex data")
        self.clear_hex_highlight()
    
    def get_pixel_hex_info(self, x, y, pil_image):
        """Get hex information for a specific pixel"""
        try:
            # Get pixel RGB values
            pixel_rgb = pil_image.getpixel((x, y))
            
            # Handle different image modes
            if pil_image.mode == 'RGB':
                r, g, b = pixel_rgb[:3]
                bytes_per_pixel = 3
            elif pil_image.mode == 'RGBA':
                r, g, b, a = pixel_rgb[:4]
                bytes_per_pixel = 4
            elif pil_image.mode == 'L':  # Grayscale
                r = g = b = pixel_rgb
                bytes_per_pixel = 1
            else:
                # Convert to RGB for analysis
                rgb_img = pil_image.convert('RGB')
                r, g, b = rgb_img.getpixel((x, y))
                bytes_per_pixel = 3
            
            # Calculate approximate hex offset in file
            # This is a rough estimation - actual offset depends on image format
            img_width, img_height = pil_image.size
            
            # Find image data start (skip headers)
            image_data_start = self.find_image_data_start()
            
            # Calculate pixel offset within image data
            pixel_index = (y * img_width + x) * bytes_per_pixel
            hex_offset = image_data_start + pixel_index
            
            # Ensure offset is within file bounds
            if hex_offset >= len(self.hex_image_data):
                hex_offset = None
            
            return {
                'x': x, 'y': y,
                'rgb': (r, g, b) if pil_image.mode != 'RGBA' else (r, g, b, pixel_rgb[3]),
                'hex_rgb': f"{r:02X} {g:02X} {b:02X}" if pil_image.mode != 'RGBA' else f"{r:02X} {g:02X} {b:02X} {pixel_rgb[3]:02X}",
                'hex_offset': hex_offset,
                'bytes_per_pixel': bytes_per_pixel,
                'mode': pil_image.mode
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def find_image_data_start(self):
        """Find approximate start of image data in file"""
        try:
            # Look for common image format markers
            if self.hex_image_data[:4] == b'\x89PNG':
                # PNG - look for IDAT chunk
                pos = self.hex_image_data.find(b'IDAT')
                if pos != -1:
                    return pos + 8  # Skip chunk length and type
                return 100  # Rough estimate
            elif self.hex_image_data[:3] == b'\xFF\xD8\xFF':
                # JPEG - look for scan data after headers
                pos = self.hex_image_data.find(b'\xFF\xDA')  # Start of Scan
                if pos != -1:
                    # Skip SOS marker and header
                    return pos + 12  # Rough estimate
                return 200  # Rough estimate
            elif self.hex_image_data[:2] == b'BM':
                # BMP - pixel data starts at offset specified in header
                if len(self.hex_image_data) >= 14:
                    offset = int.from_bytes(self.hex_image_data[10:14], 'little')
                    return offset
                return 54  # Standard BMP header size
            else:
                return 100  # Default estimate
        except:
            return 100
    
    def display_pixel_info(self, pixel_info, x, y):
        """Display pixel information in the info panel"""
        self.pixel_info_text.delete(1.0, tk.END)
        
        if 'error' in pixel_info:
            self.pixel_info_text.insert(tk.END, f"Error: {pixel_info['error']}")
            return
        
        info_lines = []
        info_lines.append(f"Pixel Coordinates: ({x}, {y})")
        
        if pixel_info['mode'] == 'RGBA':
            r, g, b, a = pixel_info['rgb']
            info_lines.append(f"RGBA Values: R={r}, G={g}, B={b}, A={a}")
            info_lines.append(f"Hex Values: {pixel_info['hex_rgb']}")
        elif pixel_info['mode'] == 'L':
            gray = pixel_info['rgb'][0]
            info_lines.append(f"Grayscale Value: {gray}")
            info_lines.append(f"Hex Value: {gray:02X}")
        else:
            r, g, b = pixel_info['rgb']
            info_lines.append(f"RGB Values: R={r}, G={g}, B={b}")
            info_lines.append(f"Hex Values: {pixel_info['hex_rgb']}")
        
        if pixel_info.get('hex_offset') is not None:
            info_lines.append(f"Approx. File Offset: 0x{pixel_info['hex_offset']:08X} ({pixel_info['hex_offset']})")
            info_lines.append("Click to jump to hex location")
        else:
            info_lines.append("Offset: Beyond file bounds")
        
        self.pixel_info_text.insert(tk.END, "\n".join(info_lines))
    
    def highlight_hex_bytes(self, offset, num_bytes):
        """Highlight specific bytes in hex viewer"""
        try:
            current_offset = int(self.offset_var.get())
            bytes_shown = int(self.bytes_var.get())
            
            # Check if the offset is within current view
            if current_offset <= offset < current_offset + bytes_shown:
                # Calculate line and position within hex view
                relative_offset = offset - current_offset
                line_num = relative_offset // 16
                byte_pos = relative_offset % 16
                
                # Clear previous highlights
                self.hex_text.tag_remove("highlight", "1.0", tk.END)
                
                # Add highlight
                # Line format: "00000000  FF FF FF FF ... ASCII"
                # Skip offset (10 chars) and find hex position
                start_line = line_num + 6  # Account for header lines
                start_col = 10 + (byte_pos * 3)  # 10 for offset, 3 chars per byte
                
                for i in range(num_bytes):
                    if byte_pos + i < 16:  # Don't go beyond current line
                        byte_start = f"{start_line}.{start_col + (i * 3)}"
                        byte_end = f"{start_line}.{start_col + (i * 3) + 2}"
                        self.hex_text.tag_add("highlight", byte_start, byte_end)
                
                # Configure highlight tag
                self.hex_text.tag_config("highlight", background="yellow", foreground="black")
                
        except Exception as e:
            pass
    
    def clear_hex_highlight(self):
        """Clear hex highlights"""
        try:
            self.hex_text.tag_remove("highlight", "1.0", tk.END)
        except:
            pass
    
    def reset_hex_image_view(self):
        """Reset hex image view"""
        try:
            self.load_hex_image()
            self.pixel_info_text.delete(1.0, tk.END)
            self.pixel_info_text.insert(tk.END, "Hover over image to see pixel hex data")
            self.clear_hex_highlight()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset view: {str(e)}")
    
    def search_pattern(self):
        try:
            pattern_hex = self.pattern_var.get().replace(" ", "").replace("0x", "")
            
            # Convert hex string to bytes
            pattern_bytes = bytes.fromhex(pattern_hex)
            
            # Read entire file for searching
            with open(self.image_path, 'rb') as f:
                file_data = f.read()
            
            matches = []
            start = 0
            while True:
                pos = file_data.find(pattern_bytes, start)
                if pos == -1:
                    break
                matches.append(pos)
                start = pos + 1
            
            if matches:
                result = f"Pattern '{self.pattern_var.get()}' found at {len(matches)} location(s):\n"
                for i, pos in enumerate(matches[:20]):  # Show first 20 matches
                    result += f"  {i+1}. Offset: {pos} (0x{pos:08X})\n"
                if len(matches) > 20:
                    result += f"  ... and {len(matches) - 20} more matches\n"
                
                # Jump to first match
                if matches:
                    self.offset_var.set(str(max(0, matches[0] - 64)))  # Show some context before
                    self.refresh_hex()
                    
                messagebox.showinfo("Pattern Search", result)
            else:
                messagebox.showinfo("Pattern Search", f"Pattern '{self.pattern_var.get()}' not found in file")
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid hex pattern: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")
    
    def get_image_properties(self):
        """Get Windows-style properties like right-click Properties"""
        properties_lines = []
        
        try:
            # File information (like Windows Properties)
            file_stat = os.stat(self.image_path)
            file_size = file_stat.st_size
            
            properties_lines.append("=" * 60)
            properties_lines.append(f"FILE PROPERTIES - {os.path.basename(self.image_path)}")
            properties_lines.append("=" * 60)
            
            properties_lines.append(f"Name: {os.path.basename(self.image_path)}")
            properties_lines.append(f"Type: Image file")
            properties_lines.append(f"Location: {os.path.dirname(self.image_path)}")
            properties_lines.append(f"Size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
            properties_lines.append(f"Size on disk: {file_size:,} bytes")
            
            # Timestamps
            try:
                created = datetime.datetime.fromtimestamp(file_stat.st_ctime)
                modified = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                accessed = datetime.datetime.fromtimestamp(file_stat.st_atime)
                
                properties_lines.append(f"Created: {created.strftime('%A, %B %d, %Y, %I:%M:%S %p')}")
                properties_lines.append(f"Modified: {modified.strftime('%A, %B %d, %Y, %I:%M:%S %p')}")
                properties_lines.append(f"Accessed: {accessed.strftime('%A, %B %d, %Y, %I:%M:%S %p')}")
            except (OSError, ValueError):
                properties_lines.append("Timestamps: Not available")
            
            properties_lines.append("")
            
            # Image details
            try:
                with Image.open(self.image_path) as img:
                    properties_lines.append("IMAGE DETAILS")
                    properties_lines.append("-" * 30)
                    properties_lines.append(f"Dimensions: {img.size[0]} x {img.size[1]} pixels")
                    properties_lines.append(f"Width: {img.size[0]} pixels")
                    properties_lines.append(f"Height: {img.size[1]} pixels")
                    properties_lines.append(f"Color depth: {img.mode}")
                    properties_lines.append(f"Format: {img.format or 'Unknown'}")
                    
                    if img.size[1] != 0:
                        properties_lines.append(f"Aspect ratio: {img.size[0]/img.size[1]:.3f}:1")
                    
                    # DPI information
                    dpi = img.info.get('dpi', (96, 96))
                    properties_lines.append(f"Horizontal resolution: {dpi[0]} dpi")
                    properties_lines.append(f"Vertical resolution: {dpi[1]} dpi")
                    
                    properties_lines.append("")
                    
                    # Additional image info
                    if img.info:
                        properties_lines.append("ADDITIONAL INFO")
                        properties_lines.append("-" * 30)
                        for key, value in list(img.info.items())[:10]:  # Limit output
                            if key not in ['dpi']:  # Skip already shown
                                properties_lines.append(f"{key}: {str(value)[:100]}")
                        properties_lines.append("")
                    
            except Exception as e:
                properties_lines.append("IMAGE DETAILS")
                properties_lines.append("-" * 30)
                properties_lines.append(f"Error reading image: {str(e)}")
                properties_lines.append("")
            
            # Security/Integrity
            try:
                with open(self.image_path, 'rb') as f:
                    file_content = f.read()
                    md5_hash = hashlib.md5(file_content).hexdigest()
                    sha1_hash = hashlib.sha1(file_content).hexdigest()
                    
                properties_lines.append("SECURITY & INTEGRITY")
                properties_lines.append("-" * 30)
                properties_lines.append(f"MD5: {md5_hash}")
                properties_lines.append(f"SHA-1: {sha1_hash}")
                properties_lines.append("")
                
            except Exception as e:
                properties_lines.append("SECURITY & INTEGRITY")
                properties_lines.append("-" * 30)
                properties_lines.append(f"Error calculating hashes: {str(e)}")
                properties_lines.append("")
            
            # Steganography hints
            properties_lines.append("STEGANOGRAPHY ANALYSIS HINTS")
            properties_lines.append("-" * 40)
            properties_lines.append("Things to check:")
            properties_lines.append("  • File size compared to similar images")
            properties_lines.append("  • Use hex editor to look for embedded files")
            properties_lines.append("  • Check for LSB patterns in image data")
            properties_lines.append("  • Look for unusual metadata")
            properties_lines.append("  • Compare with original if available")
            properties_lines.append("")
            properties_lines.append("Recommended tools:")
            properties_lines.append("  • StegSolve - Visual steganography analysis")
            properties_lines.append("  • Binwalk - Search for embedded files")
            properties_lines.append("  • Strings - Extract readable text")
            properties_lines.append("  • ExifTool - Detailed metadata analysis")
            
        except Exception as e:
            properties_lines = [
                "=" * 60,
                "ERROR READING PROPERTIES",
                "=" * 60,
                f"File: {self.image_path}",
                f"Error: {str(e)}",
                "",
                "Basic information:",
                f"File exists: {os.path.exists(self.image_path)}",
            ]
            
            try:
                file_stat = os.stat(self.image_path)
                properties_lines.append(f"File size: {file_stat.st_size:,} bytes")
            except:
                properties_lines.append("Could not get file size")
        
        return "\n".join(properties_lines)

class SteganographyComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("Steganography Image Comparison Tool")
        self.root.geometry("1400x900")
        
        # Variables
        self.base_directory = ""
        self.current_page = 0
        self.images_per_page = 1
        self.image_categories = ["android_icon", "full_color", "gray", "pokemon"]
        self.selected_category = tk.StringVar(value="android_icon")
        self.image_data = []
        self.total_pages = 0
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Directory selection
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(dir_frame, text="Base Directory:").grid(row=0, column=0, padx=(0, 5))
        self.dir_label = ttk.Label(dir_frame, text="No directory selected", foreground="gray")
        self.dir_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(row=0, column=2)
        
        dir_frame.columnconfigure(1, weight=1)
        
        # Category selection
        category_frame = ttk.Frame(main_frame)
        category_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(category_frame, text="Image Category:").grid(row=0, column=0, padx=(0, 5))
        category_combo = ttk.Combobox(category_frame, textvariable=self.selected_category, 
                                    values=self.image_categories, state="readonly", width=15)
        category_combo.grid(row=0, column=1, padx=(0, 10))
        category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        ttk.Button(category_frame, text="Load Images", command=self.load_images).grid(row=0, column=2)
        
        # Images display frame
        self.images_frame = ttk.Frame(main_frame)
        self.images_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(2, weight=1)
        
        # Pagination controls
        pagination_frame = ttk.Frame(main_frame)
        pagination_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        self.prev_button = ttk.Button(pagination_frame, text="← Previous", 
                                     command=self.previous_page, state="disabled")
        self.prev_button.grid(row=0, column=0, padx=(0, 5))
        
        self.page_label = ttk.Label(pagination_frame, text="Page 0 of 0")
        self.page_label.grid(row=0, column=1, padx=5)
        
        self.next_button = ttk.Button(pagination_frame, text="Next →", 
                                     command=self.next_page, state="disabled")
        self.next_button.grid(row=0, column=2, padx=(5, 0))
        
        # Instructions
        instructions_frame = ttk.Frame(main_frame)
        instructions_frame.grid(row=4, column=0, columnspan=2, pady=(0, 5))
        
        instructions = ttk.Label(instructions_frame, 
                               text="Click on any image to open analyzer. Use 'Hex Hover' checkbox or press 'H' key for pixel hex info!", 
                               font=('Arial', 9, 'italic'), foreground="blue")
        instructions.pack()
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Select a directory to start", 
                                     foreground="blue")
        self.status_label.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.base_directory = directory
            self.dir_label.config(text=directory, foreground="black")
            self.status_label.config(text="Directory selected. Click 'Load Images' to start.")
    
    def on_category_change(self, event=None):
        if self.base_directory:
            self.load_images()
    
    def load_images(self):
        if not self.base_directory:
            messagebox.showwarning("Warning", "Please select a directory first.")
            return
        
        category = self.selected_category.get()
        self.image_data = []
        
        try:
            # Define the image types and their paths
            image_types = [
                ("Cover", f"cover/{category}"),
                ("Stegano BPCS", f"stegano/BPCS/{category}"),
                ("Stegano LSB", f"stegano/LSB/{category}"),
                ("Stegano PVD", f"stegano/PVD/{category}"),
                ("Reveal Cover", f"cover-reveal/{category}"),
                ("Stegano Reveal BPCS", f"stegano-reveal/BPCS/{category}"),
                ("Stegano Reveal LSB", f"stegano-reveal/LSB/{category}"),
                ("Stegano Reveal PVD", f"stegano-reveal/PVD/{category}")
            ]
            
            # Get all image files from cover directory to establish the base list
            cover_path = os.path.join(self.base_directory, "cover", category)
            if not os.path.exists(cover_path):
                messagebox.showerror("Error", f"Directory not found: {cover_path}")
                return
            
            # Supported image extensions
            extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff', '*.gif']
            cover_files = []
            
            for ext in extensions:
                cover_files.extend(glob.glob(os.path.join(cover_path, ext)))
                cover_files.extend(glob.glob(os.path.join(cover_path, ext.upper())))
            
            if not cover_files:
                messagebox.showinfo("Info", f"No image files found in {cover_path}")
                return
            
            # Sort files by name (ascending)
            cover_files.sort(key=lambda x: os.path.basename(x).lower())
            
            # For each cover file, find corresponding images in other directories
            for cover_file in cover_files:
                filename = os.path.basename(cover_file)
                image_set = {
                    "filename": filename,
                    "images": {}
                }
                
                for img_type, rel_path in image_types:
                    full_path = os.path.join(self.base_directory, rel_path, filename)
                    if os.path.exists(full_path):
                        image_set["images"][img_type] = full_path
                    else:
                        image_set["images"][img_type] = None
                   
                
                # Only add if at least cover image exists
                if image_set["images"].get("Cover"):
                    self.image_data.append(image_set)
            
            self.total_pages = len(self.image_data)
            self.current_page = 0
            
            if self.total_pages > 0:
                self.update_display()
                self.update_pagination_controls()
                self.status_label.config(text=f"Loaded {self.total_pages} image sets for category: {category}")
            else:
                messagebox.showinfo("Info", "No matching image sets found.")
                self.status_label.config(text="No images found.")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading images: {str(e)}")
            self.status_label.config(text="Error loading images.")
    
    def open_image_viewer(self, image_path, image_type):
        if image_path and os.path.exists(image_path):
            ImageViewer(self.root, image_path, image_type)
        else:
            messagebox.showwarning("Warning", "Image file not found or not available.")
    
    def update_display(self):
        # Clear previous images
        for widget in self.images_frame.winfo_children():
            widget.destroy()
        
        if not self.image_data or self.current_page >= len(self.image_data):
            return
        
        current_set = self.image_data[self.current_page]
        
        # Create title with better styling
        title_label = ttk.Label(self.images_frame, text=f"Image Set: {current_set['filename']}", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        # Create grid for images (2 rows, up to 4 columns)
        image_types = [
            ("Cover", 0, 0),
            ("Stegano BPCS", 0, 1),
            ("Stegano LSB", 0, 2),
            ("Stegano PVD", 0, 3),
            ("Reveal Cover", 1, 0),
            ("Stegano Reveal BPCS", 1, 1),
            ("Stegano Reveal LSB", 1, 2),
            ("Stegano Reveal PVD", 1, 3),
        ]
        
        max_size = (300, 300)  # Increased size for better visibility
        
        for img_type, row, col in image_types:
            frame = ttk.Frame(self.images_frame, relief="solid", borderwidth=1)
            frame.grid(row=row+1, column=col, padx=10, pady=10, sticky=(tk.N, tk.S))
            
            # Type label with better styling
            type_label = ttk.Label(frame, text=img_type, font=('Arial', 12, 'bold'))
            type_label.pack(pady=(10, 8))
            
            # Image
            img_path = current_set["images"].get(img_type)
            if img_path and os.path.exists(img_path):
                try:
                    # Load and resize image
                    pil_image = Image.open(img_path)
                    pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # Create clickable label with image and padding
                    img_label = ttk.Label(frame, image=photo, cursor="hand2")
                    img_label.image = photo  # Keep a reference
                    img_label.pack(pady=(0, 8))
                    
                    # Make image clickable
                    img_label.bind("<Button-1>", lambda e, path=img_path, itype=img_type: self.open_image_viewer(path, itype))
                    
                    # Add image info with better formatting
                    original_img = Image.open(img_path)
                    file_size = os.path.getsize(img_path) / 1024  # KB
                    info_text = f"Size: {original_img.size[0]}x{original_img.size[1]}\nFile: {file_size:.1f} KB\nClick to analyze"
                    info_label = ttk.Label(frame, text=info_text, font=('Arial', 9), justify="center")
                    info_label.pack(pady=(0, 10))
                    
                except Exception as e:
                    # Error loading image
                    error_label = ttk.Label(frame, text="Error loading\nimage", 
                                          foreground="red", font=('Arial', 10), justify="center")
                    error_label.pack(pady=20)
            else:
                # Image not found
                not_found_label = ttk.Label(frame, text="Image not\nfound", 
                                          foreground="gray", font=('Arial', 10), justify="center")
                not_found_label.pack(pady=20)
    
    def update_pagination_controls(self):
        if self.total_pages <= 1:
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self.page_label.config(text=f"Page 1 of {max(1, self.total_pages)}")
        else:
            self.prev_button.config(state="normal" if self.current_page > 0 else "disabled")
            self.next_button.config(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
            self.page_label.config(text=f"Page {self.current_page + 1} of {self.total_pages}")
    
    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()
            self.update_pagination_controls()
    
    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_display()
            self.update_pagination_controls()

def main():
    root = tk.Tk()
    app = SteganographyComparator(root)
    root.mainloop()

if __name__ == "__main__":
    main()