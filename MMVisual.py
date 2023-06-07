import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QSplitter, QPushButton, QFileDialog, QComboBox, QMenuBar, QAction, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCharFormat, QTextCursor, QColor
import time
import openai
from functools import partial
import re
 
openai.api_key = "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"

class HighlightTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cursorPositionChanged.connect(self.update_highlight)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.update_highlight()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.update_highlight()

    def update_highlight(self):
        # Reset all previous formatting
        new_cursor = self.textCursor()
        new_cursor.movePosition(QTextCursor.Start)
        new_cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        reset_format = QTextCharFormat()
        new_cursor.setCharFormat(reset_format)

        # Highlight current line
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        format = QTextCharFormat()
        format.setBackground(QColor(Qt.yellow))
        cursor.setCharFormat(format)

        self.mergeCurrentCharFormat(format)

class ReadOnlyHighlightTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

    def contextMenuEvent(self, event):
        super().contextMenuEvent(event)
        self.highlightSelection()

    def highlightSelection(self):
        self.setReadOnly(False)

        cursor = self.textCursor()
        if cursor.hasSelection():
            format = QTextCharFormat()
            format.setBackground(QColor(Qt.yellow))
            cursor.setCharFormat(format)

        self.setTextCursor(cursor)
        self.setReadOnly(True)



class ChatWindow(QWidget):
    def __init__(self, editor, api_key):
        super().__init__()
        # Store reference to the TwoColumnEditor instance
        self.editor = editor
        
        self.api_key = api_key
        openai.api_key = self.api_key
        
        self.setWindowTitle("Chat Window")

        # Set the initial size of the window
        self.resize(500, 400)

        # Create the dialog text box for chat history
        self.dialog_text = QTextEdit()
        self.dialog_text.setReadOnly(True)

        # Add default prompt to the dialog box
        self.dialog_text.append("ChatBot: Hi! How can I assist you today?")

        # Create the question text box for input
        self.question_edit = QTextEdit()
        font = QFont()
        font.setPointSize(16)
        self.dialog_text.setFont(font)
        self.question_edit.setFont(font)
        self.question_edit.setPlaceholderText("Please enter your question here!")

        # Create the submit button
        self.submit_button = QPushButton('Submit')
        self.submit_button.clicked.connect(self.submit_question)

        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(self.dialog_text)
        layout.addWidget(self.question_edit)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_question(self):
        # Get the question text
        question = self.question_edit.toPlainText()

        # Get the text from the TwoColumnEditor's text boxes
        left_text = self.editor.text_edit_1.toPlainText()
        right_text = self.editor.text_edit_2.toPlainText()
        
        prompt = """你是一个聪明的AI,同时乐于助人！
用户正准备修改上面<>中的内容，但是遇到了一些困难。
请参考上述【】中的内容，回答用户下面的问题："""
        # Combine the question and the text box contents
        full_text = '<' + left_text + '>' + '\n' + '【' + right_text + '】' + prompt + '\n' + question

        # Display question in the dialog text box
        self.dialog_text.append("User: " + question)
        try:
            print(len(full_text))
            # Send the full_text to AI instead of just the question
            response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "user", "content": full_text}
            ],
            temperature=0.8,
            max_tokens=2000,
            stream=True,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            user='RdFast智能创作机器人小程序'
            )
            # ... Your code to handle the question ...
            # For example, let's assume we have a function named 'get_answer'
            # answer = get_answer(question)
            # Display answer in the dialog text box
            # self.dialog_text.append("ChatBot: " + answer)
            ans = ''
            for r in response:
                if 'content' in r.choices[0].delta:
                    ans += r.choices[0].delta['content']
                    self.dialog_text.clear()
                    self.dialog_text.append("User: " + question)
                    self.dialog_text.append("ChatBot: " + ans)
        except Exception as e:
            print("An error occurred:", e)
            QMessageBox.critical(self, "Error From API Key", "The APIkey is not legal or the balance is insufficient.")
        # Clear the question text box
        self.question_edit.clear()






class TwoColumnEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        # Setup the main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        self.init_ui()
        self.init_menu()
        self.file_name = ''
        self.load_file('Model')
    def init_menu(self):
        self.menu_bar = QMenuBar()

        # File menu
        file_menu = self.menu_bar.addMenu('File')
        open_action = QAction('Open', self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Edit menu
        edit_menu = self.menu_bar.addMenu('Edit')
        chat_action = QAction('APIkey', self)
        chat_action.triggered.connect(self.change_api_key)
        edit_menu.addAction(chat_action)
        
        # Doc menu
        doc_menu = self.menu_bar.addMenu('Doc')
        doc_action = QAction('Model', self)
        doc_action.triggered.connect(partial(self.load_file, 'Model'))
        doc_menu.addAction(doc_action)
        
        dataset_action = QAction('Dataset', self)
        dataset_action.triggered.connect(partial(self.load_file, 'Dataset'))
        doc_menu.addAction(dataset_action)

        # Add combo box to the menu bar
        # self.menu_bar.setCornerWidget(self.combo_box, Qt.TopRightCorner)
        
        self.setMenuBar(self.menu_bar)
    

    def is_valid_api_key(self, api_key):
        pattern = r'^sk-\w+$'
        return re.match(pattern, api_key) is not None

    def change_api_key(self):
        api_key, ok = QInputDialog.getText(self, 'Enter APIKEY', 'Enter your APIKEY:')
        if ok:
            if self.is_valid_api_key(api_key):
                with open('key.txt', 'w') as f:
                    f.write(api_key)
                return api_key
            else:
                QMessageBox.critical(self, "Invalid API Key", "The API key you entered is invalid. Please enter a valid API key.")
        return None

    def ask_api_key(self):
        try:
            # Try to read the API key from the file
            with open('key.txt', 'r') as f:
                api_key = f.read().strip()
            if api_key:
                return api_key
        except FileNotFoundError:
            # If the file does not exist, ask the user for the API key
            api_key, ok = QInputDialog.getText(self, 'Enter APIKEY', 'Enter your APIKEY:')
            if ok:
                # If the user entered a key, save it to the file
                with open('key.txt', 'w') as f:
                    f.write(api_key)
                return api_key
        return None



    def init_ui(self):
        self.setWindowTitle("cfg配置工具")

        self.text_edit_1 = HighlightTextEdit()
        self.text_edit_2 = ReadOnlyHighlightTextEdit()

        # Set the font size
        font = QFont()
        font.setPointSize(16)
        self.text_edit_1.setFont(font)
        self.text_edit_2.setFont(font)

        self.text_edit_2.setReadOnly(True)

        self.open_button = QPushButton('Open')
        self.open_button.clicked.connect(self.open_file)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_file)

        self.combo_box = QComboBox()
        self.combo_box.addItem('Model')
        self.combo_box.addItem('Dataset')
        self.combo_box.addItem('Data Augmentation')
        self.combo_box.currentIndexChanged.connect(self.load_file)

        self.chat_button = QPushButton('Chat')
        self.chat_button.setStyleSheet('QPushButton {background-color: #A3C1DA; color: red;}')
        self.chat_button.clicked.connect(self.open_chat_window)

        self.combo_box = QComboBox()
        self.combo_box.addItem('Model')
        self.combo_box.addItem('Dataset')
        self.combo_box.addItem('Data Augmentation')
        self.combo_box.currentIndexChanged.connect(self.load_file)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.text_edit_1)
        splitter.addWidget(self.text_edit_2)

        layout = QVBoxLayout()
        # layout.addWidget(self.open_button)
        # layout.addWidget(self.save_button)
        # layout.addWidget(self.chat_button)  # Add the chat button to the layout
        # layout.addWidget(self.combo_box)
        layout.addWidget(splitter)
        layout.addWidget(self.chat_button)

        # Adjust the layout setup
        self.main_widget.setLayout(layout)

    def open_chat_window(self):
        api_key = self.ask_api_key()
        if api_key is not None:
            self.chat_window = ChatWindow(self, api_key)
            self.chat_window.show()

    # other functions remain same...
    def open_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'All Files (*);;Text Files (*.txt)', options=options)
        if file_name:
            self.file_name = file_name
            with open(file_name, 'r') as f:
                content = f.read()
            self.text_edit_1.setText(content)

    def save_file(self):
        if self.file_name:
            with open(self.file_name, 'w') as f:
                content = self.text_edit_1.toPlainText()
                f.write(content)
        else:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'All Files (*);;Text Files (*.txt)', options=options)
            if file_name:
                with open(file_name, 'w') as f:
                    content = self.text_edit_1.toPlainText()
                    f.write(content)

    def load_file(self, param):
        file_map = {'Model': 'Model.txt', 'Dataset': 'Dataset.txt', 'Data Augmentation': 'DataAugmentation.txt'}
        print(param)
        try:
            with open(file_map[param], 'r', encoding='utf-8') as f:
                file_content = f.read()
            self.text_edit_2.setText(file_content)
        except FileNotFoundError:
            self.text_edit_2.setText("File '{}' not found.".format(file_map[param]))

def main():
    app = QApplication(sys.argv)

    editor = TwoColumnEditor()
    editor.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
