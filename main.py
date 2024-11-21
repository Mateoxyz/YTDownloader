import os, sys

def TemporalPath():
    """
    Modifica temporalmente el PATH del sistema para incluir el directorio de ffmpeg.
    Devuelve el valor original del PATH para restaurarlo posteriormente.
    """
    
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))

    
    tempDir = os.path.join(current_dir, "ffmpeg", "bin")
    
    
    original_path = os.environ.get("PATH", "")
    
    
    os.environ["PATH"] = f"{tempDir}{os.pathsep}{original_path}"
    return original_path


def RestorePath(original_path):
    """
    Restaura el PATH del sistema al valor original.
    """
    if original_path:
        os.environ["PATH"] = original_path
 


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
        configButton.grid(column=7, row=0, sticky='nsew' )
        

        frame2 = tk.Frame(frame, bg="#333")
        frame2.grid(column=0, row=1, rowspan=20, columnspan=10, sticky="nsew")
        
        tk.Label(frame2, text="URL:                                                                   ", bg="#333", font=35, foreground="#fff", justify="left").grid(column=0, row=0,columnspan=3, padx=5)
        
        urlentry = tk.Entry(frame2, width=125)
        urlentry.grid(column=0, row=1, columnspan=6, padx=10)
        
        
        tk.Label(frame2, bg="#333", width=15).grid(column=6, row=2, padx=10, pady=10)
        
        searchbutton = tk.Button(frame2, text="Search", width=15, command=lambda: self.executor.submit(self.StartSearch, urlentry.get(), filenameentry, durationLabel, weigthLabel, thumbnailLabel))
        searchbutton.grid(column=6, row=1)
        
        
        tk.Label(frame, text="_______________________________________________________________________________________________________________________", font=50, bg="#333", fg="#666").grid(column=0, row=3, columnspan=10, pady=10)
        
        tk.Label(frame2, text="Datos del Video:                                             ", bg="#333", fg="#fff", font=35).grid(column=0, row=3, columnspan=3, padx=10, pady=10)
        
        self.thumbnail = None
        
        tk.Label(frame2, bg="#333", width=50, height=12, justify="center").grid(column=1, row=4, columnspan=3, rowspan=3, sticky='nsew')
        
        thumbnailLabel = tk.Label(frame2, bg="#444", width=50, height=12, justify="center", image=self.thumbnail)
        thumbnailLabel.place(x=65, y=135, width=350, height=191)
        
        tk.Label(frame2, text="           Thumbnail", bg="#333", fg="#fff", font=15).grid(column=1, row=7, padx=10, pady=10, columnspan=2)
        
        
        tk.Label(frame2, text="File name:", bg="#333", foreground="#fff", font=15).grid(column=4, row=4)
        
        filenameentry = tk.Entry(frame2, width=50)
        filenameentry.grid(column=5, row=4, padx=10, columnspan=3)
        
        tk.Label(frame2, text="Format: ", bg="#333", foreground="#fff", font=15).grid(column=4, row=5, padx=10)
        
        options = ["----VIDEO----",
                  "MP4",
                  "----AUDIO----",
                  "MP3",
                  "WAV",
                  "OGG",]  
        
        self.selectedformat = tk.StringVar()
        self.selectedformat.set("Select an option")

        formatvideo = tk.OptionMenu(frame2, self.selectedformat, *options)  
        formatvideo.config(width=25)
        formatvideo.grid(column=5, row=5, padx=10, columnspan=2, sticky='e')
        
        tk.Label(frame2, text="Quality: ", bg="#333", foreground="#fff", font=15).grid(column=4, row=6, padx=10)

        options = ["1080p",
                   "720p",
                   "480p",
                   "360p",
                   "240p",
                   "144p"]  
        
        self.selectedquality = tk.StringVar()
        self.selectedquality.set("Select an option")

        formatvideo = tk.OptionMenu(frame2, self.selectedquality, *options)  
        formatvideo.config(width=25)
        formatvideo.grid(column=5, row=6, padx=10, columnspan=2, sticky='e')
        
        durationLabel = tk.Label(frame2, text="  Estimated duration: --",  bg="#333", foreground="#fff", font=15)
        durationLabel.grid(column=4, row=7, pady=10, columnspan=2, sticky='w')
        
        weigthLabel = tk.Label(frame2, text="Estimated file size: --",  bg="#333", foreground="#fff", font=15)
        weigthLabel.grid(column=5, row=7, pady=10, columnspan=2, sticky='e')
        
        self.progressbar = ttk.Progressbar(frame2, orient="horizontal", length=880, mode="determinate")
        self.progressbar.grid(column=0, row=9, columnspan=7, pady=10)

        downloadbutton = tk.Button(frame2, text="Download", width=50, height=2, command=lambda: self.executor.submit(self.StartDownload, urlentry.get(), filenameentry.get(), self.selectedformat.get(), self.selectedquality.get()))
        downloadbutton.grid(column=1, row=8, columnspan=5, pady=10)
        
        self.data = {}
        
        self.original_path = None
        
    def download(self, url, filename, selected_format, selected_quality):
        

        try:
            self.data = readJson()
            
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
                messagebox.showinfo("Descarga", "Descarga completa!") 
                self.progressbar['value'] = 0
        
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
            return
        
            
    
    def info(self, url, fileNameEntry, durationLabel, weightLabel, thumbLabel):
        ydl_opts = {
            'noplaylist': True,
            'format': 'bestvideo+bestaudio/best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            fileNameEntry.delete(0, tk.END)
            fileNameEntry.insert(0, info_dict.get('title', 'Sin título'))

            duration = info_dict.get('duration', 0)
            filesize = info_dict.get('filesize_approx', 0)

            minutes, seconds = divmod(duration, 60)
            duration_formatted = f"{minutes:02}:{seconds:02}"
            durationLabel.config(text=f"  Estimated duration: {duration_formatted}")

            if filesize:
                weightLabel.config(text=f"Estimated file size: {filesize / (1024 * 1024):.2f} MB")
            else:
                weightLabel.config(text="Estimated file size: Not available")
                
            thumbnail_url = info_dict.get('thumbnail', None)
            
            if thumbnail_url:
                image_data = requests.get(thumbnail_url).content
                image = Image.open(io.BytesIO(image_data))
                image = image.resize((350, 191), Image.LANCZOS)
                self.thumbnail = ImageTk.PhotoImage(image)
                thumbLabel.config(image=self.thumbnail)
                
            self.is_searching = False
                
    def progress_hook(self, d):
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
                    self.info(url, fileNameEntry, durationLabel, weightLabel, thumbLabel)
                
                else:
                    messagebox.showinfo("Busqueda", "Ingresa una URL.")
            
            else:
                messagebox.showinfo("Busqueda", "Hay una descarga en progreso, intentalo mas tarde.")
        else:
            messagebox.showinfo("Busqueda", "Ya hay una busqueda en progreso, intentalo mas tarde")
    
    def StartDownload(self, url, filename, selected_format, selected_quality):
        if not self.is_downloading:
            if url != "":
                self.is_downloading = True
                self.download(url, filename, selected_format, selected_quality)
            
            else:
                messagebox.showinfo("Descarga", "Ingreasa una URL")
        
        else: 
            messagebox.showinfo("Descarga", "Ya hay una descarga en curso. Por favor, espere a que termine.")

    
if __name__ == "__main__":
    if not os.path.isfile("config.json"):
        predeterminedJson()
        
    app = DownloaderApp()
    app.mainloop()
    
    RestorePath(original_path)
    
    