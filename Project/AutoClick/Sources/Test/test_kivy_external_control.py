import multiprocessing as mp
import time


class ControlProcess(mp.Process):
    def __init__(self, data_dict):
        super().__init__()
        self.data_dict = data_dict

    def run(self):
        while True:
            self.data_dict['counter'] += 1
            time.sleep(1)
