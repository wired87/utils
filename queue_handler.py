import queue


class QueueHandler:

    def __init__(self, q: queue.Queue or None =None):
        self.q = q or queue.Queue()

    def add_task(self, db_path, attrs, task_type: str = 'firebase_push'):
        """Fügt eine Firebase Push Aufgabe zur Queue hinzu."""
        task = {
            'type': task_type,
            'path': db_path,
            'data': attrs
        }
        print(f"Haupt-Thread: Füge Aufgabe zur Queue hinzu: {task['type']}")
        self.q.put(task)