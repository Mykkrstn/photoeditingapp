import tkinter as tk
from tkinter import (ttk, Tk, Canvas, filedialog, RIDGE, messagebox)
import cv2
from PIL import ImageTk, Image
import numpy as np


class FrontEnd:
    def __init__(self, master):
        self.master = master
        self.menu_initialisation()

    def menu_initialisation(self):
        self.master.geometry(f"9000x1000+0+0")
        self.master.title('Photo Editor')

        # Main container frame
        self.main_container = ttk.Frame(self.master)
        self.main_container.pack(fill='both', expand=True)

        # Left side frame for menu and original image
        self.left_frame = ttk.Frame(self.main_container)
        self.left_frame.pack(side='left', fill='y', padx=10)

        # Center frame for main canvas
        self.center_frame = ttk.Frame(self.main_container)
        self.center_frame.pack(side='left', fill='both', expand=True)

        # Right frame for comparison views
        self.right_frame = ttk.Frame(self.main_container)
        self.right_frame.pack(side='bottom', fill='x', pady=100)

        # Header
        self.frame_header = ttk.Frame(self.left_frame)
        self.frame_header.pack()

        ttk.Label(self.frame_header, text='Features').pack()

        # Menu
        self.frame_menu = ttk.Frame(self.left_frame)
        self.frame_menu.pack(pady=10)
        self.frame_menu.config(relief=RIDGE, padding=(50, 15))

        # Menu buttons with hints
        self.create_button_with_hint(self.frame_menu, "Upload An Image", self.upload_action, "(Ctrl + O)")
        self.create_button_with_hint(self.frame_menu, "Crop Image", self.crop_action, "(Ctrl + C)")
        self.create_button_with_hint(self.frame_menu, "Undo", self.undo_action, "(Ctrl + Z)")
        self.create_button_with_hint(self.frame_menu, "Save As", self.save_action, "(Ctrl + S)")
        self.slider = tk.Scale(self.left_frame, from_=1, to=10, orient='horizontal', label="Resize",command=None)
        self.slider.set(5)
        self.slider.configure(command=self.adjust_quality)
        self.slider.pack()

        # Original Image (below the menu buttons in the left frame)
        self.original_canvas = Canvas(self.left_frame, bg="lightgray", width=300, height=300)
        self.original_canvas.pack(pady=15)
        ttk.Label(self.left_frame, text="Original Image").pack()

        # Main canvas (centered)
        self.canvas = Canvas(self.center_frame, bg="gray")
        self.canvas.pack(expand=True)       

        # Initialize attributes
        self.rectangle_id = None
        self.crop_x = 0
        self.crop_y = 0
        self.crop_end_x = 0
        self.crop_end_y = 0
        self.original_image = None
        self.edited_image = None
        self.ratio = 1.0
        self.window_width = 900
        self.window_height = 900
        self.image_history = []
        self.redo_stack = []
        self.back_up = {}

        # Bind keyboard shortcuts for undo, redo, save, open, and crop
        self.master.bind('<Control-z>', self.undo_action)
        self.master.bind('<Control-s>', self.save_action)  # Ctrl + S for Save As
        self.master.bind('<Control-o>', self.upload_action)  # Ctrl + O for Upload File
        self.master.bind('<Control-c>', self.crop_action)  # Ctrl + C for Crop

    def create_button_with_hint(self, frame, text, command, shortcut):
        """Create a button with a hint showing the keyboard shortcut next to it."""
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=5, fill='x')

        button = ttk.Button(button_frame, text=text, command=command)
        button.pack(side='left', padx=10)

        hint_label = ttk.Label(button_frame, text=shortcut)
        hint_label.pack(side='left')

    def upload_action(self, event=None):
        """Upload and load an image onto the canvas."""
        self.canvas.delete("all")  # Clear canvas
        self.filename = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if self.filename:
            try:
                self.original_image = cv2.imread(self.filename)
                if self.original_image is None:
                    raise ValueError("Invalid image file.")
                self.edited_image = self.original_image.copy()
                self.display_image(self.edited_image, enlarge=True)
                # Display only the original image on the left canvas below the buttons
                self.display_original_image()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def crop_action(self, event=None):
        """Enable cropping mode on the canvas."""
        if self.edited_image is None:
            messagebox.showwarning("Warning", "No image to crop.")
            return
        self.image_history.append(self.edited_image.copy())  # Save the current image to history before cropping
        self.redo_stack.clear()  # Clear redo stack when a new action happens
        self.canvas.bind("<ButtonPress>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.draw_crop_rectangle)
        self.canvas.bind("<ButtonRelease>", self.end_crop)

    def start_crop(self, event):
        """Start recording the cropping rectangle."""
        self.crop_x = event.x
        self.crop_y = event.y

    def draw_crop_rectangle(self, event):
        """Draw the cropping rectangle dynamically on the canvas."""
        if self.rectangle_id:
            self.canvas.delete(self.rectangle_id)
        self.crop_end_x = event.x
        self.crop_end_y = event.y
        self.rectangle_id = self.canvas.create_rectangle( self.crop_x, self.crop_y, self.crop_end_x, self.crop_end_y, outline="red", width=2)

    def end_crop(self, event):
        """End the cropping action and update the edited image."""
        # Calculate the cropped area in original image dimensions
        x1, x2 = int(self.ratio*min(self.crop_x, self.crop_end_x)), int(self.ratio*max(self.crop_x, self.crop_end_x))
        y1, y2 = int(self.ratio*min(self.crop_y, self.crop_end_y)), int(self.ratio*max(self.crop_y, self.crop_end_y))


        # Perform the cropping
        self.edited_image = self.edited_image[y1:y2, x1:x2]
        self.display_image(self.edited_image)
        self.display_original_image()

        # Unbind crop events
        self.canvas.unbind("<ButtonPress>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease>")
        self.rectangle_id = None
        self.back_up[1] = self.edited_image.copy()
    def undo_action(self, event=None):
        """Undo the previous image edit."""
        if self.image_history:
            self.redo_stack.append(self.edited_image.copy())  # Save the current image to redo stack
            self.edited_image = self.image_history.pop()  # Pop the last image from history
            self.display_image(self.edited_image)
            self.display_original_image()        
    def adjust_quality(self, value):
        if self.edited_image is None:
            messagebox.showwarning("Warning", "No processed image to adjust, or must crop before adjusting.")
            return
        
        quality = int(value)
        if quality not in self.back_up:
            origin_image = self.back_up[1].copy()
            height, width,_ = origin_image.shape
            new_height, new_width = height * quality, width * quality 
            self.back_up[quality] = cv2.resize(origin_image, (new_width, new_height))
        self.edited_image = self.back_up[quality]
        self.display_image(self.edited_image)   

    def save_action(self):
        """Save the edited image to a new file."""
        if self.edited_image is not None:
            original_file_type = self.filename.split('.')[-1]
            save_filename = filedialog.asksaveasfilename(defaultextension=f".{original_file_type}", filetypes=[("Image Files", f"*.{original_file_type}")])
            if save_filename:
                cv2.imwrite(save_filename, self.edited_image)
                messagebox.showinfo("Success", "Image saved successfully.")
        else:
            messagebox.showwarning("Warning", "No image to save.")

    def display_image(self, image=None, enlarge=False):
        """Display the image on the main canvas."""
        self.canvas.delete("all")
        if image is None:
            image = self.edited_image.copy()

        # # Convert image to RGB (from BGR) for display
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width,_ = rgb_image.shape
        new_height = min(self.window_height, height)
        new_width = min(self.window_width, width)
        rgb_image = cv2.resize(rgb_image, (new_width, new_height))
    
        rgb_image = Image.fromarray(rgb_image)
        self.tk_image = ImageTk.PhotoImage(rgb_image)
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.create_image(new_width/2, new_height/2 , image=self.tk_image, anchor="center")
        return rgb_image

    def display_original_image(self):
        """Display the original image only on the left canvas below the buttons."""
        if self.original_image is not None:
            self.display_on_canvas(self.original_canvas, self.original_image, 300)

    def display_on_canvas(self, canvas, image, max_size):
        """Helper function to display an image on a specific canvas."""
        if image is None:
            return

        # Convert image to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]
        ratio = height / width

        # Calculate new dimensions
        if ratio > 1:
            new_height = max_size
            new_width = int(new_height / ratio)
        else:
            new_width = max_size
            new_height = int(new_width * ratio)

        # Resize image
        resized_image = cv2.resize(image_rgb, (new_width, new_height))
        photo_image = ImageTk.PhotoImage(Image.fromarray(resized_image))

        # Update canvas
        canvas.config(width=new_width, height=new_height)
        canvas.create_image(new_width/2, new_height/2, image=photo_image, anchor="center")
        canvas.image = photo_image  # Keep a reference


# Main Application
mainWindow = Tk()
FrontEnd(mainWindow)
mainWindow.mainloop()



# Main Application
mainWindow = Tk()
FrontEnd(mainWindow)
mainWindow.mainloop()
