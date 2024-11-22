from tkinter import *
from tkinter import filedialog
import json
import os

def config():

    data = readJson('config.json')
    lang = readJson('langs.json')
    lang = lang[lang['currentLanguage']]
    
    if data["download_path"] == None:
        data["download_path"] = os.path.join(os.path.expanduser("~"), 'Downloads')
    
    
    def insertDir(dir, dirText):
            dirText.config(state='normal')
            dirText.delete("1.0", END)
            dirText.insert(END, dir) 
            dirText.config(state='disabled')
    
    def changeDir(dirText):
        directory_path = filedialog.askdirectory(title=lang['selectDir'])

        if directory_path:
            insertDir(directory_path, dirText)
            
            data = {
                    "download_path": directory_path
                    }
            
            writeJson(data)
            

    root = Toplevel(bg="#333")
    root.title(lang['configLabel'])
    root.geometry("400x150")
    root.iconbitmap("Assets/Images/YTDownload.ico")
    root.resizable(False, False)
    
    root.transient()
    root.grab_set()
    
    root.attributes("-topmost", True)
    
    frame = Frame(root, bg="#333")
    frame.pack(expand=True, fill=BOTH)
    
    Label(frame, text="_______________________________________________________________________________________________________________________", font=50, bg="#333", fg="#666").place(x=0, y=25)
    
    Label(frame, text=lang['configLabel'], bg="#333", foreground="#fff", font=100).grid(column=0, row=0, sticky='n', pady=10)
    
    Label(frame, bg="#333").grid(column=0, row=1)

    Label(frame, text=f"{lang['downloadDirLabel']}: ", bg="#333", foreground="#fff", font=15).grid(column=0, row=2, sticky='w', padx=10)
    
    textWidget = Text(frame, height=1, width=30, bg="#fff", fg="#000", wrap=NONE, state='disabled') 
    textWidget.grid(column=1, row=2, columnspan=3, sticky='nsew')
    
    dirbuttom = Button(frame, text=lang['changeDirLabel'], bg="#999", fg="#fff", command=lambda: changeDir(textWidget))
    dirbuttom.grid(column=4, row=2, sticky='e', padx=1)
    
    Label(frame, text=f"{lang['creatorLabel']}: ", bg="#333", fg="#fff", font=15).grid(column=0, row=3, pady=10)
    Label(frame, text="Mateoxyz", bg="#333", fg="#fff", font=15).grid(column=2, row=3, sticky='e', columnspan=2, pady=20)
    
    insertDir(data["download_path"], textWidget)
    
def readJson(jsonName):
    with open(jsonName, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data

def writeJson(data):
    with open('config.json', 'w') as file:
        json.dump(data, file, indent=4)
        
def predeterminedJson():
    data = {
            "download_path": None,
            }
    
    writeJson(data)