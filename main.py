import os
from modifyPATH import TemporalPath, RestorePath

original_path = TemporalPath()

import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from concurrent.futures import ThreadPoolExecutor
import requests, io
from config import config, readJson, predeterminedJson

class DownloaderApp(tk.Tk):
    
    def __init__(self):
        super().__init__()
        
        self.lang = readJson('langs.json')
        self.lang = self.lang[self.lang['currentLanguage']]
        
        self.title("YTDownloader")
        self.geometry("910x545")
        self.iconbitmap("Assets/Images/YTDownload.ico")
        self.minsize(width=910, height=545)
        self.maxsize(width=910, height=545)
        self.resizable(False, False)
        
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_downloading = False
        self.is_searching = False
       
        frame = tk.Frame(self, bg="#222")
        frame.grid(column=0, row=0, sticky="nsew")
    
        original_icon = Image.open("Assets/Images/YTDownload.png")
        resized_image = original_icon.resize((75, 75), Image.LANCZOS)

        self.icon = ImageTk.PhotoImage(resized_image)
        
        tk.Label(frame, image=self.icon, bg="#222", width=75).grid(column=0, row=0, padx=0, pady=0)
        tk.Label(frame, text="YTDowloader", fg="#fff", bg="#222", font=20).grid(column=1, row=0, padx=0, pady=0, sticky='w')
        
        original_configicon = Image.open("Assets/Images/config.png")
        resized_imageconfig = original_configicon.resize((25, 25), Image.LANCZOS)
        
        self.configIcon = ImageTk.PhotoImage(resized_imageconfig)
        
        configButton = tk.Button(frame, image=self.configIcon, text="config", bg="#222", fg="#fff", activebackground="#222", width=15, height=4, bd=0, highlightthickness=0, command=config)
        configButton.place(x=850, y=13, width=50, height=50)
        

        frame2 = tk.Frame(frame, bg="#333")
        frame2.grid(column=0, row=1, rowspan=20, columnspan=10, sticky="nsew")
        
        tk.Label(frame2, text="URL:                                                                   ", bg="#333", font=35, foreground="#fff", justify="left").grid(column=0, row=0,columnspan=3, padx=5)
        
        urlentry = tk.Entry(frame2, width=125)
        urlentry.grid(column=0, row=1, columnspan=6, padx=10)
        
        
        tk.Label(frame2, bg="#333", width=15).grid(column=6, row=2, padx=10, pady=10)
        
        searchbutton = tk.Button(frame2, text=self.lang['search'], width=15, command=lambda: self.executor.submit(self.StartSearch, urlentry.get(), filenameentry, durationLabel, weigthLabel, thumbnailLabel))
        searchbutton.grid(column=6, row=1)
        
        
        tk.Label(frame, text="_______________________________________________________________________________________________________________________", font=50, bg="#333", fg="#666").grid(column=0, row=3, columnspan=10, pady=10)
        
        tk.Label(frame2, text=f"{self.lang['videoDataLabel']}:                                             ", bg="#333", fg="#fff", font=35).grid(column=0, row=3, columnspan=3, padx=10, pady=10)
        
        self.thumbnail = None
        
        tk.Label(frame2, bg="#333", width=50, height=12, justify="center").grid(column=1, row=4, columnspan=3, rowspan=3, sticky='nsew')
        
        
        
        tk.Label(frame2, text=f"           {self.lang['thumbnailLabel']}", bg="#333", fg="#fff", font=15).grid(column=1, row=7, padx=10, pady=10, columnspan=2)
        
        
        tk.Label(frame2, text=f"{self.lang['fileNameLabel']}:", bg="#333", foreground="#fff", font=15).grid(column=4, row=4)
        
        filenameentry = tk.Entry(frame2, width=50)
        filenameentry.grid(column=5, row=4, padx=10, columnspan=3)
        
        tk.Label(frame2, text=f"{self.lang['formatLabel']}:", bg="#333", foreground="#fff", font=15).grid(column=4, row=5, padx=10)
        
        options = ["----VIDEO----",
                  "MP4",
                  "----AUDIO----",
                  "MP3",
                  "WAV",
                  "OGG",]  
        
        self.selectedformat = tk.StringVar()
        self.selectedformat.set(self.lang['optionMenu'])

        formatvideo = tk.OptionMenu(frame2, self.selectedformat, *options)  
        formatvideo.config(width=25)
        formatvideo.grid(column=5, row=5, padx=10, columnspan=2, sticky='e')
        
        tk.Label(frame2, text=f"{self.lang['qualityLabel']}:", bg="#333", foreground="#fff", font=15).grid(column=4, row=6, padx=10)

        options = ["1080p",
                   "720p",
                   "480p",
                   "360p",
                   "240p",
                   "144p"]  
        
        self.selectedquality = tk.StringVar()
        self.selectedquality.set(self.lang['optionMenu'])

        formatvideo = tk.OptionMenu(frame2, self.selectedquality, *options)  
        formatvideo.config(width=25)
        formatvideo.grid(column=5, row=6, padx=10, columnspan=2, sticky='e')
        
        durationLabel = tk.Label(frame2, text=f"   {self.lang['estimatedDurationLabel']}: --",  bg="#333", foreground="#fff", font=15)
        durationLabel.grid(column=4, row=7, pady=10, columnspan=2, sticky='w')
        
        weigthLabel = tk.Label(frame2, text=f"{self.lang['estimatedFileSize']}: --",  bg="#333", foreground="#fff", font=15)
        weigthLabel.grid(column=5, row=7, pady=10, columnspan=2, sticky='e')
        
        self.progressbar = ttk.Progressbar(frame2, orient="horizontal", length=880, mode="determinate")
        self.progressbar.grid(column=0, row=9, columnspan=7, pady=10)

        downloadbutton = tk.Button(frame2, text=self.lang['downloadLabel'], width=50, height=2, command=lambda: self.executor.submit(self.StartDownload, urlentry.get(), filenameentry.get(), self.selectedformat.get(), self.selectedquality.get()))
        downloadbutton.grid(column=1, row=8, columnspan=5, pady=10)
        
        thumbnailLabel = tk.Label(frame2, bg="#444", width=50, height=12, justify="center", image=self.thumbnail)
        thumbnailLabel.place(x=65, y=135, width=350, height=191)
        
        self.data = {}
        
        self.original_path = None
        
    def download(self, url, filename, selected_format, selected_quality):
        """
        Determine the video quality and download path, then start downloading
        """

        try:
            self.data = readJson('config.json')
            
            quality_map = {
                "1080p": "bestvideo[height<=1080]+bestaudio/best",
                "720p": "bestvideo[height<=720]+bestaudio/best",
                "480p": "bestvideo[height<=480]+bestaudio/best",
                "360p": "bestvideo[height<=360]+bestaudio/best",
                "240p": "bestvideo[height<=240]+bestaudio/best",
                "144p": "bestvideo[height<=144]+bestaudio/best",
            }

            quality = quality_map.get(selected_quality, "bestvideo+bestaudio") 
        
            if self.data["download_path"] == None:
                download_path = os.path.join(os.path.expanduser("~"), 'Downloads', f'{filename}.%(ext)s')

                
            else:
                download_path = os.path.join(self.data["download_path"], f'{filename}.%(ext)s')
        
            if selected_format in  ["MP3", "WAV", "OGG"]:
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': download_path,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': selected_format.lower(),
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [self.progress_hook],
                }
            else:
                ydl_opts = {
                    'format': quality,
                    'outtmpl': download_path,
                    'merge_output_format': 'mp4',
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                    'postprocessor_args': [
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                    ],
                    'progress_hooks': [self.progress_hook], 
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])  
                self.is_downloading = False
                messagebox.showinfo(self.lang['downloadLabel'], self.lang['downloadComplete']) 
                self.progressbar['value'] = 0
        
        except Exception as e:
            messagebox.showerror(self.lang['error'], f"{self.lang['error']}: {e}")
            return
        
            
    
    def metadata(self, url, fileNameEntry, durationLabel, weightLabel, thumbLabel):
        """
        Collects the URL metadata and displays it.
        """
        
        ydl_opts = {
            'noplaylist': True,
            'format': 'bestvideo+bestaudio/best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            fileNameEntry.delete(0, tk.END)
            fileNameEntry.insert(0, info_dict.get('title', 'video'))

            duration = info_dict.get('duration', 0)
            filesize = info_dict.get('filesize_approx', 0)

            minutes, seconds = divmod(duration, 60)
            duration_formatted = f"{minutes:02}:{seconds:02}"
            durationLabel.config(text=f"   {self.lang['estimatedDurationLabel']}: {duration_formatted}")

            if filesize:
                weightLabel.config(text=f"{self.lang['estimatedFileSize']}: {filesize / (1024 * 1024):.2f} MB")
            else:
                weightLabel.config(text=f"{self.lang['estimatedFileSize']}: {self.lang['notAvailable']}")
                
            thumbnail_url = info_dict.get('thumbnail', None)
            
            if thumbnail_url:
                image_data = requests.get(thumbnail_url).content
                image = Image.open(io.BytesIO(image_data))
                image = image.resize((350, 191), Image.LANCZOS)
                self.thumbnail = ImageTk.PhotoImage(image)
                thumbLabel.config(image=self.thumbnail)
                
            self.is_searching = False
                
    def progress_hook(self, d):
        """
        Update the progress bar.
        """
        
        if d['status'] == 'downloading':
            if 'downloaded_bytes' in d and 'total_bytes' in d:
                downloaded = d['downloaded_bytes']
                total = d['total_bytes']
                if total > 0:
                    progress = downloaded / total * 100 
                    self.progressbar['value'] = progress
                    self.update_idletasks()
    
        elif d['status'] == 'finished':
            self.progressbar['value'] = 100
            self.update_idletasks()   
        
    def StartSearch(self, url, fileNameEntry, durationLabel, weightLabel, thumbLabel):
        
        if not self.is_searching:
            if not self.is_downloading:
                if url != "":
                    self.is_searching = True
                    self.metadata(url, fileNameEntry, durationLabel, weightLabel, thumbLabel)
                
                else:
                    messagebox.showinfo(self.lang['search'], self.lang['infoURL'])
            
            else:
                messagebox.showinfo(self.lang['search'], self.lang['downloadInProgress'])
        else:
            messagebox.showinfo(self.lang['search'], self.lang['searchInProgress'])
    
    def StartDownload(self, url, filename, selected_format, selected_quality):
        if not self.is_downloading:
            if url != "":
                self.is_downloading = True
                self.download(url, filename, selected_format, selected_quality)
            
            else:
                messagebox.showinfo(self.lang['downloadLabel'], self.lang['infoURL'])
        
        else: 
            messagebox.showinfo(self.lang['downloadLabel'], self.lang['downloadInProgress2'])

    
if __name__ == "__main__":
    if not os.path.isfile("config.json"):
        predeterminedJson()
        
    app = DownloaderApp()
    app.mainloop()
    
    RestorePath(original_path)
    
    