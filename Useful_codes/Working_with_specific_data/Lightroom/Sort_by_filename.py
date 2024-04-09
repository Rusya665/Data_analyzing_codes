#  Sort already exported classic Adobe Lightroom images to a specific folder and change their names
import os
import re
from icecream import ic
import Instruments
import shutil
from pathlib import Path


"""Sorting 2024 Encapsulates"""
sample_number = ''
counter = 0
# path = r'C:\Users\runiza.TY2206042\OneDrive - O365 Turun yliopisto\Desktop\2023 Carbon dark storage/'
# path = r'C:\Users\runiza_admin\OneDrive - O365 Turun yliopisto\Desktop/new1'
one_drive_path = os.environ.get('OneDrive')
path = os.path.join(one_drive_path, 'IEDT-pictures', 'Imported')
if not path.endswith('/'):
    path = path + '/'
list_devices = ['EPOXY_1', 'EPOXY_2', 'EVA_1', 'EVA_2', 'EVA_3', 'EVA_4',
                'GEL_1', 'GEL_2', 'GLAS_1', 'GLAS_2', 'GORILLA_1', 'GORILLA_2', 'MARIN_1', 'MARIN_2',
                'OPPANOL_3', 'OPPANOL_4', 'PARAFFIN_1', 'PARAFFIN_2', 'SAUMA_1', 'SAUMA_2',
                'SILIKON_1', 'SILIKON_2', 'SURLYN_1', 'SURLYN_2', 'SURLYN_3', 'SURLYN_4',
                'SYLGARD_1', 'SYLGARD_2']
for file in os.listdir(path):
    if file.endswith('.jpg'):
        # Split the file name into its components
        parts = file.split('_')
        # The date is always the first component
        date = parts[0]
        try:
            # photo_session = full_name[1:2]
            name = parts[1] + "_" + parts[2][0]
            side = parts[2].split('0000')[-1].split('.jpg')[0]
            if name in list_devices:
                folder_name = name + "_" + side
                src = path + file
                destination = Instruments.create_folder(path, folder_name)
                dst = destination + file
                shutil.move(src, dst)
                ic(f'The file {file} is successfully moved to {dst}')

        except IndexError:
            pass
# Instruments.collect_files(path, delete_empty_folders=True)
