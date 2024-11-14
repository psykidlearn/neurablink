from PyQt5 import QtWidgets, QtGui, QtCore
import keyboard

class BlurWindow(QtWidgets.QWidget):
    def __init__(self, screen):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowTransparentForInput)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        # Get screen size
        self.setGeometry(screen.geometry())

        # Timer for gradual blur
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.increase_opacity)

        # Opacity settings
        self.opacity_level = 0
        self.max_opacity_level = 155  # Maximum opacity level
        self.opacity_step = 3  # Opacity increment per step

        # Timer for initial delay
        self.initial_delay_timer = QtCore.QTimer()
        self.initial_delay_timer.timeout.connect(self.start_opacity_increase)
        self.initial_delay_seconds = 5  # Delay in seconds before opacity starts increasing

        # Start the initial delay timer
        self.initial_delay_timer.start(self.initial_delay_seconds * 1000)

    def start_opacity_increase(self):
        self.initial_delay_timer.stop()
        self.timer.start(50)  # Start the opacity increase timer

    @QtCore.pyqtSlot()
    def reset_opacity(self):
        self.opacity_level = 0
        self.timer.stop()  # Stop the opacity increase timer
        self.initial_delay_timer.start(self.initial_delay_seconds * 1000)  # Restart the initial delay timer
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, self.opacity_level))
        painter.end()
    
    def increase_opacity(self): 
        if self.opacity_level < self.max_opacity_level:
            self.opacity_level += self.opacity_step
            self.update()
        else:
            self.timer.stop()

def reset_all_windows(blur_windows):  
    for window in blur_windows:
        # Use invokeMethod to ensure the method is called in the correct thread
        QtCore.QMetaObject.invokeMethod(window, "reset_opacity", QtCore.Qt.QueuedConnection)

def main():
    app = QtWidgets.QApplication([])
    blur_windows = []
    for screen in app.screens():
        blur_window = BlurWindow(screen)
        blur_window.setGeometry(screen.geometry())  # Set the geometry to the screen's geometry
        blur_window.showFullScreen()  # Show the window in full screen mode
        blur_windows.append(blur_window)
 
    keyboard.add_hotkey('space', reset_all_windows, args=(blur_windows,))
    app.exec_()

if __name__ == "__main__":
    main() 