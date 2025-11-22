import json
import os
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
)
from PySide6.QtGui import QIcon


def config(parent=None):
    data = readJson("config.json")
    lang = readJson("langs.json")
    currentLang = lang["currentLanguage"]
    lang = lang[currentLang]

    if data["download_path"] is None:
        data["download_path"] = os.path.join(os.path.expanduser("~"), "Downloads")

    def insertDir(directory: str, dirText: QTextEdit):
        dirText.setReadOnly(False)
        dirText.setPlainText(directory)
        dirText.setReadOnly(True)

    def changeDir(dirText: QTextEdit):
        directory_path = QFileDialog.getExistingDirectory(parent, lang["selectDir"])

        if directory_path:
            insertDir(directory_path, dirText)
            writeJson("config.json", {"download_path": directory_path})

    root = QDialog(parent)
    root.setWindowTitle(lang["configLabel"])
    root.setFixedSize(400, 350)
    root.setWindowIcon(QIcon("Assets/Images/YTDownload.ico"))
    root.setModal(True)

    frame = QGridLayout(root)
    frame.setContentsMargins(15, 15, 15, 15)
    frame.setVerticalSpacing(12)

    title = QLabel(lang["configLabel"])
    title.setStyleSheet("color: #fff; font-size: 20px;")
    frame.addWidget(title, 0, 0, 1, 2)

    frame.addWidget(QLabel(""), 1, 0)

    download_label = QLabel(f"{lang['downloadDirLabel']}:")
    download_label.setStyleSheet("color: #fff;")
    frame.addWidget(download_label, 2, 0)

    textWidget = QTextEdit()
    textWidget.setFixedHeight(30)
    textWidget.setReadOnly(True)
    frame.addWidget(textWidget, 2, 1)

    dirbutton = QPushButton(lang["changeDirLabel"])
    dirbutton.clicked.connect(lambda: changeDir(textWidget))
    frame.addWidget(dirbutton, 2, 2)

    language_label = QLabel(lang["languageLabel"])
    language_label.setStyleSheet("color: #fff;")
    frame.addWidget(language_label, 3, 0)

    options = ["English", "Español", "Française", "Deutsch", "Italiano"]
    langMap = {"en": "English", "es": "Español", "fr": "Française", "de": "Deutsch", "it": "Italiano"}

    menuLangs = QComboBox()
    menuLangs.addItems(options)
    menuLangs.setCurrentText(langMap[currentLang])
    menuLangs.currentTextChanged.connect(ChangeLang)
    frame.addWidget(menuLangs, 3, 1)

    creator_label = QLabel(f"{lang['creatorLabel']}: ")
    creator_label.setStyleSheet("color: #fff;")
    frame.addWidget(creator_label, 4, 0)

    creator_value = QLabel("Mateoxyz")
    creator_value.setStyleSheet("color: #fff;")
    frame.addWidget(creator_value, 4, 1)

    insertDir(data["download_path"], textWidget)

    root.setStyleSheet("background-color: #333; color: #fff;")
    root.exec()


def readJson(jsonName):
    with open(jsonName, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data


def writeJson(jsonName, data):
    with open(jsonName, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def predeterminedJson():
    data = {
        "download_path": None,
    }

    writeJson("config.json", data)


def ChangeLang(selected_lang):
    langMap = {"English": "en", "Español": "es", "Française": "fr", "Deutsch": "de", "Italiano": "it"}

    langs = readJson("langs.json")
    langs["currentLanguage"] = langMap[selected_lang]
    writeJson("langs.json", langs)

    QMessageBox.information(None, langs[langMap[selected_lang]]["languageLabel"], langs[langMap[selected_lang]]["languageInfo"])
