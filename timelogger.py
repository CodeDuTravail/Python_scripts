#!/usr/bin/env python3
"""
Work Hours Logger
A simple script to log work start/end times and calculate hours worked.
Configurable lunch break duration.
Enhanced with 35-hour weekly rule exception.
"""

import datetime
import os
import json
from typing import Dict, List, Optional, Tuple

class WorkLogger:
    def __init__(self, data_file: str = "work_log.json"):
        self.data_file = data_file
        self.load_data()
    
    def load_data(self):
        """Load existing work log data from file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.data = {}
        else:
            self.data = {}
        
        # Ensure settings exist with default values
        if 'settings' not in self.data:
            self.data['settings'] = {'lunch_break_minutes': 30}
        elif 'lunch_break_minutes' not in self.data['settings']:
            self.data['settings']['lunch_break_minutes'] = 30
    
    def save_data(self):
        """Save work log data to file."""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_lunch_break_minutes(self) -> int:
        """Get the current lunch break duration in minutes."""
        return self.data['settings']['lunch_break_minutes']
    
    def set_lunch_break_minutes(self, minutes: int):
        """Set the lunch break duration in minutes."""
        self.data['settings']['lunch_break_minutes'] = minutes
        self.save_data()
    
    def configure_lunch_break(self):
        """Allow user to configure lunch break duration."""
        current_minutes = self.get_lunch_break_minutes()
        current_hours = current_minutes // 60
        current_mins = current_minutes % 60
        
        print(f"\n--- Configure Lunch Break ---")
        print(f"Current lunch break: {current_hours}h {current_mins}m ({current_minutes} minutes)")
        print("\nCommon options:")
        print("1. No lunch break (0 minutes)")
        print("2. Short break (15 minutes)")
        print("3. Standard break (30 minutes)")
        print("4. Long break (45 minutes)")
        print("5. One hour break (60 minutes)")
        print("6. Custom duration")
        print("7. Cancel")
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        new_minutes = None
        
        if choice == '1':
            new_minutes = 0
        elif choice == '2':
            new_minutes = 15
        elif choice == '3':
            new_minutes = 30
        elif choice == '4':
            new_minutes = 45
        elif choice == '5':
            new_minutes = 60
        elif choice == '6':
            custom_input = input("Enter custom lunch break duration in minutes (0-120): ").strip()
            try:
                custom_minutes = int(custom_input)
                if 0 <= custom_minutes <= 120:
                    new_minutes = custom_minutes
                else:
                    print("Invalid duration. Must be between 0 and 120 minutes.")
                    return
            except ValueError:
                print("Invalid input. Please enter a number.")
                return
        elif choice == '7':
            print("Configuration cancelled.")
            return
        else:
            print("Invalid choice.")
            return
        
        if new_minutes is not None:
            self.set_lunch_break_minutes(new_minutes)
            new_hours = new_minutes // 60
            new_mins = new_minutes % 60
            
            if new_minutes == 0:
                print(f"✅ Lunch break disabled (0 minutes)")
            else:
                print(f"✅ Lunch break updated to {new_hours}h {new_mins}m ({new_minutes} minutes)")
            
            # Recalculate all existing entries with new lunch break duration
            self.recalculate_all_entries()
    
    def recalculate_all_entries(self):
        """Recalculate hours worked for all entries with current lunch break setting."""
        lunch_minutes = self.get_lunch_break_minutes()
        recalculated_count = 0
        
        for date_str, entry in self.data.items():
            if date_str == 'settings':
                continue
            
            if isinstance(entry, dict) and 'start' in entry and 'end' in entry:
                try:
                    start_datetime = datetime.datetime.strptime(f"{date_str} {entry['start']}", "%Y-%m-%d %H:%M")
                    end_datetime = datetime.datetime.strptime(f"{date_str} {entry['end']}", "%Y-%m-%d %H:%M")
                    
                    # Handle case where end time is next day
                    if end_datetime < start_datetime:
                        end_datetime += datetime.timedelta(days=1)
                    
                    total_minutes = (end_datetime - start_datetime).total_seconds() / 60
                    worked_minutes = total_minutes - lunch_minutes
                    worked_hours = worked_minutes / 60
                    
                    entry['hours_worked'] = round(worked_hours, 2)
                    entry['total_minutes'] = int(worked_minutes)
                    recalculated_count += 1
                    
                except ValueError:
                    continue
        
        if recalculated_count > 0:
            self.save_data()
            print(f"📊 Recalculated {recalculated_count} entries with new lunch break duration.")
    
    def clear_previous_entries(self):
        """Clear all previous entries but keep settings."""
        settings = self.data.get('settings', {'lunch_break_minutes': 30})
        self.data = {'settings': settings}
        self.save_data()
        print("🗑️  Previous work log entries cleared for new week.")
    
    def is_first_monday_input(self, target_date: datetime.date = None) -> bool:
        """Check if this is the first input on a Monday."""
        if target_date is None:
            target_date = datetime.date.today()
        
        # Check if today is Monday
        if target_date.weekday() != 0:  # 0 = Monday
            return False
        
        # Check if there are no entries for today yet
        date_str = target_date.strftime("%Y-%m-%d")
        return date_str not in self.data or not self.data[date_str]
    
    def get_week_start(self, date: datetime.date) -> datetime.date:
        """Get the start of the week (Monday) for a given date."""
        return date - datetime.timedelta(days=date.weekday())
    
    def get_weekly_hours(self, target_date: datetime.date = None) -> Tuple[float, List[str]]:
        """Calculate total hours worked this week and return list of dates."""
        if target_date is None:
            target_date = datetime.date.today()
        
        week_start = self.get_week_start(target_date)
        total_hours = 0
        week_dates = []
        
        for i in range(7):
            date = week_start + datetime.timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            week_dates.append(date_str)
            
            if date_str in self.data and isinstance(self.data[date_str], dict):
                entry = self.data[date_str]
                hours = entry.get('hours_worked', 0)
                total_hours += hours
        
        return total_hours, week_dates
    
    def get_current_work_time(self):
        """Get current work time info if work has started today."""
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        if today not in self.data or not isinstance(self.data[today], dict):
            return None
        
        entry = self.data[today]
        if 'start' not in entry:
            return None
        
        # If work has already ended today, don't show counter
        if 'end' in entry:
            return None
        
        try:
            start_time = datetime.datetime.strptime(f"{today} {entry['start']}", "%Y-%m-%d %H:%M")
            current_time = datetime.datetime.now()
            
            # Calculate elapsed time
            elapsed = current_time - start_time
            total_minutes = int(elapsed.total_seconds() / 60)
            
            # Calculate hours and minutes
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            # Get lunch break setting
            lunch_minutes = self.get_lunch_break_minutes()
            
            # Calculate work time (minus lunch break if over 4 hours)
            work_minutes = total_minutes - (lunch_minutes if total_minutes > 240 else 0)
            work_hours = work_minutes // 60
            work_mins_remainder = work_minutes % 60
            
            # Get weekly hours (excluding today's current session)
            weekly_hours, _ = self.get_weekly_hours()
            current_day_hours = work_minutes / 60
            
            # Calculate for daily 7-hour rule
            target_total_minutes = 420 + lunch_minutes  # 7 hours + lunch break
            minutes_until_7h = target_total_minutes - total_minutes
            
            if minutes_until_7h > 0:
                leave_time_7h = start_time + datetime.timedelta(minutes=target_total_minutes)
                time_to_leave_7h = leave_time_7h.strftime("%H:%M")
                hours_until_7h = minutes_until_7h // 60
                mins_until_7h = minutes_until_7h % 60
            else:
                time_to_leave_7h = None
                hours_until_7h = 0
                mins_until_7h = 0
            
            # Calculate for weekly 35-hour rule - only if weekly hours > 27
            remaining_weekly_hours = 35 - weekly_hours
            remaining_weekly_minutes = remaining_weekly_hours * 60
            
            # How many more minutes needed today to reach 35h for the week
            minutes_needed_for_35h = remaining_weekly_minutes - work_minutes
            
            # Only calculate 35h time if weekly hours > 27
            show_35h_target = weekly_hours > 27
            
            if show_35h_target and minutes_needed_for_35h > 0:
                # Add lunch break if we haven't reached 4 hours yet
                if total_minutes <= 240:
                    minutes_needed_for_35h += lunch_minutes
                
                total_minutes_for_35h = total_minutes + minutes_needed_for_35h
                leave_time_35h = start_time + datetime.timedelta(minutes=total_minutes_for_35h)
                time_to_leave_35h = leave_time_35h.strftime("%H:%M")
                hours_until_35h = int(minutes_needed_for_35h) // 60
                mins_until_35h = int(minutes_needed_for_35h) % 60
            else:
                time_to_leave_35h = None
                hours_until_35h = 0
                mins_until_35h = 0
            
            return {
                'start_time': entry['start'],
                'elapsed_hours': hours,
                'elapsed_minutes': minutes,
                'work_hours': work_hours,
                'work_minutes': work_mins_remainder,
                'total_work_minutes': work_minutes,
                'weekly_hours': weekly_hours,
                'current_day_hours': current_day_hours,
                'remaining_weekly_hours': remaining_weekly_hours,
                'lunch_minutes': lunch_minutes,
                # 7-hour rule
                'time_to_leave_7h': time_to_leave_7h,
                'hours_until_7h': hours_until_7h,
                'mins_until_7h': mins_until_7h,
                'daily_target_reached': minutes_until_7h <= 0,
                # 35-hour rule
                'show_35h_target': show_35h_target,
                'time_to_leave_35h': time_to_leave_35h,
                'hours_until_35h': hours_until_35h,
                'mins_until_35h': mins_until_35h,
                'weekly_target_reached': remaining_weekly_hours <= current_day_hours,
                'minutes_needed_for_35h': max(0, int(minutes_needed_for_35h))
            }
        except ValueError:
            return None
    
    def display_work_counter(self):
        """Display current work time counter."""
        work_info = self.get_current_work_time()
        
        if work_info:
            print(f"\n🕐 WORK SESSION ACTIVE")
            print(f"Started: {work_info['start_time']}")
            print(f"Elapsed: {work_info['elapsed_hours']}h {work_info['elapsed_minutes']}m")
            
            if work_info['total_work_minutes'] > 0:
                print(f"Work time: {work_info['work_hours']}h {work_info['work_minutes']}m", end="")
                lunch_minutes = work_info['lunch_minutes']
                if lunch_minutes > 0:
                    if work_info['total_work_minutes'] > 240:  # More than 4 hours
                        lunch_hours = lunch_minutes // 60
                        lunch_mins = lunch_minutes % 60
                        if lunch_hours > 0:
                            print(f" ({lunch_hours}h {lunch_mins}m lunch break deducted)")
                        else:
                            print(f" ({lunch_mins}m lunch break deducted)")
                    else:
                        lunch_hours = lunch_minutes // 60
                        lunch_mins = lunch_minutes % 60
                        if lunch_hours > 0:
                            print(f" ({lunch_hours}h {lunch_mins}m lunch break will be deducted)")
                        else:
                            print(f" ({lunch_mins}m lunch break will be deducted)")
                else:
                    print(" (no lunch break)")
            
            # Show weekly progress
            print(f"📅 Weekly hours: {work_info['weekly_hours']:.1f}/35h (remaining: {work_info['remaining_weekly_hours']:.1f}h)")
            
            # Determine which rule applies
            if work_info['weekly_target_reached']:
                print(f"🎯 WEEKLY TARGET REACHED! You've completed 35+ hours this week")
            elif work_info['daily_target_reached']:
                print(f"🎯 DAILY TARGET REACHED! You've completed 7+ hours today")
                # Only show 35h target if weekly hours > 27
                if work_info['show_35h_target'] and work_info['time_to_leave_35h']:
                    print(f"📅 For 35h week: Leave at {work_info['time_to_leave_35h']} (in {work_info['hours_until_35h']:02d}:{work_info['mins_until_35h']:02d})")
            else:
                # Show both targets
                print(f"🎯 Daily (7h): Leave at {work_info['time_to_leave_7h']} (in {work_info['hours_until_7h']:02d}:{work_info['mins_until_7h']:02d})")
                # Only show 35h target if weekly hours > 27
                if work_info['show_35h_target']:
                    if work_info['time_to_leave_35h']:
                        print(f"📅 Weekly (35h): Leave at {work_info['time_to_leave_35h']} (in {work_info['hours_until_35h']:02d}:{work_info['mins_until_35h']:02d})")
                    else:
                        print(f"📅 Weekly (35h): Target already reached this week!")
            
            print()
    
    def log_start(self, time_str: Optional[str] = None):
        """Log work start time."""
        # Check if this is the first Monday input and clear previous entries
        if self.is_first_monday_input():
            self.clear_previous_entries()
        
        if time_str:
            try:
                start_time = datetime.datetime.strptime(time_str, "%H:%M")
                start_time = start_time.replace(year=datetime.date.today().year,
                                              month=datetime.date.today().month,
                                              day=datetime.date.today().day)
            except ValueError:
                print("Invalid time format. Use HH:MM (24-hour format)")
                return False
        else:
            start_time = datetime.datetime.now()
        
        date_str = start_time.strftime("%Y-%m-%d")
        
        if date_str not in self.data:
            self.data[date_str] = {}
        
        self.data[date_str]['start'] = start_time.strftime("%H:%M")
        self.save_data()
        
        print(f"Work start logged: {start_time.strftime('%Y-%m-%d %H:%M')}")
        return True
    
    def log_end(self, time_str: Optional[str] = None):
        """Log work end time and calculate hours worked."""
        # Check if this is the first Monday input and clear previous entries
        if self.is_first_monday_input():
            self.clear_previous_entries()
        
        if time_str:
            try:
                end_time = datetime.datetime.strptime(time_str, "%H:%M")
                end_time = end_time.replace(year=datetime.date.today().year,
                                          month=datetime.date.today().month,
                                          day=datetime.date.today().day)
            except ValueError:
                print("Invalid time format. Use HH:MM (24-hour format)")
                return False
        else:
            end_time = datetime.datetime.now()
        
        date_str = end_time.strftime("%Y-%m-%d")
        
        if date_str not in self.data:
            self.data[date_str] = {}
        
        if 'start' not in self.data[date_str]:
            print(f"No start time found for {date_str}. Please log start time first.")
            return False
        
        self.data[date_str]['end'] = end_time.strftime("%H:%M")
        
        # Calculate hours worked
        start_datetime = datetime.datetime.strptime(f"{date_str} {self.data[date_str]['start']}", "%Y-%m-%d %H:%M")
        end_datetime = end_time
        
        # Handle case where end time is next day
        if end_datetime < start_datetime:
            end_datetime += datetime.timedelta(days=1)
        
        total_minutes = (end_datetime - start_datetime).total_seconds() / 60
        # Subtract lunch break
        lunch_minutes = self.get_lunch_break_minutes()
        worked_minutes = total_minutes - lunch_minutes
        worked_hours = worked_minutes / 60
        
        self.data[date_str]['hours_worked'] = round(worked_hours, 2)
        self.data[date_str]['total_minutes'] = int(worked_minutes)
        
        self.save_data()
        
        print(f"Work end logged: {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Hours worked: {worked_hours:.2f} hours ({int(worked_minutes)} minutes)")
        
        if lunch_minutes > 0:
            lunch_hours = lunch_minutes // 60
            lunch_mins = lunch_minutes % 60
            if lunch_hours > 0:
                print(f"({lunch_hours}h {lunch_mins}m deducted for lunch break)")
            else:
                print(f"({lunch_mins} minutes deducted for lunch break)")
        else:
            print("(no lunch break deducted)")
        
        # Show weekly summary
        weekly_hours, _ = self.get_weekly_hours()
        print(f"Weekly total: {weekly_hours:.2f}/35 hours")
        
        return True
    
    def view_today(self):
        """View today's work log."""
        today = datetime.date.today().strftime("%Y-%m-%d")
        if today in self.data and isinstance(self.data[today], dict):
            entry = self.data[today]
            print(f"\n--- Work Log for {today} ---")
            print(f"Start: {entry.get('start', 'Not logged')}")
            print(f"End: {entry.get('end', 'Not logged')}")
            if 'hours_worked' in entry:
                print(f"Hours worked: {entry['hours_worked']} hours")
            
            # Show weekly context
            weekly_hours, _ = self.get_weekly_hours()
            print(f"Weekly total: {weekly_hours:.2f}/35 hours")
            print()
        else:
            print(f"No work log found for today ({today})")
    
    def view_week(self):
        """View this week's work log."""
        today = datetime.date.today()
        week_start = self.get_week_start(today)
        
        print(f"\n--- Work Log for Week of {week_start.strftime('%Y-%m-%d')} ---")
        total_hours = 0
        
        for i in range(7):
            date = week_start + datetime.timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            day_name = date.strftime("%A")
            
            if date_str in self.data and isinstance(self.data[date_str], dict):
                entry = self.data[date_str]
                hours = entry.get('hours_worked', 0)
                total_hours += hours
                status = "✓" if hours > 0 else "○"
                print(f"{status} {day_name} ({date_str}): {hours} hours")
            else:
                print(f"○ {day_name} ({date_str}): No log")
        
        print(f"\nTotal hours this week: {total_hours:.2f}/35 hours")
        remaining = 35 - total_hours
        if remaining > 0:
            print(f"Remaining to reach 35h: {remaining:.2f} hours")
        else:
            print("✅ Weekly target of 35 hours reached!")
        
        # Show current lunch break setting
        lunch_minutes = self.get_lunch_break_minutes()
        if lunch_minutes > 0:
            lunch_hours = lunch_minutes // 60
            lunch_mins = lunch_minutes % 60
            if lunch_hours > 0:
                print(f"Lunch break setting: {lunch_hours}h {lunch_mins}m")
            else:
                print(f"Lunch break setting: {lunch_mins} minutes")
        else:
            print("Lunch break: Disabled")
        print()
    
    def view_all(self):
        """View all work logs."""
        work_entries = {k: v for k, v in self.data.items() if k != 'settings' and isinstance(v, dict)}
        
        if not work_entries:
            print("No work logs found.")
            return
        
        print("\n--- All Work Logs ---")
        total_hours = 0
        current_week_start = None
        week_total = 0
        
        for date in sorted(work_entries.keys()):
            entry = work_entries[date]
            hours = entry.get('hours_worked', 0)
            total_hours += hours
            
            # Check if we're in a new week
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            week_start = self.get_week_start(date_obj)
            
            if current_week_start != week_start:
                if current_week_start is not None:
                    print(f"    Week total: {week_total:.2f}/35 hours")
                current_week_start = week_start
                week_total = 0
                print(f"\n  Week of {week_start.strftime('%Y-%m-%d')}:")
            
            week_total += hours
            start = entry.get('start', 'N/A')
            end = entry.get('end', 'N/A')
            print(f"    {date}: {start} - {end} ({hours} hours)")
        
        if current_week_start is not None:
            print(f"    Week total: {week_total:.2f}/35 hours")
        
        print(f"\nTotal hours logged: {total_hours:.2f} hours")
        
        # Show current lunch break setting
        lunch_minutes = self.get_lunch_break_minutes()
        if lunch_minutes > 0:
            lunch_hours = lunch_minutes // 60
            lunch_mins = lunch_minutes % 60
            if lunch_hours > 0:
                print(f"Current lunch break setting: {lunch_hours}h {lunch_mins}m")
            else:
                print(f"Current lunch break setting: {lunch_mins} minutes")
        else:
            print("Current lunch break setting: Disabled")
        print()
    
    def edit_past_day(self):
        """Edit work times for a past day."""
        work_entries = {k: v for k, v in self.data.items() if k != 'settings' and isinstance(v, dict)}
        
        if not work_entries:
            print("No work logs found to edit.")
            return
        
        print("\n--- Edit Past Day ---")
        print("Available dates:")
        for date in sorted(work_entries.keys()):
            entry = work_entries[date]
            start = entry.get('start', 'N/A')
            end = entry.get('end', 'N/A')
            hours = entry.get('hours_worked', 0)
            print(f"  {date}: {start} - {end} ({hours} hours)")
        
        date_input = input("\nEnter date to edit (YYYY-MM-DD) or press Enter to cancel: ").strip()
        if not date_input:
            return
        
        # Validate date format
        try:
            datetime.datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return
        
        # Create entry if it doesn't exist
        if date_input not in self.data:
            self.data[date_input] = {}
            print(f"Created new entry for {date_input}")
        
        current_entry = self.data[date_input]
        current_start = current_entry.get('start', 'Not set')
        current_end = current_entry.get('end', 'Not set')
        
        print(f"\nCurrent times for {date_input}:")
        print(f"Start: {current_start}")
        print(f"End: {current_end}")
        
        # Edit start time
        new_start = input(f"Enter new start time (HH:MM) or press Enter to keep '{current_start}': ").strip()
        if new_start:
            try:
                datetime.datetime.strptime(new_start, "%H:%M")
                self.data[date_input]['start'] = new_start
                print(f"Start time updated to {new_start}")
            except ValueError:
                print("Invalid time format. Start time not changed.")
        
        # Edit end time
        new_end = input(f"Enter new end time (HH:MM) or press Enter to keep '{current_end}': ").strip()
        if new_end:
            try:
                datetime.datetime.strptime(new_end, "%H:%M")
                self.data[date_input]['end'] = new_end
                print(f"End time updated to {new_end}")
            except ValueError:
                print("Invalid time format. End time not changed.")
        
        # Recalculate hours if both start and end are set
        if 'start' in self.data[date_input] and 'end' in self.data[date_input]:
            start_str = self.data[date_input]['start']
            end_str = self.data[date_input]['end']
            
            start_datetime = datetime.datetime.strptime(f"{date_input} {start_str}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.datetime.strptime(f"{date_input} {end_str}", "%Y-%m-%d %H:%M")
            
            # Handle case where end time is next day
            if end_datetime < start_datetime:
                end_datetime += datetime.timedelta(days=1)
            
            total_minutes = (end_datetime - start_datetime).total_seconds() / 60
            # Subtract lunch break
            lunch_minutes = self.get_lunch_break_minutes()
            worked_minutes = total_minutes - lunch_minutes
            worked_hours = worked_minutes / 60
            
            self.data[date_input]['hours_worked'] = round(worked_hours, 2)
            self.data[date_input]['total_minutes'] = int(worked_minutes)
            
            print(f"Hours worked recalculated: {worked_hours:.2f} hours ({int(worked_minutes)} minutes)")
            
            if lunch_minutes > 0:
                lunch_hours = lunch_minutes // 60
                lunch_mins = lunch_minutes % 60
                if lunch_hours > 0:
                    print(f"({lunch_hours}h {lunch_mins}m deducted for lunch break)")
                else:
                    print(f"({lunch_mins} minutes deducted for lunch break)")
            else:
                print("(no lunch break deducted)")
        
        self.save_data()
        print(f"\nChanges saved for {date_input}")
    
    def delete_day(self):
        """Delete a work log entry for a specific day."""
        work_entries = {k: v for k, v in self.data.items() if k != 'settings' and isinstance(v, dict)}
        
        if not work_entries:
            print("No work logs found to delete.")
            return
        
        print("\n--- Delete Day ---")
        print("Available dates:")
        for date in sorted(work_entries.keys()):
            entry = work_entries[date]
            start = entry.get('start', 'N/A')
            end = entry.get('end', 'N/A')
            hours = entry.get('hours_worked', 0)
            print(f"  {date}: {start} - {end} ({hours} hours)")
        
        date_input = input("\nEnter date to delete (YYYY-MM-DD) or press Enter to cancel: ").strip()
        if not date_input:
            return
        
        if date_input not in self.data or date_input == 'settings':
            print(f"No entry found for {date_input}")
            return
        
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete the entry for {date_input}? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            del self.data[date_input]
            self.save_data()
            print(f"Entry for {date_input} deleted.")
        else:
            print("Deletion cancelled.")

def main():
    logger = WorkLogger()
    
    while True:
        # Display the work counter at the top of the menu
        logger.display_work_counter()
        
        print("=== Work Hours Logger ===")
        print("1. Log today's workday start")
        print("2. Log today's workday end")
        print("3. View today's log")
        print("4. View this week's log")
        print("5. View all logs")
        print("6. Edit past day")
        print("7. Delete day")
        print("8. Configure lunch break")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            time_input = input("Enter start time (HH:MM) or press Enter for current time: ").strip()
            if time_input:
                logger.log_start(time_input)
            else:
                logger.log_start()
        
        elif choice == '2':
            time_input = input("Enter end time (HH:MM) or press Enter for current time: ").strip()
            if time_input:
                logger.log_end(time_input)
            else:
                logger.log_end()
        
        elif choice == '3':
            logger.view_today()
        
        elif choice == '4':
            logger.view_week()
        
        elif choice == '5':
            logger.view_all()
        
        elif choice == '6':
            logger.edit_past_day()
        
        elif choice == '7':
            logger.delete_day()
        
        elif choice == '8':
            logger.configure_lunch_break()
        
        elif choice == '9':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
