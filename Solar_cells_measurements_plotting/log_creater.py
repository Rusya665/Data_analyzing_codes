import time
import instruments
from datetime import datetime

from xlsx_plotter import PlotIV


class LogCreate(PlotIV):
    """
    A class for creating some logs. Inherits from PlotIV
    """
    def __init__(self, path_file: str, open_log=False):
        super().__init__(path_file)
        self.open_log = open_log
        self.log_folder = instruments.create_folder(self.path_file, 'Log/')
        self.log()
        print("\n", "--- %s seconds ---" % (time.time() - self.start_time))

    def log(self):
        today = f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
        log_path = f"{self.log_folder}Log for {self._indicator}, {today}.txt"
        with open(log_path, "w") as log:
            log.write(f"Log for {self._indicator}\n\n")
            log.write(f"Date: {today}\n\n")
            log.write(f'Location of the created xlsx doc: {self.xlsx_location}\n')
            log.write(f"Source folder: {self.path_file}\n")
            log.write(f'Source folder contained:\n')
            if self.data:
                for i in range(1, len(self.data) + 1):
                    log.write(f"{i}. {self.data[f'{i}']['File name']}\t"
                              f"{self.data[f'{i}']['Potentiostat']}\t"
                              f"{self.data[f'{i}']['Encoding']}\n")
            else:
                log.write('The given directory contained no applicable files\n')
            if self.skipped_files:
                log.write(f'\nIgnored files:\n')
                for skip_index, skip_file in enumerate(self.skipped_files, 1):
                    log.write(f'{skip_index}. {skip_file}\n')

            log.write(f'\nTotal analyzing and plotting time: \t{time.time() - self.start_time} sec')
        if self.open_log:
            instruments.open_file(log_path)
