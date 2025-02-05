from tkinter import (ttk, Tk, Canvas, filedialog, RIDGE)
import cv2
from PIL import ImageTk, Image
import numpy as np


class FrontEnd:
    def __init__(self, master):
        self.master = master
        self.menu_initialisation()

    # Main Application
    def menu_initialisation(self):
        self.master.geometry('750x630+250+10')
        self.master.title('Photo Editing App')

        # Header
        self.frame_header = ttk.Frame(self.master)
        self.frame_header.pack()

        ttk.Label(self.frame_header, text='PhotoHub').grid(
            row=0, column=2, columnspan=1)
        ttk.Label(self.frame_header, text='An Image Editor Just For You!').grid(
            row=1, column=1, columnspan=3)

        # Menu
        self.frame_menu = ttk.Frame(self.master)
        self.frame_menu.pack()
        self.frame_menu.config(relief=RIDGE, padding=(50, 15))

        # Upload an Image button
        ttk.Button(
            self.frame_menu, text="Upload An Image", command=self.upload_action).grid(
            row=0, column=0, columnspan=2, padx=5, pady=5, sticky='sw')

        # Crop Image button
        ttk.Button(
            self.frame_menu, text="Crop Image", command=self.crop_action).grid(
            row=1, column=0, columnspan=2, padx=5, pady=5, sticky='sw')

        # Save As button
        ttk.Button(
            self.frame_menu, text="Save As", command=self.save_action).grid(
            row=2, column=0, columnspan=2, padx=5, pady=5, sticky='sw')

        # Canvas for displaying images
        self.canvas = Canvas(self.frame_menu, bg="gray", width=500, height=500)
        self.canvas.grid(row=0, column=3, rowspan=10)

        # Initialize attributes for cropping and images
        self.rectangle_id = None
        self.crop_start_x = 0
        self.crop_start_y = 0
        self.crop_end_x = 0
        self.crop_end_y = 0
        self.original_image = None
        self.edited_image = None
        self.filtered_image = None
        self.ratio = 1.0

    def upload_action(self):
        """Upload and load an image onto the canvas."""
        self.canvas.delete("all")  # Clear canvas
        self.filename = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if self.filename:
            self.original_image = cv2.imread(self.filename)
            self.edited_image = self.original_image.copy()
            self.display_image(self.edited_image, enlarge=True)

    def crop_action(self):
        """Enable cropping mode on the canvas."""
        self.canvas.bind("<ButtonPress>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.draw_crop_rectangle)
        self.canvas.bind("<ButtonRelease>", self.end_crop)

    def start_crop(self, event):
        """Start recording the cropping rectangle."""
        self.crop_start_x = event.x
        self.crop_start_y = event.y

    def draw_crop_rectangle(self, event):
        """Draw the cropping rectangle dynamically on the canvas."""
        if self.rectangle_id:
            self.canvas.delete(self.rectangle_id)
        self.crop_end_x = event.x
        self.crop_end_y = event.y
        self.rectangle_id = self.canvas.create_rectangle(
            self.crop_start_x, self.crop_start_y,
            self.crop_end_x, self.crop_end_y,
            outline="red", width=2
        )

    def end_crop(self, event):
        # Calculate the cropped area in original image dimensions
        if self.crop_start_x <= self.crop_end_x and self.crop_start_y <= self.crop_end_y:
            x1, x2 = int(self.crop_start_x * self.ratio), int(self.crop_end_x * self.ratio)
            y1, y2 = int(self.crop_start_y * self.ratio), int(self.crop_end_y * self.ratio)
        elif self.crop_start_x > self.crop_end_x and self.crop_start_y <= self.crop_end_y:
            x1, x2 = int(self.crop_end_x * self.ratio), int(self.crop_start_x * self.ratio)
            y1, y2 = int(self.crop_start_y * self.ratio), int(self.crop_end_y * self.ratio)
        elif self.crop_start_x <= self.crop_end_x and self.crop_start_y > self.crop_end_y:
            x1, x2 = int(self.crop_start_x * self.ratio), int(self.crop_end_x * self.ratio)
            y1, y2 = int(self.crop_end_y * self.ratio), int(self.crop_start_y * self.ratio)
        else:
            x1, x2 = int(self.crop_end_x * self.ratio), int(self.crop_start_x * self.ratio)
            y1, y2 = int(self.crop_end_y * self.ratio), int(self.crop_start_y * self.ratio)

        # Perform the cropping
        self.edited_image = self.edited_image[y1:y2, x1:x2]
        self.display_image(self.edited_image)

        # Unbind crop events
        self.canvas.unbind("<ButtonPress>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease>")
        self.rectangle_id = None

    def save_action(self):
        """Save the edited image to a new file."""
        if self.edited_image is not None:
            original_file_type = self.filename.split('.')[-1]
            save_filename = filedialog.asksaveasfilename(defaultextension=f".{original_file_type}",
                                                         filetypes=[("Image Files", f"*.{original_file_type}")])
            if save_filename:
                cv2.imwrite(save_filename, self.edited_image)
        else:
            print("No image to save.")

    def display_image(self, image=None, enlarge=False):
        """Display an image on the canvas."""
        self.canvas.delete("all")
        if image is None:  # If no image provided, use the original image
            image = self.edited_image.copy()

        # Convert image to RGB (from BGR) for display
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channels = image.shape
        ratio = height / width

        # Resize the image for canvas display
        canvas_width, canvas_height = 500, 500  # Use bigger canvas dimensions
        if enlarge:
            # Resize to fill canvas area while maintaining aspect ratio
            if ratio > 1:  # If image is taller, fit to height
                new_height = canvas_height
                new_width = int(new_height / ratio)
            else:  # If image is wider, fit to width
                new_width = canvas_width
                new_height = int(new_width * ratio)
        else:
            # Default resizing if enlarge is False
            new_width, new_height = width, height
            if height > canvas_height or width > canvas_width:
                if ratio < 1:
                    new_width = canvas_width
                    new_height = int(new_width * ratio)
                else:
                    new_height = canvas_height
                    new_width = int(new_height / ratio)

        self.ratio = height / new_height
        resized_image = cv2.resize(image, (new_width, new_height))

        # Display the resized image using PIL and Tkinter
        self.new_image = ImageTk.PhotoImage(Image.fromarray(resized_image))
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.create_image(
            new_width / 2, new_height / 2, image=self.new_image, anchor="center"
        )


# Main Application
mainWindow = Tk()
FrontEnd(mainWindow)
mainWindow.mainloop()
