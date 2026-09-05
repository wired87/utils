import time
import threading


class MillisecondTimer:
    def __init__(self):
        self.start_time = 0
        self.elapsed_time = 0
        self.running = False

    def start(self):
        if not self.running:
            self.running = True
            # Subtract elapsed_time to allow resuming from pause
            self.start_time = time.perf_counter() - self.elapsed_time
            threading.Thread(target=self._update_display, daemon=True).start()

    def stop(self):
        if self.running:
            self.running = False
            self.elapsed_time = time.perf_counter() - self.start_time

    def get_elapsed_ms(self):
        if self.running:
            return (time.perf_counter() - self.start_time) * 1000
        return self.elapsed_time * 1000

    def _update_display(self):
        while self.running:
            self.elapsed_time = time.perf_counter() - self.start_time
            minutes, remainder = divmod(self.elapsed_time, 60)
            seconds, milliseconds = divmod(remainder, 1)
            ms = int(milliseconds * 1000)

            # Print over the same line in terminal
            print(f"\rTime: {int(minutes):02d}:{int(seconds):02d}.{ms:03d}  ", end="")
            time.sleep(0.01)  # Updates roughly every 10ms


def main():
    timer = MillisecondTimer()

    input("Press ENTER to START...")
    timer.start()

    input()  # Wait for user input to stop
    timer.stop()
    print("\nPaused.")

    input("Press ENTER to EXIT...")


if __name__ == "__main__":
    main()