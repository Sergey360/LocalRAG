import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_PATH = os.getenv("WATCH_PATH", "/app/files")
WORKSPACE_ID = os.getenv("WORKSPACE_ID", "1")
API_URL = os.getenv("ANYTHINGLLM_API", f"http://host.docker.internal:3001/api/workspaces/{WORKSPACE_ID}/reindex")

class ChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print(f"Изменение: {event.src_path}")
        try:
            r = requests.post(API_URL)
            print("Индекс обновлён")
        except Exception as e:
            print(f"Ошибка обновления индекса: {e}")

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(ChangeHandler(), path=WATCH_PATH, recursive=True)
    observer.start()
    print(f"Слежение за {WATCH_PATH}")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
