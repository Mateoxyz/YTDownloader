import os
import requests
import yt_dlp
from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from modifyPATH import TemporalPath, RestorePath
from config import config, readJson, predeterminedJson


class MetadataWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    @Slot()
    def run(self):
        try:
            ydl_opts = {
                "noplaylist": True,
                "format": "bestvideo+bestaudio/best",
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)

            thumbnail_data = None
            thumbnail_url = info_dict.get("thumbnail")
            if thumbnail_url:
                thumbnail_data = requests.get(thumbnail_url).content

            self.finished.emit({
                "info": info_dict,
                "thumbnail": thumbnail_data,
            })
        except Exception as exc:  # pragma: no cover - network errors
            self.error.emit(str(exc))


class DownloadWorker(QObject):
    progress = Signal(float)
    finished = Signal()
    error = Signal(str)

    def __init__(self, url: str, filename: str, selected_format: str, selected_quality: str):
        super().__init__()
        self.url = url
        self.filename = filename
        self.selected_format = selected_format
        self.selected_quality = selected_quality

    @Slot()
    def run(self):
        try:
            data = readJson("config.json")

            quality_map = {
                "1080p": "bestvideo[height<=1080]+bestaudio/best",
                "720p": "bestvideo[height<=720]+bestaudio/best",
                "480p": "bestvideo[height<=480]+bestaudio/best",
                "360p": "bestvideo[height<=360]+bestaudio/best",
                "240p": "bestvideo[height<=240]+bestaudio/best",
                "144p": "bestvideo[height<=144]+bestaudio/best",
            }

            quality = quality_map.get(self.selected_quality, "bestvideo+bestaudio")

            if data["download_path"] is None:
                download_path = os.path.join(os.path.expanduser("~"), "Downloads", f"{self.filename}.%(ext)s")
            else:
                download_path = os.path.join(data["download_path"], f"{self.filename}.%(ext)s")

            def progress_hook(status):
                if status.get("status") == "downloading":
                    downloaded = status.get("downloaded_bytes")
                    total = status.get("total_bytes")
                    if downloaded is not None and total:
                        progress = downloaded / total * 100
                        self.progress.emit(progress)
                elif status.get("status") == "finished":
                    self.progress.emit(100.0)

            if self.selected_format in ["MP3", "WAV", "OGG"]:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": download_path,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": self.selected_format.lower(),
                            "preferredquality": "192",
                        }
                    ],
                    "progress_hooks": [progress_hook],
                }
            else:
                ydl_opts = {
                    "format": quality,
                    "outtmpl": download_path,
                    "merge_output_format": "mp4",
                    "postprocessors": [
                        {
                            "key": "FFmpegVideoConvertor",
                            "preferedformat": "mp4",
                        }
                    ],
                    "postprocessor_args": [
                        "-c:v",
                        "copy",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "192k",
                    ],
                    "progress_hooks": [progress_hook],
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            self.finished.emit()
        except Exception as exc:  # pragma: no cover - network errors
            self.error.emit(str(exc))


class DownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.lang = readJson("langs.json")
        self.lang = self.lang[self.lang["currentLanguage"]]

        self.setWindowTitle("YTDownloader")
        self.setFixedSize(910, 545)
        self.setWindowIcon(QIcon("Assets/Images/YTDownload.ico"))
        self.setStyleSheet("background-color: #222; color: #fff;")

        self.is_downloading = False
        self.is_searching = False

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        icon_label = QLabel()
        app_icon = QPixmap("Assets/Images/YTDownload.png").scaled(75, 75, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(app_icon)
        header_layout.addWidget(icon_label)

        title_label = QLabel("YTDownloader")
        title_label.setStyleSheet("color: #fff; font-size: 20px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        config_icon = QPixmap("Assets/Images/config.png").scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        config_button = QPushButton()
        config_button.setIcon(QIcon(config_icon))
        config_button.setFixedSize(50, 50)
        config_button.setStyleSheet("background-color: #222; border: none;")
        config_button.clicked.connect(lambda: config(self))
        header_layout.addWidget(config_button)

        main_layout.addLayout(header_layout)

        separator = QLabel("<hr style='color:#666'>")
        separator.setStyleSheet("color: #666;")
        main_layout.addWidget(separator)

        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(10)

        url_label = QLabel("URL:")
        url_label.setStyleSheet("color: #fff;")
        self.url_entry = QLineEdit()
        form_layout.addWidget(url_label, 0, 0)
        form_layout.addWidget(self.url_entry, 1, 0, 1, 6)

        self.search_button = QPushButton(self.lang["search"])
        self.search_button.clicked.connect(self.start_search)
        form_layout.addWidget(self.search_button, 1, 6)

        info_label = QLabel(f"{self.lang['videoDataLabel']}:")
        info_label.setStyleSheet("color: #fff; font-size: 14px;")
        form_layout.addWidget(info_label, 2, 0, 1, 3)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(350, 191)
        self.thumbnail_label.setStyleSheet("background-color: #444;")
        form_layout.addWidget(self.thumbnail_label, 3, 1, 3, 3)

        thumb_text = QLabel(f"{self.lang['thumbnailLabel']}")
        thumb_text.setAlignment(Qt.AlignCenter)
        thumb_text.setStyleSheet("color: #fff;")
        form_layout.addWidget(thumb_text, 6, 1, 1, 2)

        filename_label = QLabel(f"{self.lang['fileNameLabel']}:")
        filename_label.setStyleSheet("color: #fff;")
        self.filename_entry = QLineEdit()
        form_layout.addWidget(filename_label, 3, 4)
        form_layout.addWidget(self.filename_entry, 3, 5, 1, 3)

        format_label = QLabel(f"{self.lang['formatLabel']}:")
        format_label.setStyleSheet("color: #fff;")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["----VIDEO----", "MP4", "----AUDIO----", "MP3", "WAV", "OGG"])
        self.format_combo.setCurrentIndex(1)
        for disabled_index in (0, 2):
            item = self.format_combo.model().item(disabled_index)
            if item:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        form_layout.addWidget(format_label, 4, 4)
        form_layout.addWidget(self.format_combo, 4, 5, 1, 2)

        quality_label = QLabel(f"{self.lang['qualityLabel']}:")
        quality_label.setStyleSheet("color: #fff;")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["1080p", "720p", "480p", "360p", "240p", "144p"])
        self.quality_combo.setCurrentIndex(0)
        form_layout.addWidget(quality_label, 5, 4)
        form_layout.addWidget(self.quality_combo, 5, 5, 1, 2)

        self.duration_label = QLabel(f"{self.lang['estimatedDurationLabel']}: --")
        self.duration_label.setStyleSheet("color: #fff;")
        form_layout.addWidget(self.duration_label, 6, 4, 1, 2)

        self.weight_label = QLabel(f"{self.lang['estimatedFileSize']}: --")
        self.weight_label.setStyleSheet("color: #fff;")
        form_layout.addWidget(self.weight_label, 6, 5, 1, 2)

        form_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed), 7, 0)

        self.download_button = QPushButton(self.lang["downloadLabel"])
        self.download_button.setFixedHeight(40)
        self.download_button.clicked.connect(self.start_download)
        form_layout.addWidget(self.download_button, 7, 1, 1, 5)

        self.progressbar = QProgressBar()
        self.progressbar.setRange(0, 100)
        form_layout.addWidget(self.progressbar, 8, 0, 1, 7)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        self.thumbnail = None

    def update_action_states(self):
        self.search_button.setEnabled(not self.is_searching and not self.is_downloading)
        self.download_button.setEnabled(not self.is_downloading and not self.is_searching)

    def set_search_state(self, running: bool):
        self.is_searching = running
        self.search_button.setText(f"{self.lang['search']}..." if running else self.lang["search"])
        self.update_action_states()

    def set_download_state(self, running: bool):
        self.is_downloading = running
        self.download_button.setText(
            f"{self.lang['downloadLabel']}..." if running else self.lang["downloadLabel"]
        )
        self.update_action_states()

    def show_message(self, title: str, message: str, icon=QMessageBox.Information):
        QMessageBox(icon, title, message, parent=self).exec()

    def start_search(self):
        if self.is_searching:
            self.show_message(self.lang["search"], self.lang["searchInProgress"])
            return
        if self.is_downloading:
            self.show_message(self.lang["search"], self.lang["downloadInProgress"])
            return
        url = self.url_entry.text().strip()
        if not url:
            self.show_message(self.lang["search"], self.lang["infoURL"])
            return

        self.set_search_state(True)
        self.search_thread = QThread()
        self.metadata_worker = MetadataWorker(url)
        self.metadata_worker.moveToThread(self.search_thread)
        self.search_thread.started.connect(self.metadata_worker.run)
        self.metadata_worker.finished.connect(self.on_metadata_finished)
        self.metadata_worker.error.connect(self.on_metadata_error)
        self.metadata_worker.finished.connect(self.search_thread.quit)
        self.metadata_worker.error.connect(self.search_thread.quit)
        self.search_thread.finished.connect(self.search_thread.deleteLater)
        self.search_thread.start()

    def on_metadata_finished(self, result: dict):
        info_dict = result.get("info", {})
        thumbnail_data = result.get("thumbnail")

        self.filename_entry.setText(info_dict.get("title", "video"))

        duration = info_dict.get("duration", 0)
        filesize = info_dict.get("filesize_approx", 0)

        minutes, seconds = divmod(duration, 60)
        duration_formatted = f"{minutes:02}:{seconds:02}"
        self.duration_label.setText(f"{self.lang['estimatedDurationLabel']}: {duration_formatted}")

        if filesize:
            self.weight_label.setText(f"{self.lang['estimatedFileSize']}: {filesize / (1024 * 1024):.2f} MB")
        else:
            self.weight_label.setText(f"{self.lang['estimatedFileSize']}: {self.lang['notAvailable']}")

        if thumbnail_data:
            pixmap = QPixmap()
            pixmap.loadFromData(thumbnail_data)
            pixmap = pixmap.scaled(350, 191, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumbnail_label.setPixmap(pixmap)

        self.set_search_state(False)

    def on_metadata_error(self, error_message: str):
        self.show_message(self.lang["error"], f"{self.lang['error']}: {error_message}", QMessageBox.Critical)
        self.set_search_state(False)

    def start_download(self):
        if self.is_downloading:
            self.show_message(self.lang["downloadLabel"], self.lang["downloadInProgress2"])
            return

        if self.is_searching:
            self.show_message(self.lang["downloadLabel"], self.lang["searchInProgress"])
            return

        url = self.url_entry.text().strip()
        if not url:
            self.show_message(self.lang["downloadLabel"], self.lang["infoURL"])
            return

        filename = self.filename_entry.text().strip() or "video"
        selected_format = self.format_combo.currentText()
        selected_quality = self.quality_combo.currentText()

        if selected_format.startswith("-"):
            self.show_message(self.lang["error"], self.lang["formatLabel"], QMessageBox.Warning)
            return

        self.set_download_state(True)
        self.progressbar.setValue(0)

        self.download_thread = QThread()
        self.download_worker = DownloadWorker(url, filename, selected_format, selected_quality)
        self.download_worker.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.progress.connect(self.update_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.error.connect(self.download_thread.quit)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.start()

    def update_progress(self, value: float):
        self.progressbar.setValue(int(value))

    def on_download_finished(self):
        self.set_download_state(False)
        self.progressbar.setValue(0)
        self.show_message(self.lang["downloadLabel"], self.lang["downloadComplete"])

    def on_download_error(self, error_message: str):
        self.set_download_state(False)
        self.show_message(self.lang["error"], f"{self.lang['error']}: {error_message}", QMessageBox.Critical)


if __name__ == "__main__":
    original_path = TemporalPath()
    if not os.path.isfile("config.json"):
        predeterminedJson()

    app = QApplication([])
    window = DownloaderApp()
    window.show()
    app.exec()

    RestorePath(original_path)
