import sys
import random
import time
import threading
import schedule
import numpy as np
import os
import json

# user_file = "user.json"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QStackedWidget, QSpinBox, QFormLayout, QDialog,QRadioButton,
     QTextEdit,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QTime, QDate, QDateTime

# Imported functions (assumed implemented elsewhere)
from database import (
    add_contact_to_db, get_all_contacts, get_settings, set_settings, update_contact_in_db, delete_contact_from_db, set_country_priority, get_country_priorities, get_analytics_summary, record_contact_event
)

from email_utils import email_template, save_email_template, load_email_template

from utils import MultiComboBox
from win32com.client import Dispatch

# =============================================================================
# Page 1: New Contact Page
# =============================================================================
class NewContactPage(QWidget):
    def __init__(self, refresh_contacts_callback):
        """
        refresh_contacts_callback: function to call after a new contact is added
        """
        super().__init__()
        self.refresh_contacts_callback = refresh_contacts_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Add New Contact")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Name Entry
        self.name_entry = self.create_input(layout, "Name")

        # Position (searchable dropdown using MultiComboBox)
        self.position_options = ["Manager", "Developer", "Designer"]
        self.position_select = self.create_multiselect_dropdown(layout, "Position", self.position_options)

        # Email Entry
        self.email_entry = self.create_input(layout, "Email")

        # Country (searchable dropdown)
        self.country_options = ["USA", "Canada", "UK", "Germany"]
        self.country_select = self.create_multiselect_dropdown(layout, "Country", self.country_options)

        # Contact Level (instead of a numeric priority for the person)
        layout.addWidget(QLabel("Contact Level"))
        self.level_select = QComboBox()
        self.level_select.addItems(["First Contact", "Second Contact", "Third Contact"])
        layout.addWidget(self.level_select)

        # Add Contact Button
        add_button = QPushButton("Add Contact")
        add_button.clicked.connect(self.add_contact)
        layout.addWidget(add_button)
        layout.addStretch()

    def create_input(self, layout, label_text):
        layout.addWidget(QLabel(label_text))
        entry = QLineEdit()
        layout.addWidget(entry)
        return entry

    def create_multiselect_dropdown(self, layout, label, options):
        layout.addWidget(QLabel(label))
        # Using MultiComboBox if available; otherwise you can substitute with QComboBox
        multi_combo_box = MultiComboBox()  
        multi_combo_box.addItems(options)
        multi_combo_box.setMinimumWidth(200)
        layout.addWidget(multi_combo_box)
        return multi_combo_box

    def add_contact(self):
        name = self.name_entry.text()
        position = self.position_select.currentText()
        email = self.email_entry.text()
        country = self.country_select.currentText()
        contact_level = self.level_select.currentText()  # e.g. "First Contact"

        if not (name and position and email and country and contact_level):
            QMessageBox.critical(self, "Error", "Please fill all fields correctly.")
            return

        # Use external function; note that add_contact_to_db is assumed to accept the contact_level.
        add_contact_to_db(name, position, email, country, contact_level)
        QMessageBox.information(self, "Success", "Contact added successfully.")

        # Clear fields after adding contact (optional)
        self.name_entry.clear()
        self.email_entry.clear()
        # Also refresh any tables that display contacts
        self.refresh_contacts_callback()

