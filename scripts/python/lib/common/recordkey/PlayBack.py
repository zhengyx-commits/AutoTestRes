import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.common.system.ADB import ADB
from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from tests.OTT_Hybrid.MULTI import Common_Playcontrol_Case

playerCheck = PlayerCheck_Iptv()
common_case = Common_Playcontrol_Case()


class PlayBack(ADB):
    def __init__(self):
        super().__init__()
        self.test_failed = False
        self.is_checking = False

    def process_events(self, json_file_path):
        with open(json_file_path, 'r') as file:
            events = json.load(file)

        last_timestamp = None
        self.is_checking = True
        futures = []

        with ThreadPoolExecutor(max_workers=12) as executor:
            for i, event in enumerate(events):
                current_timestamp = float(event["timestamp"])
                if last_timestamp is not None:
                    delay = current_timestamp - last_timestamp
                    time.sleep(delay)
                last_timestamp = current_timestamp

                check_type = event.get("check")
                if check_type:
                    if i + 1 < len(events):
                        next_event_timestamp = float(events[i + 1]["timestamp"])
                        next_delay = min(next_event_timestamp - current_timestamp, 35)
                    else:
                        next_delay = 35

                    if check_type == "play":
                        futures.append(executor.submit(self.check_play, next_delay - 5))
                    elif check_type == "seek":
                        logging.info("Start to check seek.")
                        futures.append(executor.submit(self.check_seek))
                        if next_delay > 10:
                            futures.append(executor.submit(self.check_play, next_delay - 5))
                        else:
                            logging.info("Time is too short to check play.")
                    elif check_type == "pause":
                        logging.info("Start to check pause.")
                        futures.append(executor.submit(self.check_pause))
                        logging.info("Check pause ended.")
                    elif check_type == "resume":
                        logging.info("Start to check resume.")
                        futures.append(executor.submit(self.check_resume))
                        if next_delay > 10:
                            futures.append(executor.submit(self.check_play, next_delay - 5))
                        else:
                            logging.info("Time is too short to check play.")
                        logging.info("Check resume ended.")
                else:
                    self.playback_recorded_key(event)

            for future in as_completed(futures):
                try:
                    result = future.result()
                except AssertionError as e:
                    self.test_failed = True
                    logging.error(str(e))

        self.is_checking = False
        if self.test_failed:
            raise AssertionError("One or more checks failed during playback.")
        logging.info(f'Playback {json_file_path} ended.')

    def check_play(self, duration):
        logging.info(f'Start to check play for {duration}s.')
        assert playerCheck.run_check_main_thread(duration), "play failed"
        logging.info("Check play ended.")
        return True

    def check_seek(self):
        result = playerCheck.kt_check_seek()
        assert result, "seek failed"
        logging.info("Check seek ended.")
        return True

    def check_pause(self):
        result = playerCheck.kt_check_pause()
        assert result, "pause failed"
        logging.info("Check pause ended.")
        return True

    def check_resume(self):
        result = playerCheck.kt_check_resume()
        assert result, "resume failed"
        logging.info("Check resume ended.")
        return True

    def playback_recorded_key(self, event):
        device_name = event["device"]
        key_value_decimal = int(event["key_value"], 16)
        key_state = int(event["key_state"])
        send_event_cmd = f'sendevent {device_name} 1 {key_value_decimal} {key_state}; sendevent {device_name} 0 0 0'
        self.run_shell_cmd(send_event_cmd)
        logging.info('cmd: %s', send_event_cmd)

