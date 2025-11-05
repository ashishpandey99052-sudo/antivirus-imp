# sentinel_app.py
# V2 - New "Pro" Theme with 2-part layout and 5-second scan animation.
# This version only scans single files.

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
import os
import datetime
import time # For the new scan timer

# --- IMPORTANT: It uses the same engine ---
import backend

# #################################################################### #
# ##################     NEW THEME & LAYOUT     ###################### #
# #################################################################### #

# --- 1. NEW "PRO" COLOR PALETTE ---
COLOR_PALETTE = {
    "background": "#000000",     # Black
    "frame_bg": "#1C1C1C",       # Dark Charcoal (replaces black for frames)
    "frame_border": "#A0A0A0",   # <-- FIXED: Added missing key
    "text": "#F5E8C7",           # Beige
    "text_dark_accent": "#A0A0A0",# Grey
    "button": "#B2A4FF",         # Purple
    "button_hover": "#A7C7E7",   # Light Blue
    "drop_hover": "#2B2B2B",     # Lighter charcoal
    "accent_green": "#2ECC71",   # Bright Green
    "accent_red": "#E74C3C",     # Bright Red
    "accent_yellow": "#FFB26B",  # Orange (replaces yellow)
}

# --- 2. NEW APP NAME ---
APP_NAME = "Sentinel"

# --- 3. NEW LARGER FONT PALETTE ---
FONT_PALETTE = {
    "title": ("Arial", 36, "bold"),
    "h1": ("Arial", 28, "bold"),
    "h2": ("Arial", 24, "bold"),
    "body_bold": ("Arial", 18, "bold"),
    "body": ("Arial", 16, "normal"),
    "small": ("Arial", 14, "normal"),
}

# --- 4. OTHER SETTINGS ---
WINDOW_WIDTH = 900  # Wider for 2-column layout
WINDOW_HEIGHT = 600
TYPE_SPEED_MS = 25
MIN_SCAN_TIME_MS = 5000 # <-- 5-Second minimum scan animation

# #################################################################### #
# ##################     END OF CUSTOMIZATION     #################### #
# #################################################################### #


