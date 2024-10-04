import os
import unicodedata
import rumps
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from PyQt6.QtWidgets import QApplication, QFileDialog
import sys

def normalize_path(path: str):
    directory, name = os.path.split(path)
    normalized_name = unicodedata.normalize('NFC', name)
    if len(name) == len(normalized_name):
        return
    normalized_path = os.path.join(directory, normalized_name)
    os.rename(path, normalized_path)

def normalize_filenames_in_directory(directory):
    for dir_path, child_dir_names, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dir_path, filename)
            normalize_path(str(file_path))
        for dir_name in child_dir_names:
            child_dir_path = os.path.join(dir_path, dir_name)
            normalize_path(str(child_dir_path))

class Watcher:
    observer: Observer | None = None
    timer: rumps.Timer | None = None

    def __init__(self, directory_to_watch):
        self.directory_to_watch = directory_to_watch

    def run(self):
        event_handler = Handler()
        self.observer and self.observer.stop()
        self.observer = Observer()
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()

        def _maintainer(timer: rumps.Timer):
            if self.observer.is_alive():
                self.observer.join(1)

        self.timer = rumps.Timer(_maintainer, 1)
        self.timer.start()

    def stop(self):
        try:
            self.observer.stop()
            self.observer.join()
        except:
            pass
        finally:
            self.timer and self.timer.stop()

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.event_type in ['created', 'modified']:
            normalize_filenames_in_directory(event.src_path)
        elif event.event_type == 'moved':
            normalize_filenames_in_directory(event.dest_path)

def select_folder():
    app = QApplication(sys.argv)
    folder_path = QFileDialog.getExistingDirectory(None, "한글 자소분리를 방지할 폴더를 선택해주세요")
    app.quit()
    return folder_path

class JasoRumpsApp(rumps.App):
    def __init__(self, *args, **kwargs):
        icon_path = "icon.icns"
        super().__init__(name="자소", icon=icon_path, quit_button=None)
        self.watcher: Watcher | None = None
        self.icon_path = icon_path

    @rumps.clicked("자동변환 시작")
    def _start(self, _):
        try:
            if self.watcher:
                self.watcher.stop()
                rumps.alert(message="이미 실행 중이던 작업을 중단했습니다.", icon_path=self.icon_path)
            
            directory_path = select_folder()
            if not directory_path:
                rumps.alert("폴더가 선택되지 않았습니다.", icon_path=self.icon_path)
            elif not os.path.isdir(directory_path):
                rumps.alert("유효하지 않은 폴더입니다.", icon_path=self.icon_path)
            else:
                rumps.alert("폴더가 설정되었습니다. 이제부터 해당 폴더에서 자동으로 한글의 자소분리가 방지됩니다.", icon_path=self.icon_path)
                self.watcher = Watcher(directory_path)
                self.watcher.run()
        except Exception as e:
            rumps.alert(f"오류: {str(e)}")

    @rumps.clicked("종료")
    def _quit(self, _):
        self.watcher and self.watcher.stop()
        rumps.quit_application()

if __name__ == "__main__":
    app = JasoRumpsApp()
    app.run()
