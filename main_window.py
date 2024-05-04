import sys
import cv2
import json
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, \
    QFileDialog, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main window setup
        self.setWindowTitle("Video Classifier")
        self.setGeometry(400, 400, 800, 600)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        # Video display
        self.video_label = QLabel("Video Display Area")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Set size policy
        layout.addWidget(self.video_label)

        # Thumbnail grid
        self.thumbnail_grid = QHBoxLayout()
        layout.addLayout(self.thumbnail_grid)

        # Grid display area for thumbnail holders
        self.grid_display_area = QHBoxLayout()
        layout.addLayout(self.grid_display_area)

        # Frame info layout
        frame_info_layout = QHBoxLayout()
        layout.addLayout(frame_info_layout)

        # Number of frames label
        self.frames_label = QLabel("Number of Frames: 0")
        frame_info_layout.addWidget(self.frames_label)

        # Current frame label
        self.current_frame_label = QLabel("Current Frame: 0")
        frame_info_layout.addWidget(self.current_frame_label)

        # Scroll buttons
        self.scroll_left_button_100 = QPushButton("-100<<<")
        self.scroll_left_button_10 = QPushButton("-10<<")
        self.scroll_left_button_1 = QPushButton("-1<")
        self.scroll_right_button_1 = QPushButton(">+1")
        self.scroll_right_button_10 = QPushButton(">>+10")
        self.scroll_right_button_100 = QPushButton(">>+100")

        layout_buttons = QHBoxLayout()
        layout_buttons.addWidget(self.scroll_left_button_100)
        layout_buttons.addWidget(self.scroll_left_button_10)
        layout_buttons.addWidget(self.scroll_left_button_1)
        layout_buttons.addWidget(self.scroll_right_button_1)
        layout_buttons.addWidget(self.scroll_right_button_10)
        layout_buttons.addWidget(self.scroll_right_button_100)
        layout.addLayout(layout_buttons)

        # Mark start and end buttons
        self.mark_start_button = QPushButton("Mark Start")
        self.mark_end_button = QPushButton("Mark End")
        layout_mark_buttons = QHBoxLayout()
        layout_mark_buttons.addWidget(self.mark_start_button)
        layout_mark_buttons.addWidget(self.mark_end_button)
        layout.addLayout(layout_mark_buttons)

        # Buttons for controls
        load_button = QPushButton("Load Video")
        classify_button = QPushButton("Classify Video")
        layout.addWidget(load_button)
        layout.addWidget(classify_button)

        # Connect button signals to slots
        load_button.clicked.connect(self.load_video)
        self.scroll_left_button_100.clicked.connect(lambda: self.scroll_frames(-100))
        self.scroll_left_button_10.clicked.connect(lambda: self.scroll_frames(-10))
        self.scroll_left_button_1.clicked.connect(lambda: self.scroll_frames(-1))
        self.scroll_right_button_1.clicked.connect(lambda: self.scroll_frames(1))
        self.scroll_right_button_10.clicked.connect(lambda: self.scroll_frames(10))
        self.scroll_right_button_100.clicked.connect(lambda: self.scroll_frames(100))
        self.mark_start_button.clicked.connect(self.mark_start_frame)
        self.mark_end_button.clicked.connect(self.mark_end_frame)

        # Variables
        self.video_file = None
        self.video_capture = None
        self.num_frames = 0
        self.current_frame_index = 0
        self.thumbnail_labels = []
        self.frame_cap_index = 3  # Index of the frame cap (4th frame)
        self.scenes = []

    def load_video(self):
        # Open file dialog to select video file
        file_dialog = QFileDialog()
        self.video_file, _ = file_dialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv)")

        if self.video_file:
            # Read video file
            self.video_capture = cv2.VideoCapture(self.video_file)

            # Get number of frames
            self.num_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.frames_label.setText(f"Number of Frames: {self.num_frames}")

            # Extract first frame
            success, frame = self.video_capture.read()
            if success:
                # Display first frame in the main window
                self.display_frame(frame)
                # Create thumbnail holders in grid display area
                self.create_thumbnail_holders(frame)
            else:
                print("Failed to read video file")

    def display_frame(self, frame):
        # Convert frame to QImage
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # Resize image if necessary to fit the QLabel
        q_img = q_img.scaled(self.video_label.size(), Qt.KeepAspectRatio)

        # Set the image as the pixmap of the QLabel
        self.video_label.setPixmap(QPixmap.fromImage(q_img))

        # Update current frame label
        self.current_frame_label.setText(f"Current Frame: {self.current_frame_index + 1}")

    def create_thumbnail_holders(self, frame):
        # Clear existing thumbnail holders
        for label in self.thumbnail_labels:
            label.deleteLater()
        self.thumbnail_labels.clear()

        # Create thumbnail holders
        for i in range(min(10, self.num_frames)):
            thumbnail_holder = QLabel()
            thumbnail_holder.setFixedSize(100, 75)  # Set size of thumbnail holder
            thumbnail = self.get_thumbnail(frame, i)
            thumbnail_holder.setPixmap(thumbnail)
            self.thumbnail_grid.addWidget(thumbnail_holder)  # Add thumbnail to the grid layout
            self.thumbnail_labels.append(thumbnail_holder)

            if i == 3:  # Index of the fourth thumbnail (0-based indexing)
                self.draw_frame_cap(thumbnail_holder)

            # Connect clicked signal to slot
            thumbnail_holder.mousePressEvent = lambda event, index=i: self.thumbnail_clicked(index)

    def get_thumbnail(self, frame, index):
        # Set video capture to the beginning
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, index)

        # Read frame
        _, frame = self.video_capture.read()

        # Resize frame to thumbnail size
        thumbnail_width = 100
        thumbnail_height = 75
        frame = cv2.resize(frame, (thumbnail_width, thumbnail_height))

        # Convert frame to QImage
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # Convert QImage to QPixmap
        pixmap = QPixmap.fromImage(q_img)

        return pixmap

    def draw_frame_cap(self, label):
        pixmap = label.pixmap()
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.red, 2))
        painter.drawRect(0, 0, pixmap.width(), pixmap.height())
        painter.end()
        label.setPixmap(pixmap)

    def thumbnail_clicked(self, index):
        # Set video capture to the clicked frame
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, index)

        # Read and display the clicked frame
        _, frame = self.video_capture.read()
        self.display_frame(frame)

    def update_thumbnail_bar(self):
        # Clear existing thumbnail holders
        for label in self.thumbnail_labels:
            label.deleteLater()
        self.thumbnail_labels.clear()

        # Set video capture to the current frame index
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_index)

        # Read frame
        _, frame = self.video_capture.read()

        # Create thumbnail holders
        for i in range(self.current_frame_index, min(self.current_frame_index + 10, self.num_frames)):
            thumbnail_holder = QLabel()
            thumbnail_holder.setFixedSize(100, 75)  # Set size of thumbnail holder
            thumbnail = self.get_thumbnail(frame, i)
            thumbnail_holder.setPixmap(thumbnail)
            self.grid_display_area.addWidget(thumbnail_holder)
            self.thumbnail_labels.append(thumbnail_holder)

            if i == self.frame_cap_index:
                self.draw_frame_cap(thumbnail_holder)

            # Connect clicked signal to slot
            thumbnail_holder.mousePressEvent = lambda event, index=i: self.thumbnail_clicked(index)

    def scroll_frames(self, step):
        # Calculate new frame index
        new_frame_index = max(0, min(self.num_frames - 1, self.current_frame_index + step))

        # Set current frame index
        self.current_frame_index = new_frame_index

        # Update thumbnails
        self.update_thumbnail_bar()

        # Set video capture to the new frame index
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, new_frame_index)

        # Read and display the frame corresponding to the new index
        _, frame = self.video_capture.read()
        self.display_frame(frame)

    def mark_start_frame(self):
        start_frame = self.current_frame_index + 1
        if start_frame <= self.num_frames:
            if not self.scenes:  # First scene
                start_frame = 1
            elif start_frame != self.scenes[-1]["end_frame"] + 1:  # Subsequent scenes
                # Adjust the start frame to be the end frame of the previous scene plus 1
                start_frame = self.scenes[-1]["end_frame"] + 1

            scene = {"id": len(self.scenes) + 1, "start_frame": start_frame}
            self.scenes.append(scene)
            print(f"Marked start frame: {start_frame}")
        else:
            print("Error: Cannot mark start frame beyond the end of the video.")

    def mark_end_frame(self):
        end_frame = self.current_frame_index + 1
        if end_frame <= self.num_frames:
            if self.scenes:
                if end_frame <= self.scenes[-1]["start_frame"]:
                    print("Error: End frame should be after the start frame.")
                    return
                self.scenes[-1]["end_frame"] = end_frame
                print(f"Marked end frame: {end_frame}")
            else:
                print("Error: Please mark start frame first.")
        else:
            print("Error: Cannot mark end frame beyond the end of the video.")

    def export_data(self):
        # Write scenes to JSON file
        if not self.scenes:
            print("Error: No scenes to export.")
            return

        # Get the name of the video file being labeled
        video_name = os.path.basename(self.video_file)
        video_name = os.path.splitext(video_name)[0]  # Remove extension

        # Get the directory of the main script file
        main_script_dir = os.path.dirname(sys.argv[0])

        # Construct the path for the JSON file
        json_dir = os.path.join(main_script_dir, "jsons")
        os.makedirs(json_dir, exist_ok=True)  # Create jsons directory if it doesn't exist
        json_file_path = os.path.join(json_dir, f"{video_name}.json")

        print(f"Attempting to save scenes to: {json_file_path}")

        # Write scenes to JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump({"scenes": self.scenes}, json_file, indent=4)

        print(f"Scenes exported to: {json_file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.aboutToQuit.connect(window.export_data)
    sys.exit(app.exec_())