class ManageContactsPage(QWidget):
    def __init__(self, refresh_callback):
        """
        refresh_callback: a function that is called whenever the dataset is updated.
        """
        super().__init__()
        self.refresh_callback = refresh_callback
        self.selected_contact_id = None  # will hold the id of the currently selected contact
        self.all_contacts = []  # store all contacts from the database
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top Layout: Title and external Edit/Delete buttons
        top_layout = QHBoxLayout()
        title = QLabel("Manage Contacts")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        top_layout.addWidget(title)
        top_layout.addStretch()

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_selected_contact)
        top_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_selected_contact)
        top_layout.addWidget(self.delete_button)
        main_layout.addLayout(top_layout)

        # Filtering Layout: One QLineEdit per filterable column
        filter_layout = QHBoxLayout()

        self.filter_name = QLineEdit()
        self.filter_name.setPlaceholderText("Filter by Name")
        self.filter_name.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_name)

        self.filter_position = QLineEdit()
        self.filter_position.setPlaceholderText("Filter by Position")
        self.filter_position.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_position)

        self.filter_email = QLineEdit()
        self.filter_email.setPlaceholderText("Filter by Email")
        self.filter_email.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_email)

        self.filter_country = QLineEdit()
        self.filter_country.setPlaceholderText("Filter by Country")
        self.filter_country.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_country)

        self.filter_level = QLineEdit()
        self.filter_level.setPlaceholderText("Filter by Contact Level")
        self.filter_level.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_level)

        main_layout.addLayout(filter_layout)

        # Table Widget with a "Select" column plus contact details
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Select", "Name", "Position", "Email", "Country", "Contact Level"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        main_layout.addWidget(self.table)

        # Load the data
        self.load_contacts()

    def load_contacts(self):
        """Loads all contacts from the database and applies the current filters."""
        self.all_contacts = get_all_contacts()  # each contact is assumed to be a tuple (id, name, position, email, country, contact_level)
        self.apply_filters()

    def apply_filters(self):
        """Filter the complete dataset based on input in the filter fields."""
        name_filter = self.filter_name.text().lower()
        pos_filter = self.filter_position.text().lower()
        email_filter = self.filter_email.text().lower()
        country_filter = self.filter_country.text().lower()
        level_filter = self.filter_level.text().lower()

        filtered_contacts = []
        for contact in self.all_contacts:
            # contact structure: (id, name, position, email, country, contact_level)
            if (name_filter in contact[1].lower() and
                pos_filter in contact[2].lower() and
                email_filter in contact[3].lower() and
                country_filter in contact[4].lower() and
                level_filter in contact[5].lower()):
                filtered_contacts.append(contact)
        self.populate_table(filtered_contacts)

    def populate_table(self, contacts):
        """Populate the QTableWidget with the given contacts."""
        self.table.setRowCount(0)
        self.selected_contact_id = None  # Reset the selection whenever the table is repopulated.
        for contact in contacts:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            
            # Create a radio button for selecting the contact.
            radio = QRadioButton()
            # Store the contact id in a property.
            radio.contact_id = contact[0]
            radio.toggled.connect(self.on_radio_toggled)
            self.table.setCellWidget(row_position, 0, radio)
            
            # Set the rest of the columns.
            self.table.setItem(row_position, 1, QTableWidgetItem(contact[1]))
            self.table.setItem(row_position, 2, QTableWidgetItem(contact[2]))
            self.table.setItem(row_position, 3, QTableWidgetItem(contact[3]))
            self.table.setItem(row_position, 4, QTableWidgetItem(contact[4]))
            self.table.setItem(row_position, 5, QTableWidgetItem(contact[5]))

    def on_radio_toggled(self):
        """
        Called whenever any radio button is toggled.
        It iterates through the table to find the currently selected contact.
        """
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget and widget.isChecked():
                self.selected_contact_id = widget.contact_id
                return

    def edit_selected_contact(self):
        """Open the edit dialog for the currently selected contact."""
        if self.selected_contact_id is None:
            QMessageBox.information(self, "Select Contact", "Please select a contact to edit.")
            return
        # Open the edit dialog (this dialog is assumed to be defined elsewhere).
        dialog = EditContactDialog(self.selected_contact_id, self.refresh_callback)
        dialog.exec_()
        self.load_contacts()
        self.refresh_callback()

    def delete_selected_contact(self):
        """Delete the currently selected contact after confirmation."""
        if self.selected_contact_id is None:
            QMessageBox.information(self, "Select Contact", "Please select a contact to delete.")
            return
        reply = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this contact?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_contact_from_db(self.selected_contact_id)
            QMessageBox.information(self, "Deleted", "Contact deleted successfully.")
            self.load_contacts()
            self.refresh_callback()


