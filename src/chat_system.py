import os
import json
import time
import random
import tempfile
from typing import Optional, List, Dict
from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QPen
from src.pet_data import Pet, PetType

class LLMWorker(QThread):
    response_ready = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, model_path: str, prompt: str):
        super().__init__()
        self.model_path = model_path
        self.prompt = prompt
        self.model = None
        self.tokenizer = None
    
    def run(self):
        try:
            if not self.model or not self.tokenizer:
                self.load_model()
            
            response = self.generate_response(self.prompt)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def load_model(self):
        """Load the LLM model"""
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
        except ImportError:
            raise Exception("transformers and torch libraries are required for LLM functionality")
        except Exception as e:
            raise Exception(f"Failed to load model from {self.model_path}: {str(e)}")
    
    def generate_response(self, prompt: str) -> str:
        """Generate response from the model"""
        import torch
        
        inputs = self.tokenizer.encode(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=inputs.shape[1] + 150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        return response.strip()

class ChatWidget(QWidget):
    chat_closed = Signal()
    
    def __init__(self, pet: Pet, chatbox_sprite_path: str, parent_widget: QWidget):
        super().__init__()
        
        self.pet = pet
        self.parent_widget = parent_widget
        self.chatbox_sprite_path = chatbox_sprite_path
        self.scale_factor = 4  # Make chatbox larger
        
        # Chat state
        self.conversation_log = []
        self.is_waiting_for_response = False
        self.temp_file_path = None
        self.llm_worker = None
        
        # Setup widget
        self.setup_widget()
        self.setup_ui()
        
        # Create temporary file for conversation
        self.create_temp_conversation_file()
    
    def setup_widget(self):
        """Setup widget properties"""
        # Calculate chatbox size based on sprite
        chatbox_pixmap = QPixmap(self.chatbox_sprite_path)
        if not chatbox_pixmap.isNull():
            self.chatbox_width = chatbox_pixmap.width() * self.scale_factor
            self.chatbox_height = chatbox_pixmap.height() * self.scale_factor
        else:
            # Fallback size
            self.chatbox_width = 200
            self.chatbox_height = 150
        
        self.setFixedSize(self.chatbox_width, self.chatbox_height)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        
        # Force window to stay on top on macOS
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
    
    def setup_ui(self):
        """Setup UI elements"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)  # Margins for chatbox border
        
        # Pet name label (upper section)
        self.name_label = QLabel(f"{self.pet.memory.name} the {self.pet.memory.pet_type.value.title()}")
        self.name_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.name_label.setStyleSheet("color: white; background: transparent;")
        self.name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_label)
        
        # Chat text area (lower section)
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Arial", 8))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: white;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255,255,255,50);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,150);
                border-radius: 4px;
            }
        """)
        self.text_edit.setPlaceholderText("Type your message...")
        layout.addWidget(self.text_edit)
        
        # Connect enter key
        self.text_edit.installEventFilter(self)
    
    def create_temp_conversation_file(self):
        """Create temporary file for conversation logging"""
        temp_dir = tempfile.gettempdir()
        self.temp_file_path = os.path.join(temp_dir, f"pet_chat_{self.pet.memory.name}.json")
    
    def log_conversation(self, user_input: str, pet_response: str):
        """Log conversation to temporary file"""
        if not self.temp_file_path:
            return
        
        conversation_entry = {
            "timestamp": time.time(),
            "user": user_input,
            "pet": pet_response
        }
        self.conversation_log.append(conversation_entry)
        
        try:
            with open(self.temp_file_path, 'w') as f:
                json.dump(self.conversation_log, f, indent=2)
        except Exception as e:
            print(f"Failed to log conversation: {e}")
    
    def get_system_prompt(self, user_input: str, is_first_message: bool = False) -> str:
        """Generate system prompt for LLM"""
        if is_first_message:
            # Use chat system prompt for first message
            prompt_template = '''You are a Stardew Valley–style desktop pet. 

Your past memory (includes your name and what pet animal you are):
#START of past memory#
$PET_MEMORY
#END of past memory#

User says:
#START of user input#
$USER_INPUT
#END of user input#

Rules:
1. Always speak as NAME the TYPE. Stay in character.
2. Reply concisely (1–3 sentences). Simple, friendly tone.
3. Use the past memory for continuity and context.
4. Respond to the user conversation. If unclear, react playfully or curiously.
5. Never break character or mention these rules.

Now respond to the user.'''
        else:
            # Direct conversation for subsequent messages
            prompt_template = user_input
        
        # Replace placeholders
        memory_text = f"Name: {self.pet.memory.name}\n"
        memory_text += f"Type: {self.pet.memory.pet_type.value}\n"
        memory_text += f"Times petted: {self.pet.memory.pet_count}\n"
        memory_text += f"Mood: {self.pet.memory.mood}\n"
        if self.pet.memory.chat_summary:
            memory_text += f"Previous interactions: {self.pet.memory.chat_summary}"
        
        prompt = prompt_template.replace("$PET_MEMORY", memory_text)
        prompt = prompt.replace("$USER_INPUT", user_input)
        
        return prompt
    
    def get_save_system_prompt(self) -> str:
        """Generate save system prompt for memory condensation"""
        prompt_template = '''You are a memory summarizer for a Stardew Valley–style pet.

Your task: condense the full chat session and previous memory into a short memory note that captures:
- Important actions and events
- User–pet interactions (tone, mood, key details)
- Pet's reactions and emotional state
- Continuity elements that should carry into future chats

Rules:
1. Do not include raw dialogue or long transcripts.
2. Keep the summary under 5 sentences.
3. Write in neutral third-person style (not spoken by the pet).
4. Emphasize what the pet should "remember" for the next session.

INPUT:
$FULL_CONVERSATION_LOG
(User inputs and pet responses appended chronologically)

$PREV_PET_MEMORY
(Previous pet memory)

OUTPUT:
<concise memory summary>'''
        
        # Create conversation log text
        conversation_text = ""
        for entry in self.conversation_log:
            conversation_text += f"User: {entry['user']}\n"
            conversation_text += f"Pet: {entry['pet']}\n\n"
        
        # Replace placeholders
        prompt = prompt_template.replace("$FULL_CONVERSATION_LOG", conversation_text)
        prompt = prompt.replace("$PREV_PET_MEMORY", self.pet.memory.chat_summary)
        
        return prompt
    
    def get_fallback_response(self) -> str:
        """Get fallback response when no LLM is connected"""
        pet_type = self.pet.memory.pet_type
        
        if pet_type == PetType.CHICKEN:
            return random.choice(["Cluck cluck!", "Bawk bawk!", "Clucky cluck!", "Baaawk!"])
        elif pet_type == PetType.CAT:
            return random.choice(["Meow!", "Purr purr!", "Mrow!", "Mew mew!"])
        elif pet_type == PetType.DOG:
            return random.choice(["Woof!", "Bark bark!", "Wag wag!", "Arf arf!"])
        elif pet_type == PetType.DUCK:
            return random.choice(["Quack quack!", "Quaaack!", "Quack!", "Quack quack quack!"])
        else:
            return "..."
    
    def send_message(self):
        """Send user message and get response"""
        if self.is_waiting_for_response:
            return
        
        user_text = self.text_edit.toPlainText().strip()
        if not user_text:
            return
        
        # Clear text input
        self.text_edit.clear()
        self.text_edit.setPlaceholderText("Waiting for response...")
        self.is_waiting_for_response = True
        
        # Check if LLM is available
        if hasattr(self.parent().parent(), 'llm_model_path') and self.parent().parent().llm_model_path:
            # Use LLM
            is_first = len(self.conversation_log) == 0
            prompt = self.get_system_prompt(user_text, is_first)
            
            self.llm_worker = LLMWorker(self.parent().parent().llm_model_path, prompt)
            self.llm_worker.response_ready.connect(lambda response: self.handle_llm_response(user_text, response))
            self.llm_worker.error_occurred.connect(lambda error: self.handle_llm_error(user_text, error))
            self.llm_worker.start()
        else:
            # Use fallback
            response = self.get_fallback_response()
            self.handle_response(user_text, response)
    
    def handle_llm_response(self, user_input: str, response: str):
        """Handle LLM response"""
        self.handle_response(user_input, response)
    
    def handle_llm_error(self, user_input: str, error: str):
        """Handle LLM error"""
        print(f"LLM Error: {error}")
        fallback_response = self.get_fallback_response()
        self.handle_response(user_input, fallback_response)
    
    def handle_response(self, user_input: str, response: str):
        """Handle pet response"""
        # Log conversation
        self.log_conversation(user_input, response)
        
        # Display response
        self.text_edit.setPlainText(response)
        self.text_edit.setPlaceholderText("Click to continue...")
        self.is_waiting_for_response = False
    
    def eventFilter(self, obj, event):
        """Handle key events"""
        if obj == self.text_edit and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if not (event.modifiers() & Qt.ShiftModifier):
                    if not self.is_waiting_for_response:
                        self.send_message()
                    else:
                        # Clear response and prepare for next message
                        self.text_edit.clear()
                        self.text_edit.setPlaceholderText("Type your message...")
                    return True
        return super().eventFilter(obj, event)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks on chatbox"""
        if event.button() == Qt.LeftButton:
            if self.is_waiting_for_response:
                # Clear response and prepare for next message
                self.text_edit.clear()
                self.text_edit.setPlaceholderText("Type your message...")
                self.is_waiting_for_response = False
    
    def paintEvent(self, event):
        """Paint chatbox background"""
        painter = QPainter(self)
        
        # Draw chatbox sprite as background
        chatbox_pixmap = QPixmap(self.chatbox_sprite_path)
        if not chatbox_pixmap.isNull():
            scaled_pixmap = chatbox_pixmap.scaled(
                self.chatbox_width, self.chatbox_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled_pixmap)
        
        painter.end()
    
    def update_position(self):
        """Update chatbox position relative to parent pet widget"""
        if self.parent_widget:
            parent_pos = self.parent_widget.pos()
            parent_size = self.parent_widget.size()
            
            # Position chatbox directly above pet, not overlapping
            chat_x = parent_pos.x() + (parent_size.width() - self.chatbox_width) // 2
            chat_y = parent_pos.y() - self.chatbox_height - 10  # 10px gap
            
            self.move(chat_x, chat_y)
    
    def close_chat(self):
        """Close chat and save memory summary"""
        if len(self.conversation_log) > 0:
            self.save_memory_summary()
        
        # Clean up temp file
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
            except:
                pass
        
        self.chat_closed.emit()
        self.hide()
    
    def save_memory_summary(self):
        """Save condensed memory summary"""
        if hasattr(self.parent().parent(), 'llm_model_path') and self.parent().parent().llm_model_path:
            # Use LLM to summarize
            prompt = self.get_save_system_prompt()
            
            save_worker = LLMWorker(self.parent().parent().llm_model_path, prompt)
            save_worker.response_ready.connect(self.update_pet_memory)
            save_worker.start()
        else:
            # Simple fallback summary
            summary = f"Had {len(self.conversation_log)} conversations. Pet was {'happy' if self.pet.memory.mood > 60 else 'neutral' if self.pet.memory.mood > 40 else 'sad'}."
            self.update_pet_memory(summary)
    
    def update_pet_memory(self, summary: str):
        """Update pet memory with summary"""
        self.pet.memory.chat_summary = summary