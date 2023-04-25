import os.path
import pandas as pd
import instruments
import time


# Set pandas' console output width
# pd.set_option('display.max_rows', 500)
# pd.set_option('display.max_columns', 500)
# pd.set_option('display.width', 1000)


class ReadData:  # The main class for reading raw data
    """
    A class for reading and parsing raw data from potentiostats and also gathering some data for further Log filing,
    including:
        |  data_files - a list of file names accepted by the class
        |  skipped_files - a list of inapplicable files
        |
    Dict data with the following keys:
        |  'File name' - file names
        |  'IV' - ready-to-use PandasDataframe of IV data
        |  'Potentiostat' - potentiostats names being used to collect given IV data
        |  'Encoding' - used encodings (some raw dara require different encoding to be read)
    """

    def __init__(self, path_file: str, raw_files=None):
        self.start_time = time.time()
        if not path_file.endswith('/'):  # Adding the '/' at the end of the given path if not there
            path_file = path_file + '/'

        self.data_files = []  # Check this line
        self.skipped_files = []
        self.data = {}
        self.path_file = path_file
        self.raw_files = raw_files
        if not raw_files:
            self.raw_files = self.check_files()

        self.dict_filling()

    def dict_filling(self):
        for ind, file in enumerate(self.raw_files, 1):
            encoding = self.potentiostat_check(os.path.join(self.path_file, file))[1]
            self.data[f'{ind}'] = {}  # Create an empty dict with the index as dict name
            self.data[f'{ind}'][f'File name'] = file
            df = self.read_file(os.path.join(self.path_file, file), encoding)
            self.data[f'{ind}'][f'IV'] = df
            self.data[f'{ind}'][f'Potentiostat'] = self.potentiostat_check(os.path.join(self.path_file, file))[2]
            self.data[f'{ind}'][f'Encoding'] = encoding
            self.data[f'{ind}'][f'Axis crossing'] = {}
            self.data[f'{ind}'][f'Axis crossing']['I'] = instruments.axis_crossing(df, 'I')
            self.data[f'{ind}'][f'Axis crossing']['V'] = instruments.axis_crossing(df, 'V')

    def check_files(self):
        """
        Sort potentiostat files by file extensions and potentiostat.check method
        :return: A list with applicable files
        """
        for file in os.listdir(self.path_file):
            if not file.startswith('Log') and file.lower().endswith(('.txt', '.csv', '.dta')):
                if self.potentiostat_check(os.path.join(self.path_file, file))[0]:
                    self.data_files.append(file)
        return self.data_files

    def potentiostat_check(self, file):
        """
        Raw-data-checking method.
        In future this method may return specific row-index for specific raw-date type
        Check this out
        https://youtu.be/tmeKsb2Fras?t=247
        :param file: A file with raw data created by a potentiostat
        :return: |  True -> if file contains applicable data
                 |  encoding_flag -> encoding being used
                 |  str -> potentiostat's name
        """
        try:
            encode_flag = 'utf-8'
            with open(file, 'r', encoding=encode_flag) as f:  # Encoding for Gamry and SMU
                g = f.read().splitlines()
        except UnicodeDecodeError:
            encode_flag = 'utf-16'
            with open(file, 'r', encoding=encode_flag) as f:  # Special encoding for PalmSens4
                g = f.read().splitlines()
        # except UnicodeDecodeError:
        #     encode_flag = 'utf-32'
        #     with open(file, 'r', encoding=encode_flag) as f:
        #         g = f.read().splitlines()
        if "CURVE1\tTABLE" in g:  # "Gamry"
            return True, encode_flag, "Gamry"
        elif "Cyclic Voltammetry: CV i vs E" in g:  # "PalmSens4"
            return True, encode_flag, "PalmSens4"
        elif '[0, 0, 0]' in g:  # "SMU"
            return True, encode_flag, "SMU"
        else:  # Skip not applicable files
            self.skipped_files.append(file)
            return False, None

    @classmethod
    def read_file(cls, file, encoding: str):
        """
        A "class" method for parsing filtered potentiostats IV data
        :param file: Filename to be parsed
        :param encoding: File's encoding
        :return: A PandasDataframe with two columns 'I' and 'V', standing for current in mA and voltage in V
         respectively
        """
        if file.lower().endswith('.txt'):  # The source measurement unit case
            df = pd.read_csv(file, sep='\t', engine='python', header=None, encoding=encoding,
                             names=['V', 'I'], skiprows=2)
            df.name = file
            return instruments.columns_swap(df)

        if file.lower().endswith('.dta'):  # The Gamry case
            df = pd.read_csv(file, engine='python', header=None, skiprows=65, encoding=encoding, sep='\t')
            """
            A special note for future me. If the skiprows=65 is not gonna work anymore, add a method to actually 
            check the .DTA file before parsing. Love you. You are the best.
            """
            df.drop(df.columns[[0, 2, 5, 6, 7, 8, 9, 10]], axis=1, inplace=True)  # Drop unnecessary columns. Check the
            # Q3 from scratch.txt
            df.columns = ['Pt', 'V', 'I']  # Keep the "Pt" column for further filtering
            df = df[df["Pt"].str.contains(r'^\d+$')].reset_index()  # Filter the df by "Pt" column
            df.drop('Pt', axis=1, inplace=True)  # Drop that column
            df.drop('index', axis=1, inplace=True)  # Finally, drop a column created by reset_index()
            df.name = file
            return instruments.columns_swap(df)

        if file.lower().endswith('.csv'):  # The PalmSens 4 case
            df = pd.read_csv(file, engine='python', header=None, encoding=encoding,
                             skiprows=6, keep_default_na=True, na_filter=False, names=['V', 'I'])
            df = df[df['I'].notna()]  # Picking only the data which is not "Nan" <- dropping the last raw
            df['I'] = df['I'].divide(10 ** 6)  # Uniforming the result. PalmSens saves the current in µA
            df.name = file
            return instruments.columns_swap(df)
