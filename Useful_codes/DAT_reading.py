import pandas as pd
import xlsxwriter
import time
import os


start_time = time.time()

path_to_files = 'path/to/your/folder'
suffix_name = '_new_name.xlsx'


def find_nm(dat_file):
    """
    Finds the row number of the "nm" string in a .dat file.

    :param dat_file: The path to the .dat file.
    :return: The row number of the "nm" string.
    """
    with open(dat_file) as f:
        for row, line in enumerate(f):
            if line.startswith('nm'):
                return row + 1


def main() -> None:
    """
    Converts .dat files to .xlsx files with specified sheet format.

    :return: None
    """
    for file in os.listdir(path_to_files):
        if file.endswith('.dat'):
            dat_file_name = os.path.join(path_to_files, file)
            print(dat_file_name)
            df = pd.read_csv(dat_file_name, sep=r'\t', header=None, skiprows=find_nm(dat_file_name), engine='python')
            df = df.drop(df.columns[0], axis=1)
            workbook = xlsxwriter.Workbook(dat_file_name.split(".dat")[0] + suffix_name,
                                           {'strings_to_numbers': True})
            worksheet = workbook.add_worksheet()
            worksheet.write_column('A1', df.iloc[:251, 0])
            for i in range(0, int(len(df.index) / 251)):
                worksheet.write_column(0, i + 1, df.iloc[i * 251:(i + 1) * 251, 2])
            workbook.close()
            time.sleep(.2)
            os.startfile(dat_file_name.split(".dat")[0] + suffix_name)
    print("\n", "--- %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    main()



