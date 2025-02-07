# import sqlite3
# import os

# DB_NAME = "contacts.db"

# def setup_database():
#     create_tables = not os.path.exists(DB_NAME)
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
    
#     # Create contacts table (note: priority field can be used for either numeric priority or a text value)
#     cursor.execute('''CREATE TABLE IF NOT EXISTS contacts (
#                         id INTEGER PRIMARY KEY AUTOINCREMENT,
#                         name TEXT,
#                         position TEXT,
#                         email TEXT,
#                         country TEXT,
#                         priority TEXT)''')
    
#     # Create settings table
#     cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
#                         id INTEGER PRIMARY KEY AUTOINCREMENT,
#                         frequency TEXT,
#                         time TEXT)''')
    
#     # Create country_priority table
#     cursor.execute('''CREATE TABLE IF NOT EXISTS country_priority (
#                         id INTEGER PRIMARY KEY AUTOINCREMENT,
#                         country TEXT UNIQUE,
#                         priority INTEGER)''')
    
#     conn.commit()
#     conn.close()

# def add_contact_to_db(name, position, email, country, priority):
#     """
#     priority: For contacts this can be a numeric value or a text representing the contact level.
#     """
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("INSERT INTO contacts (name, position, email, country, priority) VALUES (?, ?, ?, ?, ?)",
#                    (name, position, email, country, priority))
#     conn.commit()
#     conn.close()

# def get_all_contacts():
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM contacts")
#     contacts = cursor.fetchall()
#     conn.close()
#     return contacts

# def update_contact_in_db(contact_id, name, position, email, country, priority):
#     """
#     Update a contact's details based on its ID.
#     """
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute(
#         "UPDATE contacts SET name = ?, position = ?, email = ?, country = ?, priority = ? WHERE id = ?",
#         (name, position, email, country, priority, contact_id)
#     )
#     conn.commit()
#     conn.close()

# def delete_contact_from_db(contact_id):
#     """
#     Delete a contact from the database by its ID.
#     """
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
#     conn.commit()
#     conn.close()

# def get_settings():
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("SELECT frequency, time FROM settings LIMIT 1")
#     result = cursor.fetchone()
#     conn.close()
#     # Return default values if no settings are found.
#     return result if result else ([], "13:00")

# def set_settings(frequency, time):
#     """
#     frequency: a list of frequency values (will be stored as a comma separated string)
#     time: time string in format HH:MM
#     """
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("DELETE FROM settings")
#     cursor.execute("INSERT INTO settings (frequency, time) VALUES (?, ?)", (','.join(frequency), time))
#     conn.commit()
#     conn.close()

# def set_country_priority(country, priority):
#     """
#     Insert or update the priority for a country.
#     Uses an UPSERT approach by taking advantage of the UNIQUE constraint on the country field.
#     """
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute(
#         "INSERT OR REPLACE INTO country_priority (country, priority) VALUES (?, ?)",
#         (country, priority)
#     )
#     conn.commit()
#     conn.close()

# def get_country_priorities():
#     """
#     Return a list of tuples (country, priority) for all countries in the database.
#     """
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("SELECT country, priority FROM country_priority")
#     priorities = cursor.fetchall()
#     conn.close()
#     return priorities

# # Ensure that the database is set up when this module is imported.
# setup_database()


import sqlite3
import os

DB_NAME = "contacts.db"

def setup_database():
    create_tables = not os.path.exists(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Contacts table: priority is stored as TEXT (contact level)
    cursor.execute('''CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        position TEXT,
                        email TEXT,
                        country TEXT,
                        priority TEXT)''')
    
    # Settings table
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        frequency TEXT,
                        time TEXT)''')
    
    # Country priority table
    cursor.execute('''CREATE TABLE IF NOT EXISTS country_priority (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        country TEXT UNIQUE,
                        priority INTEGER)''')
    
    # Analytics table: records events when a contact is selected or emailed.
    cursor.execute('''CREATE TABLE IF NOT EXISTS analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contact_id INTEGER,
                        event_type TEXT,   -- "selected" or "emailed"
                        country TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
    
    conn.commit()
    conn.close()

def add_contact_to_db(name, position, email, country, priority):
    """
    priority: For contacts this can be a text representing the contact level.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO contacts (name, position, email, country, priority) VALUES (?, ?, ?, ?, ?)",
                   (name, position, email, country, priority))
    conn.commit()
    conn.close()

def get_all_contacts():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts")
    contacts = cursor.fetchall()
    conn.close()
    return contacts

def update_contact_in_db(contact_id, name, position, email, country, priority):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE contacts SET name = ?, position = ?, email = ?, country = ?, priority = ? WHERE id = ?",
        (name, position, email, country, priority, contact_id)
    )
    conn.commit()
    conn.close()

def delete_contact_from_db(contact_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()

def get_settings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT frequency, time FROM settings LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    # Return default values if no settings are found.
    return result if result else ([], "13:00")

def set_settings(frequency, time):
    """
    frequency: a list of frequency values (will be stored as a comma separated string)
    time: time string in format HH:MM
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings")
    cursor.execute("INSERT INTO settings (frequency, time) VALUES (?, ?)", (','.join(frequency), time))
    conn.commit()
    conn.close()

def set_country_priority(country, priority):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO country_priority (country, priority) VALUES (?, ?)",
        (country, priority)
    )
    conn.commit()
    conn.close()

def get_country_priorities():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT country, priority FROM country_priority")
    priorities = cursor.fetchall()
    conn.close()
    return priorities

# ---------------------------
# New Analytics Functions
# ---------------------------

def record_contact_event(contact_id, country, event_type):
    """
    Records an event for a contact.
    :param contact_id: ID of the contact
    :param country: The contact's country
    :param event_type: A string, either "selected" or "emailed"
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO analytics (contact_id, event_type, country) VALUES (?, ?, ?)",
                   (contact_id, event_type, country))
    conn.commit()
    conn.close()

def get_analytics_summary():
    """
    Returns aggregated analytics data.
    The result is a list of tuples: (country, selected_count, emailed_count)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Use conditional aggregation to count events by type per country.
    cursor.execute("""
        SELECT 
            country,
            SUM(CASE WHEN event_type = 'selected' THEN 1 ELSE 0 END) AS selected_count,
            SUM(CASE WHEN event_type = 'emailed' THEN 1 ELSE 0 END) AS emailed_count
        FROM analytics
        GROUP BY country
    """)
    summary = cursor.fetchall()
    conn.close()
    return summary

# Ensure the database is set up when this module is imported.
setup_database()
