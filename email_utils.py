import win32com.client
import pytz
from datetime import datetime, timedelta
from win32com.client import constants
import os
import json

def get_free_time_slots():
    """
    Retrieves free time slots from the Outlook calendar and merges consecutive slots.
    Excludes weekends and the current day.
    :return: dict - Dictionary of available time slots grouped by day
    """
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    calendar = namespace.GetDefaultFolder(9)  # 9 represents the Calendar folder
    
    tz = pytz.timezone("Etc/UTC")  # Adjust to your local timezone if necessary
    now = datetime.now(tz)
    end_time = now + timedelta(days=7)  # Checking availability for the next 7 days
    
    appointments = calendar.Items
    appointments.Sort("[Start]")
    appointments = appointments.Restrict(f"[Start] >= '{now.strftime('%m/%d/%Y %I:%M %p')}' AND [End] <= '{end_time.strftime('%m/%d/%Y %I:%M %p')}'")
    
    busy_slots = [(appt.Start.replace(tzinfo=tz), appt.End.replace(tzinfo=tz)) for appt in appointments]
    
    free_slots = {}
    current_time = now.replace(hour=9, minute=0, second=0, microsecond=0)  # Start at 9 AM
    current_weekday = now.weekday()  # 0 = Monday, 6 = Sunday
    
    while current_time < end_time:
        next_time = current_time + timedelta(hours=1)
        day_name = current_time.strftime('%A')
        day_date = current_time.strftime('%B %d')
        day = f"{day_name}, {day_date}"
        
        if current_time.date() > now.date() and current_time.weekday() < 5:  # Skip today and weekends
            if all(not (start <= current_time < end) for start, end in busy_slots):
                if day not in free_slots:
                    free_slots[day] = []
                
                if free_slots[day] and free_slots[day][-1].split(' - ')[1] == current_time.strftime('%I:%M %p'):
                    free_slots[day][-1] = free_slots[day][-1].split(' - ')[0] + f" - {next_time.strftime('%I:%M %p')}"
                else:
                    free_slots[day].append(f"{current_time.strftime('%I:%M %p')} - {next_time.strftime('%I:%M %p')}")
        
        current_time = next_time
        if current_time.hour >= 17:
            current_time = current_time.replace(hour=9) + timedelta(days=1)  # Next day's working hours
    
    return free_slots

def get_outlook_user_details():
    """
    Retrieves the current user's name and email signature from Outlook.
    :return: tuple - (user_name, email_signature)
    """
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    user_name = [x.strip() for x in namespace.CurrentUser.Name.split(",")] 
    user_name = f"{user_name[1][0].upper()}{user_name[1][1:].lower()} {user_name[0][0].upper()}{user_name[0][1:].lower()}"
    return user_name


def email_body(recipient_name, country,user_file):
    """
    Generates a formal email template for scheduling a meeting.
    :param recipient_name: str - Name of the recipient
    :param meeting_times: list - List of available time slots
    :return: str - Formatted email string
    """
    meeting_times = get_free_time_slots()
    times_formatted = "\n".join(f"\n{day}:\n" + "\n".join(f"- {time}" for time in times) for day, times in meeting_times.items())
    user_name = get_outlook_user_details()
    
    body = load_email_template(user_file)
    if body != "":
        body = body.format(recipient_name=recipient_name,country=country,
                           times_formatted=times_formatted,user_name=user_name)
    else:
        body = f"""Dear {recipient_name},\n\nI hope this email finds you well. I work for Morgan Stanley Investment Management on the Emerging Markets Debt team and we're investors in {country}. We are interested in recent economic developments in the county and are looking to schedule a meeting.\nPlease find my availability below:\n{times_formatted}\n\nKindly let me know which of these works best for you, or if you have any alternative preferences.\n\nThank you and best regards,\n{user_name}"""
    
    return body

def save_email_template(content, user_file):
    """ Saves the email template to a JSON file """
    with open(user_file, "w", encoding="utf-8") as file:
        json.dump({"email_body": content}, file, indent=4)

def load_email_template(template_file):
    """ Loads the email template from a JSON file """
    try:
        if os.path.exists(template_file):
            with open(template_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("email_body", "")
        return ""  # Return empty string if file doesn't exist
    except:
        return ""
    
def email_template(contact, user_file):
    mail_to = contact[3]
    subject = f"Morgan Stanley Investment Management Investor Meeting"
    body = email_body(recipient_name=contact[1], country=contact[4],user_file=user_file)
    return mail_to, subject, body
    