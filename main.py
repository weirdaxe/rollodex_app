import sys
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from database import setup_database
from gui import MainWindow #ContactNotifierApp

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        menu = QMenu(parent)
        exitAction = menu.addAction("Exit")
        menu.setStyleSheet("""
    QMenu::item {
        icon: none;
        padding-left: 8px;
        padding-right: 8px;
        padding-top: 4px;
        padding-bottom: 4px;
        margin-right: 10px;
    }
""")
        self.setContextMenu(menu)
        menu.triggered.connect(self.exit)

        
    def exit(self):
        QApplication.exit()                          
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev & PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
        
def main():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    
    window = MainWindow() #ContactNotifierApp()
    w = QWidget()
    icon_path = resource_path("phone_app.png")
    trayIcon = SystemTrayIcon(QIcon(icon_path), window)
    
    window = MainWindow()  #ContactNotifierApp()
    
    def on_window_close(event):
        event.ignore()
        window.hide()  # Minimize the window to tray
    
    def on_tray_icon_click(reason):
        if reason == QSystemTrayIcon.Trigger:  # Left-click on the tray icon
            window.show()  # Restore the window
            
    window.closeEvent = on_window_close
    
    window.show()
    trayIcon.show()
    trayIcon.activated.connect(on_tray_icon_click)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()




# import sys
# from PySide6.QtWidgets import QApplication
# from database import setup_database
# from gui import ContactNotifierApp

# if __name__ == "__main__":
#     setup_database()
    
#     if not QApplication.instance():
#         app = QApplication(sys.argv)
#     else:
#         app = QApplication.instance()
    
#     window = ContactNotifierApp()
#     window.show()
#     sys.exit(app.exec())


# import sys
# from PySide6.QtCore import Qt
# from PySide6.QtWidgets import QApplication, QMainWindow, QMenu
# from PySide6.QtGui import QIcon, QAction
# from PySide6.QtWidgets import QSystemTrayIcon

# from database import setup_database
# from gui import ContactNotifierApp


# class TrayApplication(QApplication):
#     def __init__(self, sys_argv):
#         super().__init__(sys_argv)
#         self.tray_icon = None

#     def create_tray_icon(self, window):
#         tray_icon = QSystemTrayIcon(QIcon("phone_app.png"), self)  # Provide path to your icon
#         tray_icon.setToolTip("Your App Name")
        
#         # Creating the tray menu
#         tray_menu = QMenu()
#         exit_action = QAction("Exit")
#         exit_action.triggered.connect(self.quit)
#         tray_menu.addAction(exit_action)
        
#         tray_icon.setContextMenu(tray_menu)

#         # Show the tray icon
#         tray_icon.show()

#         # Handle the app close event to minimize the window to the tray
#         window.closeEvent = self.on_window_close

#         self.tray_icon = tray_icon

#     def on_window_close(self, event):
#         # Prevent the window from actually closing
#         event.ignore()
#         window.hide()  # Minimize the window to tray


# if __name__ == "__main__":
#     setup_database()

#     if not QApplication.instance():
#         app = TrayApplication(sys.argv)
#     else:
#         app = QApplication.instance()

#     window = ContactNotifierApp()

#     # Create tray icon and menu
#     app.create_tray_icon(window)

#     window.show()
#     sys.exit(app.exec())



# import sys
# from PySide6.QtCore import Qt, QCoreApplication
# from PySide6.QtWidgets import QApplication, QMenu, QWidget, QSystemTrayIcon
# from PySide6.QtGui import QIcon, QAction
# from database import setup_database
# from gui import ContactNotifierApp

# class TrayApplication(QApplication):
#     def __init__(self, sys_argv, parent=None):
#         super().__init__(sys_argv,parent)
#         self.tray_icon = None

#     def create_tray_icon(self, window):
#         # Create tray icon with an icon
#         tray_icon = QSystemTrayIcon(QIcon("phone_app.png"), self)
#         tray_icon.setToolTip("Your App Name")

#         # Create a context menu for the tray icon (Right-click menu) with window as parent
#         tray_menu = QMenu(window)  # Assign `window` as the parent of the QMenu

#         # Create "Open" action
#         open_action = QAction("Open")
#         open_action.triggered.connect(window.show)
#         tray_menu.addAction(open_action)

#         # Create "Exit" action
#         exit_action = QAction("Exit")
#         exit_action.triggered.connect(self.exit)  # Use self.exit to cleanly exit the app
#         tray_menu.addAction(exit_action)

#         # Set the context menu for right-click
#         tray_icon.setContextMenu(tray_menu)

#         # Show the tray icon
#         tray_icon.show()

#         # Left-click behavior: Show the window when clicked
#         tray_icon.activated.connect(self.on_tray_icon_click)

#         # Handle the app close event to minimize the window to the tray
#         window.closeEvent = self.on_window_close

#         self.tray_icon = tray_icon

#     def on_window_close(self, event):
#         # Prevent the window from actually closing
#         event.ignore()
#         window.hide()  # Minimize the window to tray

#     def on_tray_icon_click(self, reason):
#         if reason == QSystemTrayIcon.Trigger:  # Left-click on the tray icon
#             window.show()  # Restore the window

#     def exit(self):
#         # Cleanly exit the application when the "Exit" action is triggered
#         QCoreApplication.quit()
#         if self.tray_icon:
#             self.tray_icon.hide()  # Hide the tray icon before exiting

# if __name__ == "__main__":
#     setup_database()

#     if not QApplication.instance():
#         app = TrayApplication(sys.argv)
#     else:
#         app = QApplication.instance()

#     window = ContactNotifierApp()

#     # Create tray icon and menu
#     app.create_tray_icon(window)

#     window.show()
#     sys.exit(app.exec())



# import sys
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QIcon, QAction
# from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
# from database import setup_database
# from gui import ContactNotifierApp

# class SystemTrayIcon(QSystemTrayIcon):
#     def __init__(self, icon, parent=None):
#         super().__init__(icon, parent)
#         menu = QMenu(parent)
#         exitAction = menu.addAction("Exit")
#         self.setContextMenu(menu)
#         menu.triggered.connect(self.exit)

        
#     def exit(self):
#         QApplication.exit()                          
            
# def main():
#     if not QApplication.instance():
#         app = QApplication(sys.argv)
#     else:
#         app = QApplication.instance()
    
#     window = ContactNotifierApp()
#     w = QWidget()
#     trayIcon = SystemTrayIcon(QIcon("phone_app.png"), window)
    
#     window = ContactNotifierApp()
    
#     def on_window_close(event):
#         event.ignore()
#         window.hide()  # Minimize the window to tray
    
#     def on_tray_icon_click(reason):
#         if reason == QSystemTrayIcon.Trigger:  # Left-click on the tray icon
#             window.show()  # Restore the window
            
#     window.closeEvent = on_window_close
    
#     window.show()
#     trayIcon.show()
#     trayIcon.activated.connect(on_tray_icon_click)
    
#     sys.exit(app.exec())

# if __name__ == '__main__':
#     main()
