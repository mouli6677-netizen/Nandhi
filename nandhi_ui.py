# nandhi_ui.py
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from core.engine_instance import engine

class NandhiUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nandhi AI Assistant")
        self.setGeometry(200, 200, 700, 500)
        self.layout = QVBoxLayout()
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)
        
        # Input field
        self.user_input = QLineEdit()
        self.layout.addWidget(self.user_input)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.layout.addWidget(self.send_button)
        
        # Memory count label
        self.memory_label = QLabel("Memory Count: 0")
        self.layout.addWidget(self.memory_label)
        
        self.setLayout(self.layout)
    
    def send_message(self):
        text = self.user_input.text().strip()
        if not text:
            return
        self.chat_display.append(f"You: {text}")
        self.user_input.clear()
        
        # Image/video commands
        if text.startswith("analyze_image "):
            path = text[len("analyze_image "):].strip()
            response = engine.analyze_image(path)
        elif text.startswith("analyze_video "):
            path = text[len("analyze_video "):].strip()
            response = engine.analyze_video(path)
        else:
            response = engine.generate_reply(text)
        
        self.chat_display.append(f"Nandhi: {response}\n")
        self.memory_label.setText(f"Memory Count: {engine.memory_count()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NandhiUI()
    window.show()
    sys.exit(app.exec())