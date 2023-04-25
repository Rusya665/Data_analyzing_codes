import json
import os
import time
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image, ImageDraw
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from tqdm import tqdm


class PerovskiteDataset(Dataset):
    """
    A PyTorch Dataset class for the Perovskite dataset, which provides a convenient way to load and preprocess images
    and their corresponding coordinates for training or testing a model.
    """

    def __init__(self, excel_file, image_folder, transform=None):
        """
        Initializes the PerovskiteDataset with the given Excel file, image folder, and optional transform.

        :param excel_file: Path to the Excel file containing image filenames and corresponding coordinates.
        :param image_folder: Path to the folder containing the images.
        :param transform: Optional transform to be applied on the images.
        """

        self.data = pd.read_excel(excel_file)
        self.image_folder = image_folder
        self.transform = transform

    def __len__(self):
        """
        Returns the length of the dataset, i.e., the number of images.

        :return: The number of images in the dataset.
        :rtype: int
        """

        return len(self.data)

    def __getitem__(self, idx):
        """
        Retrieves the image and its corresponding coordinates at the given index.

        :param idx: The index of the image and coordinates to be retrieved.
        :return: A tuple containing the image (PIL.Image.Image) and its coordinates (numpy.ndarray).
        """
        if torch.is_tensor(idx):
            idx = idx.tolist()
        row = self.data.iloc[idx]
        img_path = os.path.join(self.image_folder, row.iloc[0])
        image = Image.open(img_path).convert("RGB")
        coordinates = np.array(row[1:], dtype=np.float32)
        if self.transform:
            image = self.transform(image)
        return image, coordinates


class ConvNet(nn.Module):
    """
    A PyTorch Convolutional Neural Network class for the Perovskite dataset, which is designed to predict the
    coordinates from input images. The architecture uses adaptive pooling layers with fixed output sizes of
    (128, 128), (64, 64), and (32, 32) for layer1, layer2, and layer3, respectively.

    This model can handle input images of different sizes without requiring resizing during preprocessing.
    """

    def __init__(self):
        super(ConvNet, self).__init__()
        self.layer1 = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.AdaptiveMaxPool2d((128, 128)),
            nn.Dropout(p=0.5)
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveMaxPool2d((64, 64)),
            nn.Dropout(p=0.5)
        )
        self.layer3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveMaxPool2d((32, 32)),
            nn.Dropout(p=0.5)
        )
        self.fc1 = nn.Linear(128 * 32 * 32, 1024)
        self.fc2 = nn.Linear(1024, 8)

    def forward(self, x):
        """
        Defines the forward pass of the ConvNet, which applies the layers sequentially and returns the output
        coordinates.

        :param x: The input tensor, representing a batch of images.
        :type x: torch.Tensor
        :return: The output tensor, representing the predicted coordinates.
        :rtype: torch.Tensor
        """
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.fc2(x)
        return x