# This wrapper class is needed to combine CustomTkinter and TkinterDnD
class SentinelApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(bg=COLOR_PALETTE["background"])

        # --- State Variables ---
        self.scan_in_progress = False
        self.path_to_scan = None
        self.animation_dots = 0
        self.start_time = 0

        # --- 1. THE NEW 2-PART LAYOUT ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1) # Left Frame
        self.grid_columnconfigure(1, weight=1) # Right Frame

        # --- 2. BUILD LEFT FRAME (CONTROLS) ---
        self.left_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"],
                                       corner_radius=10, border_width=2,
                                       border_color=COLOR_PALETTE["frame_border"])
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(3, weight=1) # Make drop label expand
        
        # --- 3. BUILD RIGHT FRAME (RESULTS) ---
        self.right_frame = ctk.CTkFrame(self, fg_color=COLOR_PALETTE["frame_bg"],
                                        corner_radius=10, border_width=2,
                                        border_color=COLOR_PALETTE["frame_border"])
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(2, weight=1) # Make accordion expand

        # --- 4. POPULATE LEFT FRAME ---
        self._build_scan_controls()

        # --- 5. POPULATE RIGHT FRAME ---
        self._build_results_display()
        
        # --- 6. START ---
        self.right_frame.grid_remove() # Hide results frame initially
        
        # Bind DnD to the drop label
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_file_drop)
        self.drop_label.bind("<Enter>", self.on_drop_hover)
        self.drop_label.bind("<Leave>", self.on_drop_leave)

    # --- Page Building Functions ---
    def _build_scan_controls(self):
        # Title
        self.title_label = ctk.CTkLabel(self.left_frame, text=APP_NAME,
                                        font=FONT_PALETTE["title"],
                                        text_color=COLOR_PALETTE["text"])
        self.title_label.grid(row=0, column=0, pady=(20, 10))

        # Scan Path Label
        self.scan_path_label = ctk.CTkLabel(self.left_frame, text="Ready to scan...",
                                            font=FONT_PALETTE["small"],
                                            text_color=COLOR_PALETTE["text_dark_accent"])
        self.scan_path_label.grid(row=1, column=0, pady=(0, 20))

        # Drop Zone
        self.drop_label = ctk.CTkLabel(self.left_frame, text="Drag & Drop a File Here",
                                        fg_color=COLOR_PALETTE["background"],
                                        corner_radius=10, font=FONT_PALETTE["body_bold"],
                                        text_color=COLOR_PALETTE["text_dark_accent"])
        self.drop_label.grid(row=3, column=0, sticky="nsew", padx=20, pady=20)

        # File Scan Button (No folder button)
        self.browse_file_button = ctk.CTkButton(self.left_frame, text="Browse File",
                                           command=self.browse_file,
                                           fg_color=COLOR_PALETTE["button"],
                                           hover_color=COLOR_PALETTE["button_hover"],
                                           font=FONT_PALETTE["body_bold"],
                                           text_color="#000000",
                                           height=40)
        self.browse_file_button.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))

        # --- NEW ANIMATION WIDGET (Hidden by default) ---
        self.scanning_animation_label = ctk.CTkLabel(self.left_frame, text="SCANNING",
                                                     font=FONT_PALETTE["h1"],
                                                     text_color=COLOR_PALETTE["text"])

    def _build_results_display(self):
        # Title
        results_title = ctk.CTkLabel(self.right_frame, text="Scan Results",
                                     font=FONT_PALETTE["title"],
                                     text_color=COLOR_PALETTE["text"])
        results_title.grid(row=0, column=0, pady=(20, 20))

        # Status Card
        self.status_card = ctk.CTkFrame(self.right_frame, fg_color=COLOR_PALETTE["background"],
                                        corner_radius=10, border_width=0)
        self.status_card.grid(row=1, column=0, sticky="ew", padx=20)
        self.status_card.grid_columnconfigure(1, weight=1)
        self.status_icon = ctk.CTkLabel(self.status_card, text="", font=FONT_PALETTE["h1"])
        self.status_icon.grid(row=0, column=0, padx=(20, 10), pady=15)
        self.status_text = ctk.CTkLabel(self.status_card, text="", font=FONT_PALETTE["h2"])
        self.status_text.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        
        # Accordion Frame (Single File)
        self.accordion_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.accordion_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 20), padx=20)
        self.accordion_frame.grid_columnconfigure(0, weight=1)
        # Accordion Items...
        self.entropy_button = ctk.CTkButton(self.accordion_frame, text="[+] Entropy Analysis", fg_color=COLOR_PALETTE["background"], hover_color=COLOR_PALETTE["drop_hover"], anchor="w", font=FONT_PALETTE["body_bold"], command=lambda: self.toggle_accordion(self.entropy_content, self.entropy_button)); self.entropy_button.grid(row=0, column=0, sticky="ew")
        self.entropy_content = ctk.CTkFrame(self.accordion_frame, fg_color=COLOR_PALETTE["background"]); self.entropy_label = ctk.CTkLabel(self.entropy_content, text="", font=FONT_PALETTE["body"], anchor="w", justify="left"); self.entropy_label.pack(pady=10, padx=20, fill="x")
        self.imports_button = ctk.CTkButton(self.accordion_frame, text="[+] Import Analysis", fg_color=COLOR_PALETTE["background"], hover_color=COLOR_PALETTE["drop_hover"], anchor="w", font=FONT_PALETTE["body_bold"], command=lambda: self.toggle_accordion(self.imports_content, self.imports_button)); self.imports_button.grid(row=2, column=0, sticky="ew", pady=(5,0))
        self.imports_content = ctk.CTkFrame(self.accordion_frame, fg_color=COLOR_PALETTE["background"]); self.imports_label = ctk.CTkLabel(self.imports_content, text="", font=FONT_PALETTE["body"], anchor="w", justify="left"); self.imports_label.pack(pady=10, padx=20, fill="x")
        self.header_button = ctk.CTkButton(self.accordion_frame, text="[+] Header Analysis", fg_color=COLOR_PALETTE["background"], hover_color=COLOR_PALETTE["drop_hover"], anchor="w", font=FONT_PALETTE["body_bold"], command=lambda: self.toggle_accordion(self.header_content, self.header_button)); self.header_button.grid(row=4, column=0, sticky="ew", pady=(5,0))
        self.header_content = ctk.CTkFrame(self.accordion_frame, fg_color=COLOR_PALETTE["background"]); self.header_label = ctk.CTkLabel(self.header_content, text="", font=FONT_PALETTE["body"], anchor="w", justify="left"); self.header_label.pack(pady=10, padx=20, fill="x")

    # --- UI Logic ---
    def on_drop_hover(self, event): self.drop_label.configure(fg_color=COLOR_PALETTE["drop_hover"])
    def on_drop_leave(self, event): self.drop_label.configure(fg_color=COLOR_PALETTE["background"])
    def toggle_accordion(self, content_frame, button):
        if content_frame.winfo_viewable():
            content_frame.grid_remove()
            button.configure(text=button.cget("text").replace("[-]", "[+]"))
        else:
            content_frame.grid(row=int(button.grid_info()["row"]) + 1, column=0, sticky="ew", padx=10)
            button.configure(text=button.cget("text").replace("[+]", "[-]"))

    # --- NEW: Text-Based Animation ---
    def animate_scan_text(self):
        if not self.scan_in_progress:
            # Stop animation
            self.scanning_animation_label.grid_remove()
            # Restore controls
            self.drop_label.grid()
            self.browse_file_button.grid()
            return
        
        # Cycle the dots
        self.animation_dots = (self.animation_dots + 1) % 4
        dots = "." * self.animation_dots
        self.scanning_animation_label.configure(text=f"SCANNING{dots}")
        
        # Loop the animation
        self.after(400, self.animate_scan_text)

    # --- Scan Initiation ---
    def handle_file_drop(self, event):
        # This version only accepts files, not directories
        filepath = event.data.strip('{}')
        if os.path.isfile(filepath):
            self.start_scan(filepath)
        else:
            self.scan_path_label.configure(text="Error: Please drop a single file, not a folder.")
            
    def browse_file(self):
        filepath = filedialog.askopenfilename(title="Select File", filetypes=(("Executables", "*.exe;*.dll"), ("All files", "*.*")))
        if filepath: self.start_scan(filepath)
        
    def browse_folder(self):
        # This button is removed, but we keep the function from erroring
        pass 

    def start_scan(self, path):
        if self.scan_in_progress: return
        
        # --- NEW ANIMATION LOGIC ---
        self.scan_in_progress = True
        self.start_time = time.time() # Record start time
        self.path_to_scan = path
        
        # 1. Hide results, reset card
        self.right_frame.grid_remove()
        self.status_card.configure(border_width=0)
        self.scan_path_label.configure(text=f"Scan Target: {os.path.basename(path)}")
        
        # 2. Hide controls
        self.drop_label.grid_remove()
        self.browse_file_button.grid_remove()
        
        # 3. Show animation
        self.scanning_animation_label.grid(row=3, column=0, sticky="nsew", padx=20, pady=20)
        self.animate_scan_text() # Start animation loop
        
        # 4. Run the scan in the background
        # We use 'after' to let the UI update *before* the scan blocks the main thread
        self.after(50, self.run_the_actual_scan)

    # --- Scan Execution ---
    def run_the_actual_scan(self):
        # This is a file-only scan
        results = backend.run_scan(self.path_to_scan)
        
        # --- NEW: Minimum Scan Time Logic ---
        elapsed_time_ms = (time.time() - self.start_time) * 1000
        wait_time_ms = max(0, MIN_SCAN_TIME_MS - elapsed_time_ms)
        
        # Schedule the results to display *after* the min time has passed
        self.after(int(wait_time_ms), self._display_file_results, results)

    # --- Display File Results (Accordion) ---
    def _display_file_results(self, results):
        self.scan_in_progress = False # This will stop the animation loop
        
        result_color = COLOR_PALETTE["frame_border"]
        if "error" in results:
            result_color = COLOR_PALETTE["accent_red"]
            self.status_icon.configure(text="X", text_color=result_color); self.status_text.configure(text="SCAN FAILED", text_color=result_color)
            self.entropy_button.configure(text="[+] Entropy (Error)"); self.entropy_label.configure(text=results["error"])
            self.imports_button.configure(text="[+] Imports (Error)"); self.imports_label.configure(text=results["error"])
            self.header_button.configure(text="[+] Header (Error)"); self.header_label.configure(text=results["error"])
        else:
            risk = results['risk_score']
            if risk == 0: result_color = COLOR_PALETTE["accent_green"]; self.status_icon.configure(text="✓", text_color=result_color); self.status_text.configure(text="FILE CLEAN", text_color=result_color)
            elif risk <= 2: result_color = COLOR_PALETTE["accent_yellow"]; self.status_icon.configure(text="!", text_color=result_color); self.status_text.configure(text="SUSPICIOUS FILE", text_color=result_color)
            else: result_color = COLOR_PALETTE["accent_red"]; self.status_icon.configure(text="X", text_color=result_color); self.status_text.configure(text="HIGH DANGER", text_color=result_color)

            entropy_status, entropy_data = results['entropy']; self.entropy_label.configure(text=f"   {entropy_data}"); self.entropy_button.configure(text=f"[+] Entropy ({entropy_status})", text_color=COLOR_PALETTE["accent_red"] if entropy_status == "HIGH" else COLOR_PALETTE["text"])
            import_status, import_data = results['imports']; data_str = "\n   • ".join(import_data) if isinstance(import_data, list) else f"   {import_data}"; self.imports_label.configure(text=data_str); self.imports_button.configure(text=f"[+] Imports ({import_status})", text_color=COLOR_PALETTE["accent_red"] if import_status == "SUSPICIOUS" else COLOR_PALETTE["text"])
            header_status, header_data = results['header']; data_str = "\n   • ".join(header_data) if isinstance(header_data, list) else f"   {header_data}"; self.header_label.configure(text=data_str); self.header_button.configure(text=f"[+] Header ({header_status})", text_color=COLOR_PALETTE["accent_red"] if header_status == "SUSPICIOUS" else COLOR_PALETTE["text"])
            for btn, content in [(self.entropy_button, self.entropy_content), (self.imports_button, self.imports_content), (self.header_button, self.header_content)]:
                 btn.configure(text=btn.cget("text").replace("[-]", "[+]")); content.grid_remove()

        self.status_card.configure(border_color=result_color, border_width=2)
        
        # Show the results frame
        self.right_frame.grid()
        self.update_idletasks()

# --- Entry Point ---
if __name__ == "__main__":
    app = SentinelApp()
    app.mainloop()