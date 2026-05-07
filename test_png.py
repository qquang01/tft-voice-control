from PIL import Image, ImageTk
import customtkinter as ctk
import os

# Test PNG support
root = ctk.CTk()
root.title("PNG Test")
root.geometry("400x300")

canvas = ctk.CTkCanvas(root, width=300, height=200, bg="white")
canvas.pack(pady=20)

try:
    img_path = "temp_capture.png"
    if os.path.exists(img_path):
        # Load PNG
        pil_img = Image.open(img_path)
        print(f"Image loaded: {pil_img.size}, mode: {pil_img.mode}")
        
        # Resize for display
        pil_img = pil_img.resize((300, 200))
        
        # Convert to Tkinter format
        tk_img = ImageTk.PhotoImage(pil_img)
        
        # Display on canvas
        canvas.create_image(150, 100, image=tk_img, anchor="center")
        canvas.image = tk_img  # Keep reference
        
        label = ctk.CTkLabel(root, text="PNG displayed successfully!")
        label.pack()
    else:
        label = ctk.CTkLabel(root, text=f"File not found: {img_path}")
        label.pack()
except Exception as e:
    label = ctk.CTkLabel(root, text=f"Error: {e}")
    label.pack()
    print(f"Error: {e}")

root.mainloop()
