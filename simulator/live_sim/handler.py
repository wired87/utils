import json

from utils.logger import LOGGER


class LiveSimHandler:




    def __init__(self):
        pass




    async def receive(self, text_data=None, bytes_data=None):
        LOGGER.info(f"Received message from frontend: {text_data}")
        try:
            data = json.loads(text_data)
            data_type = data.get("type")  # assuming 'type' field for command
            command_details = data.get("payload")  # assuming 'payload' for command data

            if data_type == "stim":
                # Example: Put a 'stimulus' command with details into the queue
                self.command_queue.put({"command": "apply_stimulus", "details": command_details})
                LOGGER.info(f"Frontend command 'stimulus' added to queue.")
            elif data_type == "pause":
                self.command_queue.put({"command": "pause_simulation"})
                LOGGER.info(f"Frontend command 'pause' added to queue.")
            elif data_type == "resume":
                self.command_queue.put({"command": "resume_simulation"})
                LOGGER.info(f"Frontend command 'resume' added to queue.")
            elif data_type == "stop":
                self.command_queue.put({"command": "stop_simulation"})
                LOGGER.info(f"Frontend command 'stop' added to queue.")
            # Add more command types as needed
            else:
                LOGGER.warning(f"Unknown command type received: {data_type}")

        except json.JSONDecodeError:
            LOGGER.error(f"Failed to decode JSON from frontend: {text_data}")
        except Exception as e:
            LOGGER.error(f"Error processing received message: {e}")