class PerovskiteTrainer:
    """
    A class for training a ConvNet model on the Perovskite dataset.
    """

    def __init__(self, image_folder, excel_file, model_folder, batch_size=1, learning_rate=0.001, num_epochs=30,
                 weight_decay=1e-4, patience=5):
        """
        Initializes the PerovskiteTrainer with the specified parameters.

        :param image_folder: Path to the folder containing the images.
        :param excel_file: Path to the Excel file with the dataset information.
        :param model_folder: Path to the folder where the trained model will be saved.
        :param batch_size: The batch size for training (default is 1).
        :param learning_rate: The learning rate for the optimizer (default is 0.001).
        :param num_epochs: The number of training epochs (default is 30).
        """
        self.clip_value = 1.0  # You can experiment with different clip values
        self.image_folder = image_folder
        self.weight_decay = weight_decay
        self.patience = patience
        self.excel_file = excel_file
        self.model_folder = model_folder
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        transform = transforms.Compose([transforms.ToTensor()])
        self.dataset = PerovskiteDataset(self.excel_file, self.image_folder, transform)
        self.train_loader = DataLoader(self.dataset, batch_size=self.batch_size, shuffle=True, num_workers=0)
        self.model = ConvNet().to(self.device)
        self.criterion = nn.MSELoss()
        # self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        # self.optimizer = optim.SGD(self.model.parameters(), lr=self.learning_rate, momentum=0.9, weight_decay=1e-5)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)

    def train(self):
        """
        Trains the model for one epoch and returns the average loss.

        :return: The average training loss for the epoch.
        """
        self.model.train()
        running_loss = 0.0
        progress_bar = tqdm(enumerate(self.train_loader), desc="Training", total=len(self.train_loader), leave=False)
        for batch_idx, (images, coordinates) in progress_bar:
            images = images.to(self.device)
            coordinates = coordinates.view(-1, 8).to(self.device)
            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, coordinates)
            loss.backward()
            nn.utils.clip_grad_norm_(self.model.parameters(), self.clip_value)  # Apply gradient clipping
            self.optimizer.step()
            running_loss += loss.item()
            progress_bar.set_postfix(loss=loss.item())
        return running_loss / len(self.train_loader)

    def save_logs(self, model_name, epoch_losses_durations, early_stopping_triggered):
        """
        Saves the logs for the trained model to a file.
        :param epoch_losses_durations: Details of each epoch, loss and its duration
        :param model_name: The name of the model file.
        :param early_stopping_triggered: Add flag if early_stopping_triggered
        :return: None
        """
        model_info = {
            "model_name": model_name,
            "num_epochs": self.num_epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "model_layers": [],
            "epoch_losses_durations": epoch_losses_durations,
            "early_stopping_triggered": early_stopping_triggered,
            "total time": f'{time.time() - start_time} sec'
        }
        for i, layer in enumerate(self.model.modules()):
            if i != 0:
                model_info["model_layers"].append(str(layer))
        log_file_path = os.path.join(self.model_folder, f"log_for_{model_name}.txt")
        with open(log_file_path, "w") as log_file:
            log_file.write(json.dumps(model_info, indent=4))

    def save_model(self, model_name):
        """
        Saves the trained model to the specified model file.

        :param model_name: The name of the model file.
        :return: None
        """
        model_path = os.path.join(self.model_folder, model_name)
        torch.save(self.model.state_dict(), model_path)
        print(f"Model saved as {model_name}")

    def find_next_model_name(self):
        """
        Finds the next available model file name.

        :return: The next available model file name.
        """
        counter = 1
        model_name = "model.pth"
        model_path = os.path.join(self.model_folder, model_name)
        while os.path.isfile(model_path):
            counter += 1
            model_name = f"model-{counter}.pth"
            model_path = os.path.join(self.model_folder, model_name)
        return model_name

    def run(self):
        """
        Runs the training process for the specified number of epochs and saves the trained model.
        :return: None
        """

        best_loss = float('inf')
        epochs_without_improvement = 0
        epoch_losses_durations = []
        early_stopping_triggered = False

        for epoch in range(self.num_epochs):
            epoch_time = time.time()
            train_loss = self.train()
            duration = time.time() - epoch_time
            print(f"Epoch [{epoch + 1}/{self.num_epochs}], Loss: {train_loss:.4f}, duration: {duration:.3f} sec")
            epoch_losses_durations.append({"epoch": epoch + 1, "loss": train_loss, "duration": duration})

            # Early stopping
            if train_loss < best_loss:
                best_loss = train_loss
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
                if epochs_without_improvement >= self.patience:
                    print("Early stopping triggered")
                    early_stopping_triggered = True
                    break

        model_name = self.find_next_model_name()
        self.save_model(model_name)
        self.save_logs(model_name, epoch_losses_durations, early_stopping_triggered)