# A simple dialog for editing a contact (assumes update_contact_in_db exists)
class EditContactDialog(QDialog):
    def __init__(self, contact_id, refresh_callback):
        super().__init__()
        self.contact_id = contact_id
        self.refresh_callback = refresh_callback
        self.setWindowTitle("Edit Contact")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        # For simplicity, we reload the contact info from get_all_contacts
        contacts = get_all_contacts()
        self.contact = next((c for c in contacts if c[0] == self.contact_id), None)
        if not self.contact:
            QMessageBox.critical(self, "Error", "Contact not found.")
            self.reject()
            return

        form_layout = QFormLayout()
        self.name_entry = QLineEdit(self.contact[1])
        self.position_entry = QLineEdit(self.contact[2])
        self.email_entry = QLineEdit(self.contact[3])
        self.country_entry = QLineEdit(self.contact[4])
        self.level_entry = QComboBox()
        self.level_entry.addItems(["First Contact", "Second Contact", "Third Contact"])
        # Pre-select the current level
        index = self.level_entry.findText(self.contact[5])
        if index >= 0:
            self.level_entry.setCurrentIndex(index)

        form_layout.addRow("Name:", self.name_entry)
        form_layout.addRow("Position:", self.position_entry)
        form_layout.addRow("Email:", self.email_entry)
        form_layout.addRow("Country:", self.country_entry)
        form_layout.addRow("Contact Level:", self.level_entry)
        layout.addLayout(form_layout)

        # Dialog buttons
        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.save_contact)
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

    def save_contact(self):
        # Assume update_contact_in_db exists (imported from database)
        from database import update_contact_in_db
        name = self.name_entry.text()
        position = self.position_entry.text()
        email = self.email_entry.text()
        country = self.country_entry.text()
        level = self.level_entry.currentText()
        if not (name and position and email and country and level):
            QMessageBox.critical(self, "Error", "Please fill all fields.")
            return

        update_contact_in_db(self.contact_id, name, position, email, country, level)
        QMessageBox.information(self, "Saved", "Contact updated successfully.")
        self.refresh_callback()
        self.accept()


# =============================================================================
# Page 3: Scheduler Page
# =============================================================================

class SchedulerPage(QWidget):
    def __init__(self, show_notification_callback):
        super().__init__()
        self.show_notification_callback = show_notification_callback
        self.init_ui()
        # self.user_file = "user.json"

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.user_file = "user.json"

        title = QLabel("Scheduler Settings")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Frequency (dropdown)
        layout.addWidget(QLabel("Frequency"))
        self.frequency_select = QComboBox()
        self.frequency_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.frequency_select.addItems(self.frequency_options)
        layout.addWidget(self.frequency_select)

        # Time selection (separate hour and minute dropdowns)
        layout.addWidget(QLabel("Time"))
        time_layout = QHBoxLayout()
        
        self.hour_select = QComboBox()
        self.hour_select.addItems([f"{hour:02d}" for hour in range(24)])
        time_layout.addWidget(self.hour_select)
        
        self.minute_select = QComboBox()
        self.minute_select.addItems([f"{minute:02d}" for minute in range(0, 60)])
        time_layout.addWidget(self.minute_select)
        
        layout.addLayout(time_layout)

        # Set Frequency Button
        set_button = QPushButton("Set Frequency")
        set_button.clicked.connect(self.set_frequency)
        layout.addWidget(set_button)

        # Force Notification Button
        force_button = QPushButton("Force Notification")
        force_button.clicked.connect(self.show_notification_callback)
        layout.addWidget(force_button)
        
        # Email Template Editor
        element = QHBoxLayout()
        self.email_edit_label = QLabel("Edit Email Template")
        self.email_edit_label2 = QLabel("TEST")
        self.email_edit_label.setToolTip("Recepient name: {recepient_name}, Country: {country}, Your Name: {user_name}, Available times: {times_formatted}")
        element.addWidget(self.email_edit_label) # Change str to Alignment Type - first improt
        # element.addWidget(self.email_edit_label2,0,"Qt::AlignRight")
        # layout.addWidget(self.email_edit_label)
        layout.addLayout(element)
        
        self.email_editor = QTextEdit()
        self.email_editor.setText(load_email_template(self.user_file))  # Load existing template
        layout.addWidget(self.email_editor)
        
        # Save Email Template Button
        save_button = QPushButton("Save Email Template")
        save_button.clicked.connect(self.save_email_template)
        layout.addWidget(save_button)

        layout.addStretch()

    def set_frequency(self):
        frequency = self.frequency_select.currentText()
        time_str = f"{self.hour_select.currentText()}:{self.minute_select.currentText()}"
        set_settings([frequency], time_str)
        QMessageBox.information(self, "Success", f"Frequency updated! Notifications scheduled for {frequency} at {time_str}.")

    def save_email_template(self):
        content = self.email_editor.toPlainText()
        save_email_template(content,self.user_file)
        QMessageBox.information(self, "Success", "Email template saved successfully!")


# =============================================================================
# Page 4: Analytics Page
# =============================================================================

