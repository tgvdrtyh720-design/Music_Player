import os
import pygame
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageFilter, ImageDraw, ImageTk
import customtkinter as ctk
from mutagen.mp3 import MP3
from mutagen import File
from mutagen.id3 import ID3, APIC
from pathlib import Path
import hashlib
import math
import json
from datetime import datetime
import random

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ModernMusicPlayer:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("✨ AURA Music Player ✨")
        self.window.geometry("1200x750")
        self.window.minsize(1000, 600)
        self.window.configure(fg_color="#1a1a2e")

        pygame.mixer.init()

        self.current_track = None
        self.current_track_path = None
        self.is_playing = False
        self.is_paused = False
        self.current_time = 0
        self.total_length = 0
        self.update_slider_flag = True
        self.is_seeking = False
        self.playlist = []
        self.current_index = -1
        self.track_covers = {}
        self.repeat_mode = "none"
        self.shuffle_mode = False
        self.equalizer_enabled = False
        self.visualization_enabled = True
        self.favorites = []
        self.play_history = []
        self.last_played = None
        self.volume_popup = None
        self.visualization_animation_running = True
        self.glow_animation_id = None
        
        self.music_dir = "music"
        self.cache_dir = "cover_cache"
        self.data_dir = "player_data"
        os.makedirs(self.music_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.favorites_file = os.path.join(self.data_dir, "favorites.json")
        self.history_file = os.path.join(self.data_dir, "history.json")
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        
        self.colors = {
            'primary': '#6C63FF',
            'secondary': '#FF6584',
            'accent': '#FFD166',
            'dark': '#2A2B2E',
            'darker': '#1E1F22',
            'light': '#F8F9FA',
            'gradient_start': '#667eea',
            'gradient_end': '#764ba2',
            'success': '#00C851',
            'warning': '#FF8800',
            'info': '#33b5e5'
        }

        self.load_settings()
        self.load_favorites()
        self.load_history()
        self.create_widgets()
        self.scan_music_folder()
        self.update_ui()
        self.start_visualization()
        
        self.window.bind('<space>', self.space_pressed)

        self.window.mainloop()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.repeat_mode = settings.get('repeat_mode', "none")
                    self.shuffle_mode = settings.get('shuffle_mode', False)
                    self.equalizer_enabled = settings.get('equalizer_enabled', False)
                    self.visualization_enabled = settings.get('visualization_enabled', True)
            except:
                pass

    def save_settings(self):
        settings = {
            'repeat_mode': self.repeat_mode,
            'shuffle_mode': self.shuffle_mode,
            'equalizer_enabled': self.equalizer_enabled,
            'visualization_enabled': self.visualization_enabled
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)

    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r') as f:
                    self.favorites = json.load(f)
            except:
                self.favorites = []
        else:
            self.favorites = []

    def save_favorites(self):
        with open(self.favorites_file, 'w') as f:
            json.dump(self.favorites, f)

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.play_history = json.load(f)
            except:
                self.play_history = []
        else:
            self.play_history = []

    def save_history(self):
        if len(self.play_history) > 100:
            self.play_history = self.play_history[-100:]
        with open(self.history_file, 'w') as f:
            json.dump(self.play_history, f)

    def add_to_history(self, track_path, title, artist):
        history_entry = {
            'path': track_path,
            'title': title,
            'artist': artist,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.play_history.append(history_entry)
        self.save_history()
        self.update_history_panel()

    def scan_music_folder(self):
        if os.path.exists(self.music_dir):
            supported_formats = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
            music_files = []
            
            for file in os.listdir(self.music_dir):
                if file.lower().endswith(supported_formats):
                    file_path = os.path.join(self.music_dir, file)
                    music_files.append(file_path)
            
            if music_files:
                for file_path in music_files:
                    if file_path not in self.playlist:
                        title, artist = self.get_metadata(file_path)
                        self.playlist.append(file_path)
                        self.add_track_to_playlist_ui(file_path, len(self.playlist) - 1, title, artist)
                
                if len(self.playlist) > 0 and self.current_index == -1:
                    self.current_index = 0
                    self.load_track(self.current_index)
                
                self.status_bar.configure(text=f"✅ Loaded {len(music_files)} tracks from music folder")
            else:
                self.status_bar.configure(text="📁 No music found in 'music' folder")

    def space_pressed(self, event):
        if self.current_track_path:
            self.play_pause()
        elif self.playlist:
            self.current_index = 0
            self.load_track(0)
            self.play()

    def create_widgets(self):
        self.main_container = ctk.CTkFrame(self.window, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.create_navbar()

        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=(20, 0))

        self.create_playlist_panel()
        self.create_player_panel()
        self.create_side_panel()

    def create_navbar(self):
        self.navbar = ctk.CTkFrame(self.main_container, height=60, corner_radius=15, 
                                   fg_color=("#1E1F22", "#1E1F22"))
        self.navbar.pack(fill="x", pady=(0, 20))
        self.navbar.pack_propagate(False)
        
        self.logo_label = ctk.CTkLabel(self.navbar, text="✨ AURA", 
                                       font=ctk.CTkFont(size=24, weight="bold"),
                                       text_color=("#6C63FF", "#6C63FF"))
        self.logo_label.pack(side="left", padx=20)
        
        self.nav_buttons_frame = ctk.CTkFrame(self.navbar, fg_color="transparent")
        self.nav_buttons_frame.pack(side="right", padx=20)
        
        self.shuffle_btn = ctk.CTkButton(self.nav_buttons_frame, text="🔀", width=40, height=35,
                                        font=ctk.CTkFont(size=18), command=self.toggle_shuffle,
                                        fg_color=self.colors['primary'] if self.shuffle_mode else "transparent",
                                        hover_color=self.colors['primary'])
        self.shuffle_btn.pack(side="left", padx=5)
        
        self.repeat_btn = ctk.CTkButton(self.nav_buttons_frame, text="🔁", width=40, height=35,
                                       font=ctk.CTkFont(size=18), command=self.toggle_repeat,
                                       fg_color=self.colors['primary'] if self.repeat_mode != "none" else "transparent",
                                       hover_color=self.colors['primary'])
        self.repeat_btn.pack(side="left", padx=5)
        
        self.equalizer_btn = ctk.CTkButton(self.nav_buttons_frame, text="🎚️", width=40, height=35,
                                          font=ctk.CTkFont(size=18), command=self.toggle_equalizer,
                                          fg_color="transparent", hover_color=self.colors['primary'])
        self.equalizer_btn.pack(side="left", padx=5)

    def create_playlist_panel(self):
        self.playlist_panel = ctk.CTkFrame(self.content_frame, width=320, corner_radius=20,
                                          fg_color=("#2A2B2E", "#2A2B2E"))
        self.playlist_panel.pack(side="left", fill="y", padx=(0, 15))
        self.playlist_panel.pack_propagate(False)

        self.playlist_header = ctk.CTkFrame(self.playlist_panel, fg_color="transparent")
        self.playlist_header.pack(fill="x", padx=20, pady=(20, 15))
        
        self.playlist_title = ctk.CTkLabel(self.playlist_header, text="🎵 ПЛЕЙЛИСТ", 
                                          font=ctk.CTkFont(size=16, weight="bold"))
        self.playlist_title.pack(side="left")
        
        self.track_count_label = ctk.CTkLabel(self.playlist_header, text="0 треков",
                                             font=ctk.CTkFont(size=12), text_color="gray")
        self.track_count_label.pack(side="right")

        self.playlist_controls = ctk.CTkFrame(self.playlist_panel, fg_color="transparent")
        self.playlist_controls.pack(fill="x", padx=20, pady=(0, 15))
        
        self.add_tracks_btn = ctk.CTkButton(self.playlist_controls, text="➕ Добавить", 
                                           command=self.add_tracks, height=35,
                                           fg_color=self.colors['primary'],
                                           hover_color="#5a52d6")
        self.add_tracks_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.refresh_btn = ctk.CTkButton(self.playlist_controls, text="🔄 Обновить",
                                        command=self.scan_music_folder, height=35,
                                        fg_color="#FFD166", hover_color="#e5c000",
                                        text_color="#1a1a2e")
        self.refresh_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        self.playlist_frame = ctk.CTkScrollableFrame(self.playlist_panel, fg_color="transparent")
        self.playlist_frame.pack(fill="both", expand=True, padx=15, pady=(0, 20))
        
        self.playlist_widgets = []

    def create_player_panel(self):
        self.player_panel = ctk.CTkFrame(self.content_frame, corner_radius=25,
                                        fg_color=("#1E1F22", "#1E1F22"))
        self.player_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        self.cover_container = ctk.CTkFrame(self.player_panel, fg_color="transparent")
        self.cover_container.pack(fill="both", expand=True, pady=(20, 10))
        
        self.cover_frame = ctk.CTkFrame(self.cover_container, width=400, height=400, 
                                       corner_radius=25, fg_color="transparent")
        self.cover_frame.pack(pady=10)
        self.cover_frame.pack_propagate(False)
        
        self.cover_label = ctk.CTkLabel(self.cover_frame, text="🎵", 
                                       font=ctk.CTkFont(size=100),
                                       width=400, height=400,
                                       fg_color="#2A2B2E",
                                       corner_radius=20)
        self.cover_label.pack()
        self.cover_label.bind("<Button-3>", lambda e: self.change_track_cover())
        
        self.visualization_frame = ctk.CTkFrame(self.player_panel, height=80, corner_radius=10,
                                               fg_color=self.colors['darker'])
        self.visualization_frame.pack(fill="x", padx=40, pady=(5, 10))
        self.visualization_frame.pack_propagate(False)
        
        self.visualization_canvas = tk.Canvas(self.visualization_frame, height=60, 
                                              bg=self.colors['darker'], highlightthickness=0)
        self.visualization_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.track_info_frame = ctk.CTkFrame(self.player_panel, fg_color="transparent")
        self.track_info_frame.pack(fill="x", padx=40, pady=(0, 15))
        
        self.song_title = ctk.CTkLabel(self.track_info_frame, text="No track selected", 
                                       font=ctk.CTkFont(size=22, weight="bold"),
                                       text_color="white")
        self.song_title.pack()
        
        self.song_artist = ctk.CTkLabel(self.track_info_frame, text="---",
                                        font=ctk.CTkFont(size=13),
                                        text_color="gray")
        self.song_artist.pack()

        self.progress_frame = ctk.CTkFrame(self.player_panel, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=40, pady=5)
        
        self.current_time_label = ctk.CTkLabel(self.progress_frame, text="0:00", width=45,
                                              font=ctk.CTkFont(size=12))
        self.current_time_label.pack(side="left")
        
        self.progress_slider = ctk.CTkSlider(self.progress_frame, from_=0, to=100,
                                             command=self.on_slider_drag,
                                             button_color=self.colors['primary'],
                                             button_hover_color=self.colors['secondary'],
                                             progress_color=self.colors['primary'])
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=15)
        
        self.progress_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        
        self.total_time_label = ctk.CTkLabel(self.progress_frame, text="0:00", width=45,
                                            font=ctk.CTkFont(size=12))
        self.total_time_label.pack(side="right")

        self.controls_frame = ctk.CTkFrame(self.player_panel, fg_color="transparent")
        self.controls_frame.pack(pady=15)
        
        btn_style = {
            'width': 60,
            'height': 60,
            'font': ctk.CTkFont(size=26),
            'corner_radius': 30
        }
        
        self.prev_btn = ctk.CTkButton(self.controls_frame, text="⏮", command=self.previous_track,
                                     **btn_style, fg_color="transparent", hover_color=self.colors['primary'])
        self.prev_btn.pack(side="left", padx=8)
        
        self.play_pause_btn = ctk.CTkButton(self.controls_frame, text="▶", command=self.play_pause,
                                           **btn_style, fg_color=self.colors['primary'],
                                           hover_color="#5a52d6")
        self.play_pause_btn.pack(side="left", padx=8)
        
        self.stop_btn = ctk.CTkButton(self.controls_frame, text="⏹", command=self.stop,
                                     **btn_style, fg_color="transparent", hover_color=self.colors['secondary'])
        self.stop_btn.pack(side="left", padx=8)
        
        self.next_btn = ctk.CTkButton(self.controls_frame, text="⏭", command=self.next_track,
                                     **btn_style, fg_color="transparent", hover_color=self.colors['primary'])
        self.next_btn.pack(side="left", padx=8)

        self.fav_btn = ctk.CTkButton(self.controls_frame, text="❤️", width=45, height=45,
                                    font=ctk.CTkFont(size=22), command=self.toggle_favorite,
                                    fg_color="transparent", hover_color="#FF6584",
                                    corner_radius=23)
        self.fav_btn.pack(side="left", padx=8)

        self.volume_frame = ctk.CTkFrame(self.player_panel, fg_color="transparent")
        self.volume_frame.pack(fill="x", padx=40, pady=15)
        
        self.volume_button = ctk.CTkButton(self.volume_frame, text="🔊", width=40, height=30,
                                          font=ctk.CTkFont(size=16), command=self.show_volume_popup,
                                          fg_color="transparent", hover_color=self.colors['primary'])
        self.volume_button.pack(side="left")
        
        self.volume_slider = ctk.CTkSlider(self.volume_frame, from_=0, to=100,
                                          command=self.change_volume,
                                          button_color=self.colors['primary'],
                                          progress_color=self.colors['primary'])
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=15)
        self.volume_slider.set(70)
        pygame.mixer.music.set_volume(0.7)
        
        self.volume_value_label = ctk.CTkLabel(self.volume_frame, text="70%", width=40,
                                              font=ctk.CTkFont(size=12))
        self.volume_value_label.pack(side="right")

        self.status_bar = ctk.CTkLabel(self.player_panel, text="✨ Ready to play music",
                                       font=ctk.CTkFont(size=11, slant="italic"),
                                       text_color="gray")
        self.status_bar.pack(side="bottom", pady=10)

    def update_status(self, text, status_type="info"):
        colors = {
            "playing": "#00C851",
            "paused": "#FF8800", 
            "error": "#FF4444",
            "info": "#6C63FF",
            "success": "#00C851"
        }
        color = colors.get(status_type, colors["info"])
        self.status_bar.configure(text=text, text_color=color)
        
        def reset_color():
            self.status_bar.configure(text_color="gray")
        
        self.window.after(2000, reset_color)

    def on_slider_drag(self, value):
        self.is_seeking = True
        if self.total_length > 0:
            seek_time = (float(value) / 100) * self.total_length
            self.current_time_label.configure(text=self.format_time(seek_time))

    def on_slider_release(self, event):
        if self.current_track_path and self.total_length > 0:
            value = self.progress_slider.get()
            seek_time = (float(value) / 100) * self.total_length
            pygame.mixer.music.play(start=seek_time)
            self.current_time = seek_time
            self.is_playing = True
            self.is_paused = False
            self.play_pause_btn.configure(text="⏸")
        self.is_seeking = False

    def show_volume_popup(self):
        if self.volume_popup and self.volume_popup.winfo_exists():
            self.volume_popup.destroy()
        
        self.volume_popup = ctk.CTkToplevel(self.window)
        self.volume_popup.title("")
        self.volume_popup.geometry("50x200")
        self.volume_popup.resizable(False, False)
        self.volume_popup.attributes('-topmost', True)
        self.volume_popup.overrideredirect(True)
        
        x = self.volume_button.winfo_rootx() + 15
        y = self.volume_button.winfo_rooty() - 180
        self.volume_popup.geometry(f"50x180+{x}+{y}")
        
        volume_slider_vertical = ctk.CTkSlider(self.volume_popup, from_=0, to=100,
                                               command=self.change_volume,
                                               orientation="vertical",
                                               button_color=self.colors['primary'],
                                               progress_color=self.colors['primary'])
        volume_slider_vertical.pack(expand=True, fill="y", padx=10, pady=20)
        volume_slider_vertical.set(self.volume_slider.get())
        
        def on_focus_out(event):
            if self.volume_popup:
                self.volume_popup.destroy()
        
        self.volume_popup.bind("<FocusOut>", on_focus_out)

    def create_side_panel(self):
        self.side_panel = ctk.CTkFrame(self.content_frame, width=280, corner_radius=20,
                                      fg_color=("#2A2B2E", "#2A2B2E"))
        self.side_panel.pack(side="right", fill="y")
        self.side_panel.pack_propagate(False)
        
        self.accordion_frame = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        self.accordion_frame.pack(fill="both", expand=True, padx=15, pady=20)
        
        self.favorites_header = ctk.CTkButton(self.accordion_frame, text="❤️ ИЗБРАННОЕ", 
                                             command=self.toggle_favorites_section,
                                             font=ctk.CTkFont(size=14, weight="bold"),
                                             fg_color=self.colors['primary'],
                                             hover_color="#5a52d6",
                                             height=40)
        self.favorites_header.pack(fill="x", pady=(0, 2))
        
        self.favorites_content = ctk.CTkFrame(self.accordion_frame, fg_color="transparent")
        self.favorites_content.pack(fill="both", expand=True, pady=(0, 5))
        self.favorites_content.pack_propagate(False)
        self.favorites_content.configure(height=0)
        
        self.favorites_scrollable = ctk.CTkScrollableFrame(self.favorites_content, fg_color="transparent", height=150)
        self.favorites_scrollable.pack(fill="both", expand=True)
        self.favorites_widgets = []
        
        self.history_header = ctk.CTkButton(self.accordion_frame, text="📜 ИСТОРИЯ", 
                                           command=self.toggle_history_section,
                                           font=ctk.CTkFont(size=14, weight="bold"),
                                           fg_color="transparent",
                                           hover_color=self.colors['primary'],
                                           height=40)
        self.history_header.pack(fill="x", pady=(0, 2))
        
        self.history_content = ctk.CTkFrame(self.accordion_frame, fg_color="transparent")
        self.history_content.pack(fill="both", expand=True, pady=(0, 5))
        self.history_content.pack_propagate(False)
        self.history_content.configure(height=0)
        
        self.history_scrollable = ctk.CTkScrollableFrame(self.history_content, fg_color="transparent", height=150)
        self.history_scrollable.pack(fill="both", expand=True)
        self.history_widgets = []
        
        self.stats_header = ctk.CTkButton(self.accordion_frame, text="📊 СТАТИСТИКА", 
                                         command=self.toggle_stats_section,
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         fg_color="transparent",
                                         hover_color=self.colors['primary'],
                                         height=40)
        self.stats_header.pack(fill="x", pady=(0, 2))
        
        self.stats_content = ctk.CTkFrame(self.accordion_frame, fg_color="transparent")
        self.stats_content.pack(fill="both", expand=True)
        self.stats_content.pack_propagate(False)
        self.stats_content.configure(height=0)
        
        self.create_stats_panel()
        self.toggle_favorites_section()

    def toggle_favorites_section(self):
        current_height = self.favorites_content.winfo_height()
        if current_height > 10:
            self.favorites_content.configure(height=0)
            self.favorites_header.configure(fg_color="transparent")
        else:
            self.favorites_content.configure(height=200)
            self.favorites_header.configure(fg_color=self.colors['primary'])
            self.history_content.configure(height=0)
            self.stats_content.configure(height=0)
            self.history_header.configure(fg_color="transparent")
            self.stats_header.configure(fg_color="transparent")
        
        self.update_favorites_panel()

    def toggle_history_section(self):
        current_height = self.history_content.winfo_height()
        if current_height > 10:
            self.history_content.configure(height=0)
            self.history_header.configure(fg_color="transparent")
        else:
            self.history_content.configure(height=200)
            self.history_header.configure(fg_color=self.colors['primary'])
            self.favorites_content.configure(height=0)
            self.stats_content.configure(height=0)
            self.favorites_header.configure(fg_color="transparent")
            self.stats_header.configure(fg_color="transparent")
        
        self.update_history_panel()

    def toggle_stats_section(self):
        current_height = self.stats_content.winfo_height()
        if current_height > 10:
            self.stats_content.configure(height=0)
            self.stats_header.configure(fg_color="transparent")
        else:
            self.stats_content.configure(height=200)
            self.stats_header.configure(fg_color=self.colors['primary'])
            self.favorites_content.configure(height=0)
            self.history_content.configure(height=0)
            self.favorites_header.configure(fg_color="transparent")
            self.history_header.configure(fg_color="transparent")
        
        self.update_stats()

    def create_stats_panel(self):
        stats_frame = ctk.CTkFrame(self.stats_content, fg_color="transparent")
        stats_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.total_tracks_label = ctk.CTkLabel(stats_frame, text="🎵 Всего треков: 0",
                                              font=ctk.CTkFont(size=13))
        self.total_tracks_label.pack(pady=8)
        
        self.total_played_label = ctk.CTkLabel(stats_frame, text="🎧 Прослушано: 0",
                                              font=ctk.CTkFont(size=13))
        self.total_played_label.pack(pady=8)
        
        self.favorites_count_label = ctk.CTkLabel(stats_frame, text="❤️ В избранном: 0",
                                                font=ctk.CTkFont(size=13))
        self.favorites_count_label.pack(pady=8)

    def update_stats(self):
        self.total_tracks_label.configure(text=f"🎵 Всего треков: {len(self.playlist)}")
        self.favorites_count_label.configure(text=f"❤️ В избранном: {len(self.favorites)}")
        self.total_played_label.configure(text=f"🎧 Прослушано: {len(self.play_history)}")

    def update_history_panel(self):
        for widget in self.history_widgets:
            widget.destroy()
        self.history_widgets.clear()
        
        for entry in reversed(self.play_history[-15:]):
            history_item = ctk.CTkFrame(self.history_scrollable, corner_radius=8)
            history_item.pack(fill="x", pady=2)
            
            title_label = ctk.CTkLabel(history_item, text=entry['title'][:25] + ("..." if len(entry['title']) > 25 else ""),
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       anchor="w")
            title_label.pack(anchor="w", padx=10, pady=(5, 0))
            
            artist_label = ctk.CTkLabel(history_item, text=entry['artist'][:20],
                                       font=ctk.CTkFont(size=10), text_color="gray")
            artist_label.pack(anchor="w", padx=10, pady=(0, 5))
            
            self.history_widgets.append(history_item)

    def update_favorites_panel(self):
        for widget in self.favorites_widgets:
            widget.destroy()
        self.favorites_widgets.clear()
        
        for fav_path in self.favorites:
            if fav_path in self.playlist:
                index = self.playlist.index(fav_path)
                title, artist = self.get_metadata(fav_path)
                
                fav_item = ctk.CTkFrame(self.favorites_scrollable, corner_radius=8)
                fav_item.pack(fill="x", pady=2)
                
                title_label = ctk.CTkLabel(fav_item, text=title[:25] + ("..." if len(title) > 25 else ""),
                                          font=ctk.CTkFont(size=11, weight="bold"),
                                          anchor="w")
                title_label.pack(anchor="w", padx=10, pady=(5, 0))
                
                artist_label = ctk.CTkLabel(fav_item, text=artist[:20],
                                           font=ctk.CTkFont(size=10), text_color="gray")
                artist_label.pack(anchor="w", padx=10, pady=(0, 5))
                
                play_btn = ctk.CTkButton(fav_item, text="▶", width=25, height=25,
                                        font=ctk.CTkFont(size=12),
                                        command=lambda i=index: self.play_from_playlist(i))
                play_btn.pack(side="right", padx=10)
                
                self.favorites_widgets.append(fav_item)
        
        self.update_stats()

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        self.shuffle_btn.configure(fg_color=self.colors['primary'] if self.shuffle_mode else "transparent")
        self.save_settings()
        self.update_status("Shuffle mode " + ("ON" if self.shuffle_mode else "OFF"), "info")

    def toggle_repeat(self):
        if self.repeat_mode == "none":
            self.repeat_mode = "one"
            self.repeat_btn.configure(text="🔂", fg_color=self.colors['primary'])
            self.update_status("Repeat: One track", "info")
        elif self.repeat_mode == "one":
            self.repeat_mode = "all"
            self.repeat_btn.configure(text="🔁", fg_color=self.colors['primary'])
            self.update_status("Repeat: All tracks", "info")
        else:
            self.repeat_mode = "none"
            self.repeat_btn.configure(text="🔁", fg_color="transparent")
            self.update_status("Repeat: Off", "info")
        
        self.save_settings()

    def toggle_favorite(self):
        if self.current_track_path:
            if self.current_track_path in self.favorites:
                self.favorites.remove(self.current_track_path)
                self.fav_btn.configure(fg_color="transparent")
                self.update_status("❌ Removed from favorites", "error")
            else:
                self.favorites.append(self.current_track_path)
                self.fav_btn.configure(fg_color="#FF6584")
                self.update_status("❤️ Added to favorites", "success")
            
            self.save_favorites()
            self.update_favorites_panel()

    def toggle_equalizer(self):
        self.equalizer_enabled = not self.equalizer_enabled
        self.equalizer_btn.configure(fg_color=self.colors['primary'] if self.equalizer_enabled else "transparent")
        self.save_settings()
        
        if self.equalizer_enabled:
            self.update_status("🎚️ Equalizer enabled", "success")
        else:
            self.update_status("🎚️ Equalizer disabled", "info")

    def add_track_to_playlist_ui(self, track_path, index, title, artist):
        track_frame = ctk.CTkFrame(self.playlist_frame, corner_radius=10, height=70)
        track_frame.pack(fill="x", pady=3)
        track_frame.pack_propagate(False)
        
        track_frame.grid_columnconfigure(0, weight=1)
        track_frame.grid_columnconfigure(1, weight=0)
        track_frame.grid_columnconfigure(2, weight=0)
        track_frame.grid_rowconfigure(0, weight=1)
        
        info_frame = ctk.CTkFrame(track_frame, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=(12, 5), pady=8)
        info_frame.grid_propagate(False)
        
        display_title = title[:30] + "..." if len(title) > 30 else title
        display_artist = artist[:25] + "..." if len(artist) > 25 else artist
        
        title_label = ctk.CTkLabel(info_frame, text=display_title,
                                  font=ctk.CTkFont(size=13, weight="bold"),
                                  anchor="w")
        title_label.pack(anchor="w")
        
        artist_label = ctk.CTkLabel(info_frame, text=display_artist,
                                   font=ctk.CTkFont(size=11),
                                   text_color="gray", anchor="w")
        artist_label.pack(anchor="w")
        
        duration_label = ctk.CTkLabel(track_frame, text="---", font=ctk.CTkFont(size=11),
                                     text_color="gray", width=45)
        duration_label.grid(row=0, column=1, sticky="e", padx=5)
        
        button_frame = ctk.CTkFrame(track_frame, fg_color="transparent", width=75)
        button_frame.grid(row=0, column=2, sticky="e", padx=(0, 10))
        button_frame.grid_propagate(False)
        
        fav_icon = "❤️" if track_path in self.favorites else "🤍"
        fav_btn = ctk.CTkButton(button_frame, text=fav_icon, width=32, height=30,
                               font=ctk.CTkFont(size=14), fg_color="transparent",
                               hover_color="#FF6584", 
                               command=lambda p=track_path: self.toggle_favorite_from_list(p))
        fav_btn.pack(side="left", padx=2)
        
        remove_btn = ctk.CTkButton(button_frame, text="×", width=32, height=30,
                                  font=ctk.CTkFont(size=18), fg_color="transparent",
                                  hover_color="#FF6584", command=lambda: self.remove_track(index))
        remove_btn.pack(side="left", padx=2)
        
        track_frame.bind("<Button-1>", lambda e, i=index: self.play_from_playlist(i))
        track_frame.bind("<Button-3>", lambda e, i=index: self.show_context_menu(e, i))
        
        for widget in [info_frame, title_label, artist_label]:
            widget.bind("<Button-1>", lambda e, i=index: self.play_from_playlist(i))
        
        self.playlist_widgets.append({
            'frame': track_frame,
            'title': title_label,
            'artist': artist_label,
            'duration': duration_label,
            'remove_btn': remove_btn,
            'fav_btn': fav_btn,
            'index': index,
            'path': track_path
        })
        
        threading.Thread(target=self.update_track_duration, args=(index, track_path), daemon=True).start()
        self.update_track_count()
        self.update_stats()

    def toggle_favorite_from_list(self, track_path):
        if track_path in self.favorites:
            self.favorites.remove(track_path)
        else:
            self.favorites.append(track_path)
        
        self.save_favorites()
        self.update_favorites_panel()
        
        for widget in self.playlist_widgets:
            if widget['path'] == track_path:
                fav_icon = "❤️" if track_path in self.favorites else "🤍"
                widget['fav_btn'].configure(text=fav_icon)
                break

    def update_track_duration(self, index, track_path):
        try:
            audio = MP3(track_path)
            duration = self.format_time(audio.info.length)
            self.window.after(0, lambda: self._update_duration_label(index, duration))
        except:
            pass
    
    def _update_duration_label(self, index, duration):
        if index < len(self.playlist_widgets):
            self.playlist_widgets[index]['duration'].configure(text=duration)

    def update_track_count(self):
        self.track_count_label.configure(text=f"{len(self.playlist)} треков")

    def play_from_playlist(self, index):
        self.current_index = index
        self.load_track(self.current_index)
        self.play()
        self.highlight_current_track()

    def highlight_current_track(self):
        for i, widget in enumerate(self.playlist_widgets):
            if i == self.current_index:
                widget['frame'].configure(fg_color=self.colors['primary'])
                widget['title'].configure(text_color="white")
                widget['artist'].configure(text_color="#e0e0e0")
            else:
                widget['frame'].configure(fg_color="transparent")
                widget['title'].configure(text_color="white")
                widget['artist'].configure(text_color="gray")

    def show_context_menu(self, event, index):
        self.context_menu_index = index
        menu = tk.Menu(self.window, tearoff=0, bg='#2A2B2E', fg='white',
                      activebackground=self.colors['primary'])
        menu.add_command(label="🎨 Изменить обложку", command=self.change_track_cover)
        menu.add_command(label="🗑️ Удалить обложку", command=self.remove_track_cover)
        menu.add_separator()
        menu.add_command(label="ℹ️ Информация о треке", command=self.show_track_info)
        menu.post(event.x_root, event.y_root)

    def remove_track(self, index):
        if index < len(self.playlist):
            self.playlist.pop(index)
            self.playlist_widgets[index]['frame'].destroy()
            self.playlist_widgets.pop(index)
            
            for i, widget in enumerate(self.playlist_widgets):
                widget['index'] = i
            
            if self.current_index == index:
                self.stop()
                if len(self.playlist) > 0:
                    self.current_index = min(index, len(self.playlist) - 1)
                    self.load_track(self.current_index)
                else:
                    self.current_index = -1
                    self.song_title.configure(text="No track selected")
                    self.song_artist.configure(text="---")
                    self.cover_label.configure(text="🎵", font=ctk.CTkFont(size=100))
            elif self.current_index > index:
                self.current_index -= 1
            
            self.update_track_count()
            self.update_stats()
            self.update_status("Track removed from playlist", "error")

    def change_track_cover(self):
        index = self.context_menu_index if hasattr(self, 'context_menu_index') else self.current_index
        
        if index < 0 or index >= len(self.playlist):
            messagebox.showwarning("Warning", "Select a track first!")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select cover image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        
        if file_path:
            track_path = self.playlist[index]
            self.save_cover_for_track(track_path, file_path)
            
            if index == self.current_index:
                self.load_album_art()
            
            self.update_status(f"Cover updated for track {index + 1}", "success")
            messagebox.showinfo("Success", "Cover image updated successfully!")

    def remove_track_cover(self):
        index = self.context_menu_index if hasattr(self, 'context_menu_index') else self.current_index
        
        if index < 0 or index >= len(self.playlist):
            messagebox.showwarning("Warning", "Select a track first!")
            return
        
        track_path = self.playlist[index]
        
        try:
            if track_path.lower().endswith('.mp3'):
                audio = ID3(track_path)
                audio.delall('APIC')
                audio.save()
        except:
            pass
        
        cache_key = hashlib.md5(track_path.encode()).hexdigest() + '.jpg'
        cache_path = os.path.join(self.cache_dir, cache_key)
        if os.path.exists(cache_path):
            os.remove(cache_path)
        
        if index == self.current_index:
            self.cover_label.configure(text="🎵", font=ctk.CTkFont(size=100))
            if hasattr(self.cover_label, 'image'):
                self.cover_label.image = None
        
        self.update_status(f"Cover removed for track {index + 1}", "error")
        messagebox.showinfo("Success", "Cover removed successfully!")

    def show_track_info(self):
        index = self.context_menu_index if hasattr(self, 'context_menu_index') else self.current_index
        
        if index < 0 or index >= len(self.playlist):
            return
        
        track_path = self.playlist[index]
        title, artist = self.get_metadata(track_path)
        file_size = os.path.getsize(track_path) / (1024 * 1024)
        
        info_text = f"""
        🎵 Track Information:
        
        Title: {title}
        Artist: {artist}
        File: {os.path.basename(track_path)}
        Size: {file_size:.2f} MB
        """
        
        messagebox.showinfo("Track Info", info_text)

    def save_cover_for_track(self, track_path, image_path):
        if track_path.lower().endswith('.mp3'):
            try:
                image = Image.open(image_path)
                
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                from io import BytesIO
                img_bytes = BytesIO()
                image.save(img_bytes, format='JPEG', quality=90)
                img_data = img_bytes.getvalue()
                
                audio = ID3(track_path)
                audio.delall('APIC')
                audio.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=img_data
                ))
                audio.save()
            except Exception as e:
                print(f"Error saving to ID3: {e}")
        
        cache_key = hashlib.md5(track_path.encode()).hexdigest() + '.jpg'
        cache_path = os.path.join(self.cache_dir, cache_key)
        
        img = Image.open(image_path)
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        img.save(cache_path)

    def load_album_art(self):
        cache_key = hashlib.md5(self.current_track_path.encode()).hexdigest() + '.jpg'
        cache_path = os.path.join(self.cache_dir, cache_key)
        
        if os.path.exists(cache_path):
            try:
                img = Image.open(cache_path)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 400))
                self.cover_label.configure(image=photo, text="")
                self.cover_label.image = photo
                return
            except:
                pass
        
        try:
            if self.current_track_path.lower().endswith('.mp3'):
                audio = ID3(self.current_track_path)
                for tag in audio.getall('APIC'):
                    from io import BytesIO
                    img = Image.open(BytesIO(tag.data))
                    img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    img.save(cache_path)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 400))
                    self.cover_label.configure(image=photo, text="")
                    self.cover_label.image = photo
                    return
        except:
            pass
        
        self.cover_label.configure(text="🎵", font=ctk.CTkFont(size=100))
        if hasattr(self.cover_label, 'image'):
            self.cover_label.image = None

    def add_tracks(self):
        file_paths = filedialog.askopenfilenames(
            title="Select audio files",
            filetypes=[("Audio files", "*.mp3 *.wav *.ogg *.flac"), ("All files", "*.*")]
        )
        
        for file_path in file_paths:
            if file_path not in self.playlist:
                title, artist = self.get_metadata(file_path)
                self.playlist.append(file_path)
                self.add_track_to_playlist_ui(file_path, len(self.playlist) - 1, title, artist)
                self.update_status(f"Added: {title}", "success")
        
        if len(self.playlist) > 0 and self.current_index == -1:
            self.current_index = 0
            self.load_track(self.current_index)

    def get_metadata(self, file_path):
        try:
            audio = File(file_path)
            if audio is not None:
                title = str(audio.get('TIT2', [''])[0]) if audio.get('TIT2') else Path(file_path).stem
                artist = str(audio.get('TPE1', ['Unknown Artist'])[0]) if audio.get('TPE1') else "Unknown Artist"
                return title, artist
        except:
            pass
        return Path(file_path).stem, "Unknown Artist"

    def remove_selected_track(self):
        if self.current_index >= 0:
            self.remove_track(self.current_index)

    def load_track(self, index):
        if 0 <= index < len(self.playlist):
            self.current_track_path = self.playlist[index]
            title, artist = self.get_metadata(self.current_track_path)
            self.current_track = title
            self.song_title.configure(text=title)
            self.song_artist.configure(text=artist)
            
            if self.current_track_path in self.favorites:
                self.fav_btn.configure(fg_color="#FF6584")
            else:
                self.fav_btn.configure(fg_color="transparent")
            
            try:
                audio = MP3(self.current_track_path)
                self.total_length = audio.info.length
                self.total_time_label.configure(text=self.format_time(self.total_length))
            except:
                self.total_length = 0
                self.total_time_label.configure(text="0:00")
            
            self.highlight_current_track()
            self.load_album_art()
            self.update_status(f"Loaded: {self.current_track}", "info")

    def play(self):
        if self.current_track_path and os.path.exists(self.current_track_path):
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.is_playing = True
                self.play_pause_btn.configure(text="⏸")
                self.update_status("Playing", "playing")
            else:
                try:
                    pygame.mixer.music.load(self.current_track_path)
                    pygame.mixer.music.play()
                    self.is_playing = True
                    self.is_paused = False
                    self.play_pause_btn.configure(text="⏸")
                    self.current_time = 0
                    self.update_status(f"Now playing: {self.current_track}", "playing")
                    
                    title, artist = self.get_metadata(self.current_track_path)
                    self.add_to_history(self.current_track_path, title, artist)
                    
                    self.update_slider_flag = True
                    threading.Thread(target=self.update_progress_thread, daemon=True).start()
                except Exception as e:
                    self.update_status(f"Error: {str(e)}", "error")

    def play_pause(self):
        if self.current_track_path:
            if self.is_playing and not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                self.play_pause_btn.configure(text="▶")
                self.update_status("Paused", "paused")
            elif self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.play_pause_btn.configure(text="⏸")
                self.update_status("Playing", "playing")
            else:
                self.play()

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_time = 0
        self.play_pause_btn.configure(text="▶")
        self.progress_slider.set(0)
        self.current_time_label.configure(text="0:00")
        self.update_status("Stopped", "info")

    def next_track(self):
        if self.playlist:
            if self.repeat_mode == "one":
                self.load_track(self.current_index)
                self.play()
                return
            elif self.shuffle_mode:
                new_index = random.randint(0, len(self.playlist) - 1)
                while new_index == self.current_index and len(self.playlist) > 1:
                    new_index = random.randint(0, len(self.playlist) - 1)
                self.current_index = new_index
            elif self.current_index < len(self.playlist) - 1:
                self.current_index += 1
            elif self.repeat_mode == "all":
                self.current_index = 0
            else:
                self.stop()
                return
            
            self.load_track(self.current_index)
            self.play()

    def previous_track(self):
        if self.playlist:
            if self.repeat_mode == "one":
                self.load_track(self.current_index)
                self.play()
                return
            elif self.current_index > 0:
                self.current_index -= 1
            elif self.repeat_mode == "all":
                self.current_index = len(self.playlist) - 1
            else:
                self.stop()
                return
            
            self.load_track(self.current_index)
            self.play()

    def change_volume(self, value):
        volume = float(value) / 100
        pygame.mixer.music.set_volume(volume)
        self.volume_slider.set(value)
        self.volume_value_label.configure(text=f"{int(volume * 100)}%")
        
        if volume == 0:
            self.volume_button.configure(text="🔇")
        elif volume < 0.3:
            self.volume_button.configure(text="🔈")
        elif volume < 0.7:
            self.volume_button.configure(text="🔉")
        else:
            self.volume_button.configure(text="🔊")

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def update_progress_thread(self):
        while self.is_playing and not self.is_paused:
            try:
                if pygame.mixer.music.get_busy():
                    self.current_time = pygame.mixer.music.get_pos() / 1000.0
                    if self.current_time > 0:
                        self.update_slider_flag = True
                else:
                    if self.is_playing:
                        self.window.after(0, self.next_track)
                    break
                time.sleep(0.2)
            except:
                break

    def update_ui(self):
        if self.is_playing and not self.is_paused and self.total_length > 0 and not self.is_seeking:
            if self.current_time <= self.total_length:
                progress_percent = (self.current_time / self.total_length) * 100
                self.progress_slider.set(progress_percent)
                self.current_time_label.configure(text=self.format_time(self.current_time))
        
        self.window.after(200, self.update_ui)

    def start_visualization(self):
        def animate_visualization():
            if self.visualization_enabled and self.is_playing and not self.is_paused:
                self.visualization_canvas.delete("all")
                width = self.visualization_canvas.winfo_width()
                height = self.visualization_canvas.winfo_height()
                
                if width > 10:
                    bars = 40
                    bar_width = width / bars
                    
                    volume = pygame.mixer.music.get_volume()
                    if volume < 0.1:
                        volume = 0.5
                    
                    for i in range(bars):
                        amplitude = (random.random() * volume * 1.5 + 0.3)
                        sin_effect = math.sin(i * math.pi / bars) * 0.4
                        bar_height = int(height * (0.2 + amplitude * 0.6 + sin_effect))
                        bar_height = max(5, min(bar_height, height - 5))
                        
                        x1 = i * bar_width
                        y1 = height - bar_height
                        x2 = x1 + bar_width - 1
                        y2 = height
                        
                        color_ratio = bar_height / height
                        r = int(108 + (147 - 108) * color_ratio)
                        g = int(99 + (112 - 99) * color_ratio)
                        b = int(255 + (219 - 255) * color_ratio)
                        color = f'#{r:02x}{g:02x}{b:02x}'
                        
                        self.visualization_canvas.create_rectangle(x1, y1, x2, y2, 
                                                                  fill=color,
                                                                  outline="")
            
            self.window.after(50, animate_visualization)
        
        animate_visualization()

if __name__ == "__main__":
    app = ModernMusicPlayer()