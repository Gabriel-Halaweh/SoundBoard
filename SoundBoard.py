import os
import tkinter as tk
from tkinter import filedialog, ttk
import pygame

# Initialize pygame for audio playback
pygame.mixer.init()

class SoundboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Soundboard App")
        self.sound_buttons = {}
        self.volume_sliders = {}
        self.playing_sounds = {}
        self.looping_sounds = set()

        # Create a menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.menu_bar.add_command(label="Open Folder", command=self.open_folder)
        self.menu_bar.add_command(label="Exit", command=self.root.quit)

        # Scrollable frame
        self.main_frame = tk.Frame(self.root)
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.frame = tk.Frame(self.canvas)

        self.main_frame.pack(fill=tk.BOTH, expand=1)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # Create a control frame for master controls
        self.control_frame = tk.Frame(self.root)

        # Create a "Stop All" button
        self.stop_all_button = ttk.Button(self.control_frame, text="Stop All", command=self.stop_all_sounds)
        self.stop_all_button.pack(side=tk.LEFT)

        # Create a master volume label
        self.volume_label = tk.Label(self.control_frame, text="Master Volume:")
        self.volume_label.pack(side=tk.LEFT, padx=10)

        # Create a master volume slider
        self.master_volume_slider = ttk.Scale(self.control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_master_volume)
        self.master_volume_slider.set(100)  # Set the initial value to max volume
        self.master_volume_slider.pack(side=tk.LEFT)

        self.control_frame.pack(fill=tk.X, padx=10, pady=10)

        # Bind the mouse wheel event to the canvas
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

    def open_folder(self):
        folder_path = filedialog.askdirectory(title="Select a Folder")
        if folder_path:
            self.load_sounds_from_folder(folder_path)
            self.root.geometry("1200x600")  # Resize the window to 1200x600

    def load_sounds_from_folder(self, folder_path):
        # Clear existing buttons and sliders
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.sound_buttons.clear()
        self.volume_sliders.clear()

        # List sound files
        sound_files = [f for f in os.listdir(folder_path) if f.endswith((".mp3", ".wav"))]
        self.create_buttons_and_sliders(folder_path, sound_files)

    def create_buttons_and_sliders(self, folder_path, sound_files):
        for index, sound_file in enumerate(sound_files):
            row = index // 4
            col = index % 4

            # Create a button
            sound_button = ttk.Button(self.frame, text=sound_file, command=lambda file=sound_file: self.play_sound(folder_path, file))
            sound_button.grid(row=row, column=col*2, pady=10, padx=10)

            # Bind left-click to play and right-click to stop
            sound_button.bind('<Button-1>', lambda event, file=sound_file: self.play_sound(folder_path, file))
            sound_button.bind('<Button-3>', lambda event, file=sound_file: self.stop_sound(file))

            # Bind middle-click to toggle looping
            sound_button.bind('<Button-2>', lambda event, file=sound_file: self.toggle_loop(event, file))

            # Create a volume slider
            volume_slider = ttk.Scale(self.frame, from_=0, to=100, orient=tk.HORIZONTAL, command=lambda val, file=sound_file: self.set_volume(val, file), value=100)
            volume_slider.grid(row=row, column=col*2+1, pady=10, padx=10)

            self.sound_buttons[sound_file] = sound_button
            self.volume_sliders[sound_file] = volume_slider


    def play_sound(self, folder_path, file):
        # Stop sound if already playing
        if file in self.playing_sounds:
            self.playing_sounds[file].stop()
            del self.playing_sounds[file]
            self.update_button_style(file)

        # Play sound
        sound_path = os.path.join(folder_path, file)
        sound_obj = pygame.mixer.Sound(sound_path)
        sound_obj.set_volume((self.volume_sliders[file].get() / 100) * (self.master_volume_slider.get() / 100))
        sound_obj.play(loops=-1 if file in self.looping_sounds else 0)
        self.playing_sounds[file] = sound_obj
        self.update_button_style(file)

    def stop_sound(self, file):
        # Stop sound prematurely
        if file in self.playing_sounds:
            self.playing_sounds[file].stop()
            if file in self.looping_sounds:
                self.looping_sounds.remove(file)  # Unloop the sound
            del self.playing_sounds[file]
            self.update_button_style(file)

    def set_volume(self, val, file):
        volume = float(val) / 100.0
        if file in self.playing_sounds:
            self.playing_sounds[file].set_volume((volume * self.master_volume_slider.get()) / 100)

    def toggle_loop(self, event, file):
        if file in self.looping_sounds:
            self.looping_sounds.remove(file)
        else:
            self.looping_sounds.add(file)
        self.update_button_style(file)

    def stop_all_sounds(self):
        for file in list(self.playing_sounds.keys()):
            self.playing_sounds[file].stop()
            del self.playing_sounds[file]
            self.update_button_style(file)

    def on_mousewheel(self, event):
        # Scroll the canvas when the mouse wheel is scrolled
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def set_master_volume(self, val):
        # Adjust the volume of all playing sounds taking individual volume sliders into account
        master_volume = float(val) / 100.0
        for file, sound_obj in self.playing_sounds.items():
            sound_obj.set_volume((self.volume_sliders[file].get() / 100) * master_volume)
            self.update_button_style(file)

    def update_button_style(self, file):
        # Update the button style based on whether the sound is playing or looping
        if file in self.playing_sounds:
            if file in self.looping_sounds:
                self.sound_buttons[file].configure(style='Loop.TButton')
            else:
                self.sound_buttons[file].configure(style='Play.TButton')
                if file in self.looping_sounds:
                    self.looping_sounds.remove(file)
                
        else:
            self.sound_buttons[file].configure(style='TButton')

if __name__ == "__main__":
    root = tk.Tk()
    app = SoundboardApp(root)

    # Configure button styles
    style = ttk.Style()
    style.configure("TButton", foreground="black", width=20, height=2)
    style.configure("Play.TButton", foreground="green")
    style.configure("Loop.TButton", foreground="orange")

    root.mainloop()