class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Optionally, update the analytics data every time the page is shown.
        self.update_analytics()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        header_layout = QHBoxLayout()
        title = QLabel("Analytics")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.update_analytics)
        header_layout.addWidget(refresh_button)

        self.layout.addLayout(header_layout)

        # Table to display analytics data
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Country", "Contacts Selected", "Contacts Emailed"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.layout.addWidget(self.table)

        self.layout.addStretch()

    def update_analytics(self):
        """
        Query the database for analytics summary and update the table.
        """
        summary = get_analytics_summary()  # List of tuples: (country, selected_count, emailed_count)
        self.table.setRowCount(0)
        for country, selected_count, emailed_count in summary:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(country))
            self.table.setItem(row, 1, QTableWidgetItem(str(selected_count)))
            self.table.setItem(row, 2, QTableWidgetItem(str(emailed_count)))



# =============================================================================
# Page 5: Country Priority Page
# =============================================================================
class CountryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title = QLabel("Country Priorities")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title)

        # Form for setting a country’s priority
        form_layout = QFormLayout()
        self.country_select = QComboBox()
        self.country_select.addItems(["USA", "Canada", "UK", "Germany"])  # Update as needed
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 5)
        form_layout.addRow("Country:", self.country_select)
        form_layout.addRow("Priority (1-5):", self.priority_spin)
        main_layout.addLayout(form_layout)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_country_priority)
        main_layout.addWidget(submit_button)

        # Table to show current country priorities
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Country", "Priority"])
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        self.load_country_priorities()
        main_layout.addStretch()

    def submit_country_priority(self):
        country = self.country_select.currentText()
        priority = self.priority_spin.value()
        # Assume set_country_priority is implemented externally to update the database.
        from database import set_country_priority
        set_country_priority(country, priority)
        QMessageBox.information(self, "Success", f"Priority for {country} updated to {priority}.")
        self.load_country_priorities()

    def load_country_priorities(self):
        # Assume get_country_priorities returns a list of tuples: (country, priority)
        from database import get_country_priorities
        priorities = get_country_priorities()
        self.table.setRowCount(0)
        for country, priority in priorities:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(country))
            self.table.setItem(row, 1, QTableWidgetItem(str(priority)))


