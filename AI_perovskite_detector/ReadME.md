# Perovskite Crystal Corner Detection

This folder contains codes to train and evaluate a convolutional neural network (CNN) for detecting the corners of perovskite crystals in images. Perovskite materials are used in solar cells, and their unique crystal structure allows them to efficiently absorb sunlight and convert it into electricity. Analyzing the crystal structure is important for understanding the performance of the solar cells.

## Table of Contents
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Usage

1. Prepare your dataset of images containing perovskite crystals and corresponding corner annotations.

2. Train the model using the following command, specifying the path to your dataset:
python train.py --data_path /path/to/your/dataset

3. Evaluate the trained model on a test set using the following command, specifying the path to your test dataset:
python evaluate.py --data_path /path/to/your/test-dataset

4. To use the trained model for corner detection in new images, use the following command, specifying the path to the image:
python predict.py --image_path /path/to/your/image


## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT License](https://choosealicense.com/licenses/mit/)
