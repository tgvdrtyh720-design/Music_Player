import requests
from bs4 import BeautifulSoup
import customtkinter as ctk
import pygame
import threading
import time
import json
import os

class HitmoRadioPlayer:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("🎵 Hitmo Радио")
        self.window.geometry("750x800")
        self.window.configure(fg_color="#1a1a2e")
        
        pygame.mixer.init()
        
        self.tracks = []
        self.current_track = None
        self.is_playing = False
        self.current_index = -1
        self.cache_file = "hitmo_cache.json"
        
        self.create_widgets()
        self.load_tracks()
        
        self.window.mainloop()
    
    def create_widgets(self):
        # Заголовок
        title = ctk.CTkLabel(self.window, text="🎵 Hitmo Радио", 
                            font=ctk.CTkFont(size=28, weight="bold"),
                            text_color="#6C63FF")
        title.pack(pady=20)
        
        # Статус
        self.status_label = ctk.CTkLabel(self.window, text="Загрузка треков...", 
                                        font=ctk.CTkFont(size=13),
                                        text_color="#888888")
        self.status_label.pack(pady=(0, 15))
        
        # Поиск
        search_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Поиск по трекам...",
                                        height=35,
                                        font=ctk.CTkFont(size=13))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.search_tracks)
        
        self.refresh_btn = ctk.CTkButton(search_frame, text="🔄", width=50, height=35,
                                       command=self.load_tracks,
                                       fg_color="#6C63FF",
                                       hover_color="#5a52d6",
                                       font=ctk.CTkFont(size=18))
        self.refresh_btn.pack(side="right")
        
        # Список треков
        self.track_list = ctk.CTkScrollableFrame(self.window, width=500, height=380,
                                                fg_color="#2A2B2E",
                                                corner_radius=15)
        self.track_list.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Информация о текущем треке
        self.current_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        self.current_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        self.current_label = ctk.CTkLabel(self.current_frame, text="💿 Не выбрано", 
                                         font=ctk.CTkFont(size=15, weight="bold"),
                                         text_color="white")
        self.current_label.pack(side="left")
        
        # Управление воспроизведением
        player_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        player_frame.pack(pady=15, fill="x", padx=20)
        
        controls_frame = ctk.CTkFrame(player_frame, fg_color="transparent")
        controls_frame.pack(side="left")
        
        self.prev_btn = ctk.CTkButton(controls_frame, text="⏮", 
                                     command=self.prev_track,
                                     fg_color="#2A2B2E",
                                     hover_color="#6C63FF",
                                     width=50,
                                     height=40,
                                     font=ctk.CTkFont(size=18))
        self.prev_btn.pack(side="left", padx=5)
        
        self.play_btn = ctk.CTkButton(controls_frame, text="▶ Воспроизвести", 
                                     command=self.play_pause,
                                     fg_color="#6C63FF",
                                     hover_color="#5a52d6",
                                     width=140,
                                     height=40,
                                     font=ctk.CTkFont(size=14, weight="bold"))
        self.play_btn.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(controls_frame, text="⏭", 
                                     command=self.next_track,
                                     fg_color="#2A2B2E",
                                     hover_color="#6C63FF",
                                     width=50,
                                     height=40,
                                     font=ctk.CTkFont(size=18))
        self.next_btn.pack(side="left", padx=5)
        
        # Громкость
        volume_frame = ctk.CTkFrame(player_frame, fg_color="transparent")
        volume_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
        
        self.volume_label = ctk.CTkLabel(volume_frame, text="🔊", 
                                        font=ctk.CTkFont(size=16))
        self.volume_label.pack(side="left", padx=(0, 10))
        
        self.volume_slider = ctk.CTkSlider(volume_frame, from_=0, to=100,
                                          command=self.change_volume,
                                          button_color="#6C63FF",
                                          progress_color="#6C63FF",
                                          width=150)
        self.volume_slider.pack(side="left", fill="x", expand=True)
        self.volume_slider.set(70)
        pygame.mixer.music.set_volume(0.7)
        
        self.volume_value = ctk.CTkLabel(volume_frame, text="70%", 
                                        font=ctk.CTkFont(size=12),
                                        width=35)
        self.volume_value.pack(side="left", padx=(10, 0))
    
    def load_tracks(self):
        """Загрузка треков с Hitmo"""
        # Проверяем кэш
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.tracks = json.load(f)
                    self.update_list()
                    self.status_label.configure(text=f"✅ Загружено {len(self.tracks)} треков (кэш)")
                    return
            except:
                pass
        
        self.status_label.configure(text="🔄 Загрузка треков с Hitmo...")
        self.refresh_btn.configure(state="disabled")
        
        def load():
            try:
                # Парсим главную страницу
                url = "https://rus.hitmoz.org/"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                self.tracks = []
                
                # Находим все треки
                track_items = soup.find_all('li', class_='tracks__item')
                
                for item in track_items:
                    try:
                        title_elem = item.find('div', class_='track__title')
                        artist_elem = item.find('div', class_='track__desc')
                        
                        if title_elem and artist_elem:
                            title = title_elem.text.strip()
                            artist = artist_elem.text.strip()
                            
                            # Находим ссылку на скачивание
                            download_btn = item.find('a', class_='track__download-btn')
                            if download_btn:
                                download_url = download_btn.get('href')
                                if download_url and not download_url.startswith('http'):
                                    download_url = 'https://rus.hitmoz.org' + download_url
                                
                                self.tracks.append({
                                    'title': title,
                                    'artist': artist,
                                    'url': download_url,
                                    'display': f"{artist} - {title}"
                                })
                    except Exception as e:
                        print(f"Ошибка парсинга трека: {e}")
                        continue
                
                # Сохраняем в кэш
                if self.tracks:
                    with open(self.cache_file, 'w', encoding='utf-8') as f:
                        json.dump(self.tracks, f, ensure_ascii=False, indent=2)
                
                self.window.after(0, self.update_list)
                self.window.after(0, lambda: self.status_label.configure(
                    text=f"✅ Загружено {len(self.tracks)} треков с Hitmo"
                ))
                
            except Exception as e:
                # Если ошибка - пробуем использовать альтернативный метод
                self.load_tracks_alternative()
            
            self.window.after(0, lambda: self.refresh_btn.configure(state="normal"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def load_tracks_alternative(self):
        """Альтернативный метод загрузки (через поиск)"""
        try:
            url = "https://rus.hitmoz.org/search"
            params = {"q": "популярное"}
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            self.tracks = []
            track_items = soup.find_all('li', class_='tracks__item')
            
            for item in track_items[:20]:
                try:
                    title_elem = item.find('div', class_='track__title')
                    artist_elem = item.find('div', class_='track__desc')
                    
                    if title_elem and artist_elem:
                        title = title_elem.text.strip()
                        artist = artist_elem.text.strip()
                        
                        download_btn = item.find('a', class_='track__download-btn')
                        if download_btn:
                            download_url = download_btn.get('href')
                            if download_url and not download_url.startswith('http'):
                                download_url = 'https://rus.hitmoz.org' + download_url
                            
                            self.tracks.append({
                                'title': title,
                                'artist': artist,
                                'url': download_url,
                                'display': f"{artist} - {title}"
                            })
                except:
                    continue
            
            # Если треков мало - добавляем примеры
            if len(self.tracks) < 5:
                self.tracks = self.get_fallback_tracks()
            
            self.window.after(0, self.update_list)
            self.window.after(0, lambda: self.status_label.configure(
                text=f"✅ Загружено {len(self.tracks)} треков"
            ))
            
        except Exception as e:
            self.tracks = self.get_fallback_tracks()
            self.window.after(0, self.update_list)
            self.window.after(0, lambda: self.status_label.configure(
                text=f"⚠️ Использую примеры ({len(self.tracks)} треков)"
            ))
    
    def get_fallback_tracks(self):
        """Резервный список треков"""
        return [
            {'title': 'Она танцует под шадэ', 'artist': 'Индия by', 'url': '', 'display': 'Индия by - Она танцует под шадэ'},
            {'title': 'Шадэ', 'artist': 'By Индия, Xcho, MOT', 'url': '', 'display': 'By Индия, Xcho, MOT - Шадэ'},
            {'title': 'Ты не бойся ночи', 'artist': 'ENZRO', 'url': '', 'display': 'ENZRO - Ты не бойся ночи'},
            {'title': 'Мальборо', 'artist': 'SAYAN', 'url': '', 'display': 'SAYAN - Мальборо'},
            {'title': 'Сыпь, гармоника!', 'artist': 'СДП', 'url': '', 'display': 'СДП - Сыпь, гармоника!'},
        ]
    
    def update_list(self, search_query=""):
        """Обновление списка треков"""
        for widget in self.track_list.winfo_children():
            widget.destroy()
        
        filtered = self.tracks
        if search_query:
            filtered = [t for t in self.tracks if search_query.lower() in t['display'].lower()]
        
        if not filtered:
            empty_label = ctk.CTkLabel(self.track_list, text="🔍 Ничего не найдено",
                                      font=ctk.CTkFont(size=14),
                                      text_color="#888888")
            empty_label.pack(pady=50)
            return
        
        for i, track in enumerate(filtered):
            card = ctk.CTkFrame(self.track_list, fg_color="#3A3B3E", corner_radius=10)
            card.pack(fill="x", pady=3, padx=5)
            
            # Информация о треке
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=8)
            
            title_label = ctk.CTkLabel(info_frame, text=track['title'],
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      anchor="w")
            title_label.pack(anchor="w")
            
            artist_label = ctk.CTkLabel(info_frame, text=track['artist'],
                                       font=ctk.CTkFont(size=11),
                                       text_color="#888888",
                                       anchor="w")
            artist_label.pack(anchor="w")
            
            # Кнопка воспроизведения
            play_btn = ctk.CTkButton(card, text="▶", 
                                    command=lambda t=track, idx=i: self.play_track(t, idx),
                                    fg_color="#6C63FF",
                                    hover_color="#5a52d6",
                                    width=40,
                                    height=35,
                                    font=ctk.CTkFont(size=16))
            play_btn.pack(side="right", padx=15, pady=8)
            
            # Клик по карточке тоже воспроизводит
            card.bind("<Button-1>", lambda e, t=track, idx=i: self.play_track(t, idx))
            title_label.bind("<Button-1>", lambda e, t=track, idx=i: self.play_track(t, idx))
            artist_label.bind("<Button-1>", lambda e, t=track, idx=i: self.play_track(t, idx))
    
    def search_tracks(self, event):
        query = self.search_entry.get()
        self.update_list(query)
    
    def play_track(self, track, index):
        """Воспроизведение трека"""
        self.current_index = index
        self.current_track = track
        self.current_label.configure(text=f"🎵 {track['display']}")
        
        # Если есть ссылка - воспроизводим
        if track.get('url'):
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(track['url'])
                pygame.mixer.music.play()
                
                self.is_playing = True
                self.play_btn.configure(text="⏸ Пауза", fg_color="#FF6584")
                self.status_label.configure(text=f"🎵 Играет: {track['display'][:40]}")
                
                threading.Thread(target=self.check_playing, daemon=True).start()
                
            except Exception as e:
                self.status_label.configure(text=f"❌ Ошибка: {str(e)[:40]}")
                # Если ссылка не работает - показываем уведомление
                self.show_audio_not_available(track)
        else:
            # Если нет ссылки - пытаемся найти через поиск
            self.find_track_url(track)
    
    def find_track_url(self, track):
        """Поиск URL трека через сайт"""
        self.status_label.configure(text=f"🔍 Поиск: {track['title']}...")
        
        def search():
            try:
                url = "https://rus.hitmoz.org/search"
                params = {"q": f"{track['artist']} {track['title']}"}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем первый трек в результатах
                first_track = soup.find('li', class_='tracks__item')
                if first_track:
                    download_btn = first_track.find('a', class_='track__download-btn')
                    if download_btn:
                        download_url = download_btn.get('href')
                        if download_url and not download_url.startswith('http'):
                            download_url = 'https://rus.hitmoz.org' + download_url
                        
                        # Обновляем URL в списке
                        if self.current_index < len(self.tracks):
                            self.tracks[self.current_index]['url'] = download_url
                        
                        # Воспроизводим
                        self.window.after(0, lambda: self.play_track(track, self.current_index))
                        return
                
                self.window.after(0, lambda: self.status_label.configure(
                    text=f"⚠️ Не найден URL для: {track['title']}"
                ))
                self.window.after(0, lambda: self.show_audio_not_available(track))
                
            except Exception as e:
                self.window.after(0, lambda: self.status_label.configure(
                    text=f"❌ Ошибка поиска: {str(e)[:40]}"
                ))
                self.window.after(0, lambda: self.show_audio_not_available(track))
        
        threading.Thread(target=search, daemon=True).start()
    
    def show_audio_not_available(self, track):
        """Показ сообщения о недоступности трека"""
        self.current_label.configure(text=f"⚠️ {track['display'][:30]}")
        self.play_btn.configure(text="▶ Воспроизвести", fg_color="#6C63FF")
        self.is_playing = False
    
    def play_pause(self):
        """Пауза/воспроизведение"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_btn.configure(text="▶ Воспроизвести", fg_color="#6C63FF")
        else:
            if self.current_track:
                pygame.mixer.music.unpause()
                self.is_playing = True
                self.play_btn.configure(text="⏸ Пауза", fg_color="#FF6584")
            else:
                if self.tracks:
                    self.play_track(self.tracks[0], 0)
    
    def next_track(self):
        """Следующий трек"""
        if self.tracks and self.current_index < len(self.tracks) - 1:
            self.play_track(self.tracks[self.current_index + 1], self.current_index + 1)
    
    def prev_track(self):
        """Предыдущий трек"""
        if self.tracks and self.current_index > 0:
            self.play_track(self.tracks[self.current_index - 1], self.current_index - 1)
    
    def check_playing(self):
        """Проверка состояния воспроизведения"""
        while self.is_playing:
            time.sleep(0.5)
            if not pygame.mixer.music.get_busy():
                self.window.after(0, lambda: self.current_label.configure(text="⏸ Трек завершён"))
                self.window.after(0, lambda: self.status_label.configure(text="⏸ Воспроизведение завершено"))
                self.window.after(0, lambda: self.play_btn.configure(text="▶ Воспроизвести", fg_color="#6C63FF"))
                self.is_playing = False
                break
    
    def stop_radio(self):
        """Остановка воспроизведения"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_btn.configure(text="▶ Воспроизвести", fg_color="#6C63FF")
        self.current_label.configure(text="💿 Остановлено")
        self.status_label.configure(text="⏸ Воспроизведение остановлено")
    
    def change_volume(self, value):
        volume = float(value) / 100
        pygame.mixer.music.set_volume(volume)
        self.volume_value.configure(text=f"{int(volume * 100)}%")
        
        if volume == 0:
            self.volume_label.configure(text="🔇")
        elif volume < 0.3:
            self.volume_label.configure(text="🔈")
        elif volume < 0.7:
            self.volume_label.configure(text="🔉")
        else:
            self.volume_label.configure(text="🔊")

if __name__ == "__main__":
    app = HitmoRadioPlayer()