class PerovskiteGUI:
    """
    A class to create a graphical user interface for the PerovskiteTester.
    """

    def __init__(self, tester):
        """
        Initializes the PerovskiteGUI with a PerovskiteTester instance.

        :param tester: The PerovskiteTester instance for testing models.
        """
        self.tester = tester
        self.window = tk.Tk()
        self.window.title("Perovskite Corner Detection")
        self.window.geometry("300x300")

        self.model_label = tk.Label(self.window, text="No model selected")
        self.model_label.pack()
        self.model_button = ctk.CTkButton(
            self.window,
            text="Select Model",
            command=self.select_model,
        )
        self.model_button.pack(pady=10)

        self.image_label = tk.Label(self.window, text="No image selected")
        self.image_label.pack()
        self.image_button = ctk.CTkButton(
            self.window,
            text="Select Image",
            command=self.select_image,
        )
        self.image_button.pack(pady=10)

        self.test_button = ctk.CTkButton(
            self.window,
            text="Test",
            command=self.run,
        )
        self.test_button.pack(pady=10)

        self.window.mainloop()

    def select_model(self) -> None:
        """
        Opens a file dialog to select a model for testing and updates the model_label with the selected file's name.
        :return: None
        """
        model_file = filedialog.askopenfilename(title="Select Model File", filetypes=[("Model files", "*.pth;*.pt")])
        if model_file:
            self.tester.load_model(model_file)
            self.model_label.config(text=os.path.basename(model_file))

    def select_image(self) -> None:
        """
        Opens a file dialog to select an image for testing and updates the image_label with the selected file's name.
        """
        image_file = filedialog.askopenfilename(title="Select Image File",
                                                filetypes=[("Image files", "*.jpg;*.png")])
        if image_file:
            self.tester.set_image_path(image_file)
            self.image_label.config(text=os.path.basename(image_file))

    def run(self) -> None:
        """
        Calls the PerovskiteTester's show_image_with_corners method to display the selected image with detected corners.
        """
        self.tester.show_image_with_corners()


class PerovskiteTester:
    """
    A class to test the corner detection of a given model on a selected image.
    """

    def __init__(self, model_path: [str] = None):
        """
        Initializes the PerovskiteTester with an optional model path.

        :param model_path: Path to the model file, if available.
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = ConvNet().to(self.device)
        self.image_path = None
        if model_path:
            self.load_model(model_path)
        self.transform = transforms.Compose([transforms.ToTensor()])

    def load_model(self, model_path: str) -> None:
        """
        Loads a model from the specified file path.

        :param model_path: Path to the model file.
        """
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def set_image_path(self, image_path: str) -> None:
        """
        Sets the image file path for testing.

        :param image_path: Path to the image file.
        """
        self.image_path = image_path

    def predict_corners(self) -> np.ndarray:
        """
        Predicts the corners of the perovskite crystal in the selected image.

        :return: A NumPy array containing the coordinates of the corners.
        """
        # Use the stored image_path instead of passing it as an argument
        image = Image.open(self.image_path).convert("RGB")
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = self.model(input_tensor)
        corners = output.squeeze().cpu().numpy()
        return corners.reshape(4, 2)

    def show_image_with_corners(self) -> None:
        """
        Displays the selected image with the detected corners drawn on it.
        :return: None
        """
        # Use the stored image_path instead of passing it as an argument
        image = Image.open(self.image_path).convert("RGB")
        corners = self.predict_corners()
        draw = ImageDraw.Draw(image)
        draw.polygon(corners, outline="red", width=15)
        image.show()


if __name__ == "__main__":
    start_time = time.time()
    image_folder1 = "path/to/your/folder"
    excel_file1 = "path/to/your/folder"
    model_folder1 = "path/to/your/folder"
    trainer = PerovskiteTrainer(image_folder1, excel_file1, model_folder1, batch_size=4, num_epochs=2,
                                learning_rate=0.01)
    trainer.run()
    print("\n", "--- %s seconds ---" % (time.time() - start_time))