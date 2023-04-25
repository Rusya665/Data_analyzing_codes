import math
import re
import time
from datetime import datetime
from pathlib import Path

# import cv2
import numpy as np
import pandas as pd
from cv2 import cv2
from imutils import perspective
from tqdm import tqdm, trange

from Instruments import *


class RemoveBackgroundMakeFilm:
    def __init__(self, parent_path: str, cycles=3, film='y', open_logs=False, frame_rate=1):
        if not parent_path.endswith('/'):
            parent_path = parent_path + '/'
        self.extension = '.jpg'
        self.extension_out = '.png'  # Keep output extension as .png to apply alpha channel
        self.frame_rate = frame_rate
        self.path = self.check_path(parent_path)
        self.folder = None
        self.cycles = cycles  # Cycles are NOT specified folder specifically
        self.sizes_pd = None
        self.film = film
        self.log_files = []
        pbar_main = tqdm(self.path, desc=f'Working in {os.path.basename(os.path.normpath(parent_path))}',
                         position=0, ncols=100, unit='directory', colour='#ffc25c')  # unit_scale=True)
        for folder in pbar_main:
            # ic(folder)
            self.start_time = time.time()
            self.folder = folder + '/'
            self.path_out = self.folder + "Processed/"
            self.samples, self.pre_processed, self.sizes, self.center, self.no_background, self.cropped, \
                self.error_list = [], [], [], [], [], [], []
            self.sample_name = os.path.basename(os.path.normpath(self.folder))
            pbar_main.set_description(f'Working on {self.sample_name}')
            self.video_name = f'Ageing {self.sample_name}.avi'
            for file in os.listdir(self.folder):
                if file.endswith(self.extension):
                    self.samples.append(file)
            self.time_line = self.timeline_detector()
            self.file_sorting()
            self.erase_background()
            self.processing_images()
            self.sizes_pd = pd.DataFrame(self.sizes)
            self.crop_images()
            self.executed_time = time.time()
            if film == 'y':
                self.create_video()
            self.log_file()
        if open_logs:
            for log in self.log_files:
                open_file(log)
                time.sleep(.1)

    def log_file(self):
        """
        Generate a log file contain some useful information for each device.
        :return: None
        """
        today = f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
        log_name = f"{self.path_out}Log {self.sample_name} {today}.txt"
        self.log_files.append(log_name)
        with open(log_name, "w") as log:
            log.write(f"Log for {self.sample_name}\n\n")
            log.write(f"Date: {today}\n\n")
            log.write(f"Source folder: {self.folder}\n")
            log.write(f'Initial images (w, h, ch) turned to (w, h, ch):\n')
            skipped_img_index = []
            for i, j in enumerate(self.samples):
                try:
                    max_time_len = len(str(self.time_line.iat[-1, 0]))
                    final_image_name = (max_time_len - len(str(self.time_line.iat[i, 0]))) * ' ' \
                                       + str(self.time_line.iat[i, 0])  # Add spaces from the left to align names
                    log.write(f"{i + 1}. {j} {self.img_shape(self.folder + j)}"
                              f"\t{final_image_name}{self.extension_out} {self.img_shape(self.cropped[i])}\n")
                except AttributeError:
                    log.write(f'{i + 1}. Empty image\t{final_image_name}{self.extension_out}\n')
                    skipped_img_index.append(i + 1)
            if skipped_img_index:
                log.write(f'\nErrors\n')
                for w in range(len(skipped_img_index)):
                    log.write(f'Skipped images: {skipped_img_index[w]}. {self.error_list[w]}\n')
            log.write(f'\nParameters being used:\n')
            log.write(f'Number of background erasing cycles: {self.cycles}\n')
            log.write(f'Did film was created: {self.film}\n')
            if self.film == 'y':
                log.write(f'Ageing video: {self.video_name}\n')
                log.write(f'Frame rate: {self.frame_rate}\n')
                log.write(f'Frame size: {self.img_shape(self.cropped[0])[0:2]}\n')
            log.write(f'\nImages processing time: \t{self.executed_time - self.start_time} sec'
                      f'\nTotal time: \t{time.time() - self.start_time} sec\n')

    def img_shape(self, img=None):
        """
        Getting dimensions and channels of the first cropped image
        :return: height, width, channels
        """
        if not img:
            img = self.cropped[0]
        img_hwc = cv2.imread(img)
        height, width, channels = img_hwc.shape
        return height, width, channels

    def create_video(self):
        """
        Create a video based on processed images
        :return: None
        """
        # frame = cv2.imread(cropped)
        height, width, _ = self.img_shape()
        video = cv2.VideoWriter(self.path_out + self.video_name, 0, self.frame_rate, (width, height))

        for shoot in trange(len(self.cropped), desc='Filming', ncols=100, unit='img', colour='red', position=1,
                            leave=None):
            try:
                img_1 = cv2.imread(self.cropped[shoot])
                resized = cv2.resize(img_1, (width, height))
                video.write(resized)
            except cv2.error:
                pass
        video.release()

    def crop_images(self):
        """
        Crop images and save in the new folder
        :return: None
        """
        pbar2 = tqdm(range(len(self.samples)), desc='Cropping images and saving', unit=' image processing',
                     ncols=100, colour='green', leave=None, position=1)
        for pic in pbar2:
            final_image = self.cropping_an_image(self.sizes_pd, self.center[pic], self.pre_processed[pic])
            # final_image = pre_processed[pic]
            if final_image is None:
                raise ValueError('A very specific bad thing happened.')
            out_img = create_folder(self.folder, "Processed") + str(self.time_line.iat[pic, 0]) + self.extension_out
            self.cropped.append(out_img)
            try:
                cv2.imwrite(out_img, final_image)
            except cv2.error:
                print('cv2 error')
                self.error_list.append(str(self.time_line.iat[pic, 0]) + self.extension_out)
            pbar2.set_description(f'Cropping and saving image {pic + 1}')

    @staticmethod
    def cropping_an_image(shapes, c, image_rotated):  # Final cropping
        """
        Crop preprocessed image
        :param shapes: Cropping shape
        :param c: Cropping center
        :param image_rotated: Preprocessed image (rotated if needed)
        :return: Cropped image
        """
        x_min_0 = shapes[0].min()
        x_max_0 = shapes[1].max()
        y_min_0 = shapes[2].min()
        y_max_0 = shapes[3].max()
        correction_x = (x_max_0 - x_min_0) / 2
        correction_y = (y_max_0 - y_min_0) / 2
        # correction_x = 0
        # correction_y = 0
        x_min = c[0] - correction_x
        x_max = c[0] + correction_x
        y_min = c[1] - correction_y
        y_max = c[1] + correction_y
        some_space = 0
        crop_img = image_rotated[round(y_min) - some_space:round(y_max) + some_space,
                   round(x_min) - some_space:round(x_max) + some_space]
        # crop_img = image_rotated[round(y_min_0) - some_space:round(y_max_0) + some_space,
        #            round(x_min_0) - some_space:round(x_max_0) + some_space]
        return crop_img

    def processing_images(self):
        """
        Preprocess pictures, fill the self.pre_processed, self.sizes, self.center lists
        :return: None
        """
        pbar1 = tqdm(range(len(self.samples)), desc='Preprocessing images', unit=' image processing', ncols=100,
                     colour='YELLOW', position=1, leave=None)
        for index in pbar1:
            image = self.no_background[index]
            processing = self.an_image_processing(image)[0]
            if processing is None:
                raise ValueError('A very specific bad thing happened.')
            self.pre_processed.append(processing)
            self.sizes.append(self.set_cropping_shape(self.an_image_processing(image)[1],
                                                      self.an_image_processing(image)[2]))
            self.center.append(self.an_image_processing(image)[2])
            pbar1.set_description(f'Preprocessing image {index + 1}')

    def an_image_processing(self, photo):
        """
        Preprocessing of a single image
        :param photo: Picture to be preprocessed
        :return: rotated image, rotation matrix, rotation center
        """
        photo0 = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)  # If [Start]FindContours supports only CV_8UC1 images when
        # mode != CV_RETR_FLOODFILL otherwise supports CV_32SC1 images only in function 'cvStartFindContours_Impl'
        contours_in, _ = cv2.findContours(photo0, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        objects_contours = []
        for cnt_in in contours_in:
            area = cv2.contourArea(cnt_in)
            if area > 100000:
                objects_contours.append(cnt_in)
        rect = cv2.minAreaRect(objects_contours[0])
        (x, y), _, _ = rect
        coord = cv2.boxPoints(rect)
        coord = np.int0(coord)
        height, width = photo.shape[:2]
        box = self.pick_coordinates(coord)
        matrix = cv2.getRotationMatrix2D((int(x - 1), int(y - 1)), self.angle_between2(box[-1], box[0]), 1.0)
        ones = np.ones(shape=(len(coord), 1))
        points_ones = np.hstack([coord, ones])
        aaa = matrix.dot(points_ones.T).T
        rotated_image = cv2.warpAffine(photo, matrix, (width, height))
        return rotated_image, aaa, (int(x - 1), int(y - 1))

    @staticmethod
    def set_cropping_shape(coordinate_matrix, cen):  # Set cropping shape
        """
        Determine the cropping shape
        :param coordinate_matrix: numpy matrix for cv2.cropping
        :param cen: a cropping center
        :return: 4 cropping coordinates
        """
        x_min_0, y_min_0 = coordinate_matrix.min(axis=0)
        x_max_0, y_max_0 = coordinate_matrix.max(axis=0)
        # Corrections might be overkill, because they are also applying in cropping_image
        correction_x = (x_max_0 - x_min_0) / 2
        correction_y = (y_max_0 - y_min_0) / 2
        # correction_x = 0
        # correction_y = 0
        x_min = cen[0] - correction_x
        x_max = cen[0] + correction_x
        y_min = cen[1] - correction_y
        y_max = cen[1] + correction_y
        return x_min, x_max, y_min, y_max

    @staticmethod
    def angle_between2(p1, p2):  # Angle to rotate image
        """
        Find an angel between two points representing the lowest rectangle side. In other words, find an angle between
        two rotated rectangles
        :param p1: first point, x1 < x2
        :param p2: second point, x2 > x1
        :return: angle
        """
        return np.degrees(math.atan2(p2[-1] - p1[-1], p2[0] - p1[0]))

    @staticmethod
    def pick_coordinates(initial_coordinates):
        """
        Based on given coordinates return 2 lower ones
        :param initial_coordinates: given coordinates
        :return: two lower ones
        """
        points_sorted = perspective.order_points(initial_coordinates)
        lower_coord = points_sorted[-2:]
        return lower_coord

    def erase_background(self):
        """
        Deleting background in all pictures in the given path. If number of cycles more than 1, applying a recursion
        :return: list with erased background pictures opened in cv2
        """
        for cycle in tqdm(range(self.cycles), desc='Erasing cycles', position=1, ncols=100, unit='img',
                          colour='#FF7518', leave=None):
            for initial_photo in trange(len(self.samples), desc=f'Cycle {cycle + 1} erasing background', position=2,
                                        ncols=100, unit='img', leave=None, colour='blue'):
                if len(self.no_background) == len(self.samples):  # If cycles > 1
                    clear_img = delete_background(self.no_background[initial_photo])
                    self.no_background[initial_photo] = clear_img
                    if clear_img is None:
                        raise ValueError('A very specific bad thing happened.')
                if len(self.no_background) < len(self.samples):  # For the first cycle
                    clear_img = delete_background(self.folder + self.samples[initial_photo])
                    self.no_background.append(clear_img)
                    if clear_img is None:
                        raise ValueError('A very specific bad thing happened.')

    def timeline_detector(self):
        """
        Detect a given Timeline
        :return: Pandas DataFrame with hours
        """
        flag = '.xlsx'  # Here is the extension for timeline file
        time_line_directory = str(os.path.dirname(os.path.dirname(self.path[0] + '/'))) + '/'
        if time_line_directory.endswith('Perovskite/'):
            name_k = int(self.sample_name.split('-')[0])
            if name_k == 5 or name_k == 6 or name_k == 11:  # Specified timeline for specific case (Perovskite case)
                flag = '1.xlsx'
                print('Specific Timeline file has been used')
        timeline = Path(time_line_directory + 'Timeline' + flag)  # Specify here the file with timepoints
        if timeline.is_file():
            df = pd.read_excel(timeline, header=None, na_values=["NA"])
            if len(df.index) < len(self.samples):
                raise ValueError(f'Check the {timeline}. It seems like not enough timepoints are given')
            return np.ceil(df).astype(int)
        else:
            raise ValueError(f'Check the {timeline}')

    def file_sorting(self):
        """
        If the images are not starting with the yyyy-mm-dd format, i.e. they are not renamed with the
        Lightroom_naming_changing, apply manual sorting. Cases like [1, 2, 10, 20] are taken into account
        :return: None
        """
        img_name = self.samples[0].split('_')[0]
        if not is_date(img_name, True):
            print(self.samples[0])
            print('Non-date case detected. ReSorting applied')
            self.samples.sort(key=lambda f: int(re.sub("\D", '', f)))

    def check_path(self, path):
        """
        Check the given path
        :param path: the path to a folder
        :return: list with folder(s) containing pictures with the specified extension
        """
        folders = []
        for dir_path, dir_names, files in os.walk(path):
            for file in files:
                if file.endswith(self.extension):
                    if dir_path not in folders:
                        folders.append(dir_path)
        if folders:
            if path in folders:
                folders.remove(path)
        if not folders:
            folders.append(path)
        return folders


if __name__ == '__main__':
    start_time = time.time()
    path_to = "path/to/your/folder"
    RemoveBackgroundMakeFilm(path_to, cycles=1, open_logs=True)
    print("\n", "--- %s seconds ---" % (time.time() - start_time))
