# core/tools.py
import os
from PIL import Image, ImageFilter
import cv2

class MediaTools:
    """Analyze and edit images/videos locally"""
    
    # --- Image methods ---
    def analyze_image(self, path):
        try:
            img = Image.open(path)
            return f"Image {os.path.basename(path)} size: {img.size}, mode: {img.mode}"
        except Exception as e:
            return f"Failed to analyze image: {e}"

    def edit_image(self, path, output_path, operation="grayscale"):
        try:
            img = Image.open(path)
            if operation == "grayscale":
                img = img.convert("L")
            elif operation == "blur":
                img = img.filter(ImageFilter.BLUR)
            img.save(output_path)
            return f"Edited image saved to {output_path}"
        except Exception as e:
            return f"Failed to edit image: {e}"

    # --- Video methods ---
    def analyze_video(self, path):
        try:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                return f"Cannot open video {path}"
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            return f"Video {os.path.basename(path)}: {frame_count} frames, {width}x{height}, {fps:.2f} FPS"
        except Exception as e:
            return f"Failed to analyze video: {e}"

    def extract_frames(self, path, output_dir, step=30):
        """Extract every `step`-th frame from video"""
        os.makedirs(output_dir, exist_ok=True)
        cap = cv2.VideoCapture(path)
        count = 0
        saved = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if count % step == 0:
                frame_path = os.path.join(output_dir, f"frame_{count}.jpg")
                cv2.imwrite(frame_path, frame)
                saved += 1
            count += 1
        cap.release()
        return f"Extracted {saved} frames to {output_dir}"

class ToolRegistry:
    def __init__(self, tool_impl):
        self.tool_impl = tool_impl

    # Image
    def analyze_image(self, path):
        return self.tool_impl.analyze_image(path)

    def edit_image(self, path, output_path, operation="grayscale"):
        return self.tool_impl.edit_image(path, output_path, operation)

    # Video
    def analyze_video(self, path):
        return self.tool_impl.analyze_video(path)

    def extract_frames(self, path, output_dir, step=30):
        return self.tool_impl.extract_frames(path, output_dir, step)