# =============================================================================
# Main Window with Sidebar Navigation and Page Switching
# =============================================================================
class MainWindow(QMainWindow):
    # notification_requested = Signal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contact Notifier")
        self.setGeometry(100, 100, 1000, 600)
        self.contacts = []  # Cache contacts if needed
        
        # get user settings from user.json
        self.user_file = "user.json"
        
        # Main container widget and layout
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QHBoxLayout()
        container.setLayout(main_layout)

        # Sidebar navigation
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Stacked widget for pages
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages, 1)  # stretch factor so pages expand

        # Create pages
        self.new_contact_page = NewContactPage(self.refresh_contacts)
        self.manage_contacts_page = ManageContactsPage(self.refresh_contacts)
        # self.scheduler_page = SchedulerPage(self.show_notification)
        
        self.scheduler_page = SchedulerPage(self.show_notification)

        
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.schedule_notification)
        self.notification_timer.start(10)  # check every 30 seconds
        
        self.pushed_today = False
        
        self.analytics_page = AnalyticsPage()
        self.country_page = CountryPage()

        # Add pages to the stacked widget
        self.pages.addWidget(self.new_contact_page)       # index 0
        self.pages.addWidget(self.manage_contacts_page)     # index 1
        self.pages.addWidget(self.scheduler_page)           # index 2
        self.pages.addWidget(self.analytics_page)           # index 3
        self.pages.addWidget(self.country_page)             # index 4

        # Start the scheduler thread
        threading.Thread(target=self.run_scheduler, daemon=True).start()
        # self.run_scheduler()

    
    def create_sidebar(self):
        sidebar = QWidget()
        layout = QVBoxLayout()
        sidebar.setLayout(layout)

        # Buttons for navigation
        buttons = [
            ("New Contact", 0),
            ("Manage Contacts", 1),
            ("Scheduler", 2),
            ("Analytics", 3),
            ("Country", 4),
        ]
        for text, index in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, idx=index: self.pages.setCurrentIndex(idx))
            layout.addWidget(btn)
        layout.addStretch()
        return sidebar

    def refresh_contacts(self):
        # Refresh contacts on pages that display them
        self.manage_contacts_page.load_contacts()
        # Also update internal contacts list used for notification selection
        self.contacts = get_all_contacts()

    def run_scheduler(self):
        # This thread will run scheduled tasks without blocking the UI.
        while True:
            schedule.run_pending()
            time.sleep(1)

    def schedule_notification(self):
        # # Retrieve frequency settings from database (assumed implemented)
        # frequency = get_settings("frequency")
        # time_str = get_settings("time")
        # # In this example, we schedule the notification daily at the specified time.
        # schedule.every().day.at(time_str).do(self.show_notification)
        """
        Retrieve frequency settings from the database and schedule a notification job.
        The frequency is expected to be a day name ("Monday", "Tuesday", etc.)
        and the time is in "HH:MM" format (local time).
        """
        # Retrieve settings (note: our set_settings stores frequency as a comma separated string,
        # but here we assume that only one frequency is selected)
        
        dt_now = QDateTime.currentDateTime().toString("dddd,hh:mm").lower().split(",")
        date_now = dt_now[0]
        time_now = dt_now[1]
        
        if self.pushed_today:
            if time_now == "00:00":
                self.pushed_today = False
        
        if not self.pushed_today:
            frequency, time_str = get_settings()  # e.g., (["Monday"], "13:00")

            #print(frequency, time_str)
            if not frequency:
                # No frequency was set; you might decide to schedule a default or do nothing.
                return

            # for day in frequency:
            day = frequency.lower()
            day = day.lower()
            if date_now == day:
                if time_now == time_str:
                    self.show_notification()
                    self.pushed_today = True
                    # time.sleep(3)

    def show_notification(self):
        # Reload contacts
        self.contacts = get_all_contacts()
        if not self.contacts:
            QMessageBox.information(self, "Notification", "No contacts available to notify.")
            return

        # --- New Notification Selection Logic ---
        # 1. Group contacts by country.
        contacts_by_country = {}
        for contact in self.contacts:
            # Assuming contact structure: (id, name, position, email, country, contact_level)
            country = contact[4]
            contacts_by_country.setdefault(country, []).append(contact)

        if not contacts_by_country:
            QMessageBox.information(self, "Notification", "No contacts available.")
            return

        # 2. Retrieve country priorities.
        # Assume get_country_priorities returns a list of tuples: (country, priority)
        from database import get_country_priorities
        country_priority_dict = dict(get_country_priorities())
        # For any country not set, assume a default priority value (e.g., 3)
        default_priority = 3
        countries = list(contacts_by_country.keys())
        weights = []
        for country in countries:
            # Lower numeric priority means higher importance; we use (6 - priority) as weight.
            cp = country_priority_dict.get(country, default_priority)
            weights.append(6 - cp)

        # 3. Randomly select a country using the weights.
        selected_country = random.choices(countries, weights=weights, k=1)[0]

        # 4. Within that country, select a contact based on contact level priority.
        # Preferred order: First Contact > Second Contact > Third Contact.
        candidates = contacts_by_country[selected_country]
        preferred_order = ["First Contact", "Second Contact", "Third Contact"]
        selected_contact = None
        for level in preferred_order:
            level_candidates = [c for c in candidates if c[5] == level]
            if level_candidates:
                selected_contact = random.choice(level_candidates)
                break
        if not selected_contact:
            # Fallback: choose any contact
            selected_contact = random.choice(candidates)

        # 5. Create and show the notification popup.
        self.show_notification_popup(selected_contact)

    def show_notification_popup(self, contact):
        # Record that this contact has been selected.
        record_contact_event(contact[0], contact[4], "selected")

        popup = QDialog(self)
        popup.setWindowTitle("Contact Reminder")
        popup.setModal(True)
        popup.resize(400, 300)

        layout = QVBoxLayout()
        popup.setLayout(layout)

        title = QLabel("Contact to Reach Out")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        info_label = QLabel(f"Name: {contact[1]}\n"
                            f"Position: {contact[2]}\n"
                            f"Email: {contact[3]}\n"
                            f"Country: {contact[4]}\n"
                            f"Contact Level: {contact[5]}")
        layout.addWidget(info_label)

        email_button = QPushButton("Email")
        # When the user clicks the Email button, record that event and send email.
        email_button.clicked.connect(lambda: [self.send_email(contact),
                                                record_contact_event(contact[0], contact[4], "emailed")])
        layout.addWidget(email_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(popup.accept)
        layout.addWidget(close_button)

        popup.exec_()

    def send_email(self, contact):
        mail_to, subject, body = email_template(contact,self.user_file)
        try:
            outlook = Dispatch("outlook.application")
            mail = outlook.CreateItem(0)
            mail.To = mail_to #contact[3]  # Assuming email is at index 3
            mail.Subject = subject #"Hello"
            mail.Body = body #"This is a reminder to connect."
            mail.Display()
        except Exception as e:
            QMessageBox.critical(self, "Email Error", f"Failed to send email: {e}")

