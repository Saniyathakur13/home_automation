import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
from datetime import datetime, time as dt_time
import json
import os

class SmartHomeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Home Automation System")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # Initialize voice assistant before other methods that might use it
        self.voice_assistant_enabled = False
        
        # Load or initialize devices
        self.devices_file = "devices.json"
        self.schedules_file = "schedules.json"
        self.devices = self.load_devices()
        self.schedules = self.load_schedules()
        
        # Setup styles
        self.setup_styles()
        
        # Create main interface
        self.create_widgets()
        
        # Start schedule checker in background
        self.running = True
        self.schedule_thread = threading.Thread(target=self.check_schedules)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.root.configure(bg='#f0f0f0')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('TButton', font=('Arial', 10), padding=5)
        style.configure('DeviceOn.TButton', background='#4CAF50', foreground='white')
        style.configure('DeviceOff.TButton', background='#F44336', foreground='white')
        style.configure('TRadiobutton', background='#f0f0f0')
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'), padding=[10, 5])
        style.configure('TEntry', padding=5)
        style.configure('TCombobox', padding=5)
        
    def load_devices(self):
        default_devices = {
            "Living Room Light": {"state": False, "type": "light"},
            "Kitchen Light": {"state": False, "type": "light"},
            "Bedroom Light": {"state": False, "type": "light"},
            "Thermostat": {"state": False, "type": "climate", "temperature": 22},
            "Security Camera": {"state": False, "type": "security"},
            "Smart Plug": {"state": False, "type": "plug"}
        }
        
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, 'r') as f:
                    return json.load(f)
            except:
                return default_devices
        return default_devices
    
    def load_schedules(self):
        if os.path.exists(self.schedules_file):
            try:
                with open(self.schedules_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_devices(self):
        with open(self.devices_file, 'w') as f:
            json.dump(self.devices, f, indent=4)
    
    def save_schedules(self):
        with open(self.schedules_file, 'w') as f:
            json.dump(self.schedules, f, indent=4)
    
    def create_widgets(self):
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Device Control Tab
        self.device_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.device_tab, text="Device Control")
        
        # Scheduling Tab
        self.schedule_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.schedule_tab, text="Scheduling")
        
        # Settings Tab
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Build each tab
        self.build_device_tab()
        self.build_schedule_tab()
        self.build_settings_tab()
        
    def build_device_tab(self):
        # Header
        header = ttk.Label(self.device_tab, text="Smart Home Device Control", style='Header.TLabel')
        header.pack(pady=10)
        
        # Device grid frame
        grid_frame = ttk.Frame(self.device_tab)
        grid_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create device controls
        self.device_buttons = {}
        row, col = 0, 0
        
        for device, details in self.devices.items():
            frame = ttk.Frame(grid_frame, borderwidth=1, relief='solid', padding=10)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            # Device label
            label = ttk.Label(frame, text=device, font=('Arial', 10, 'bold'))
            label.pack()
            
            # Device type indicator
            type_label = ttk.Label(frame, text=f"Type: {details['type']}")
            type_label.pack()
            
            # State indicator
            state_text = "ON" if details['state'] else "OFF"
            state_label = ttk.Label(frame, text=f"State: {state_text}")
            state_label.pack()
            
            # Control button
            btn_text = "Turn Off" if details['state'] else "Turn On"
            btn_style = "DeviceOn.TButton" if details['state'] else "DeviceOff.TButton"
            btn = ttk.Button(frame, text=btn_text, style=btn_style,
                            command=lambda d=device: self.toggle_device(d))
            btn.pack(pady=5)
            
            # Additional controls for specific devices
            if details['type'] == 'climate':
                temp_frame = ttk.Frame(frame)
                temp_frame.pack(pady=5)
                
                ttk.Label(temp_frame, text="Temp:").pack(side='left')
                temp_var = tk.IntVar(value=details['temperature'])
                spin = ttk.Spinbox(temp_frame, from_=10, to=30, textvariable=temp_var, width=5)
                spin.pack(side='left', padx=5)
                ttk.Button(temp_frame, text="Set", 
                          command=lambda d=device, v=temp_var: self.set_temperature(d, v.get())).pack(side='left')
            
            self.device_buttons[device] = {
                'state_label': state_label,
                'control_button': btn,
                'state': details['state']
            }
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        # Make grid cells expandable
        for i in range(3):
            grid_frame.columnconfigure(i, weight=1)
        for i in range(row + 1):
            grid_frame.rowconfigure(i, weight=1)
    
    def build_schedule_tab(self):
        # Header
        header = ttk.Label(self.schedule_tab, text="Schedule Device Automation", style='Header.TLabel')
        header.pack(pady=10)
        
        # Schedule list frame
        list_frame = ttk.Frame(self.schedule_tab)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Schedule list
        self.schedule_tree = ttk.Treeview(list_frame, columns=('device', 'action', 'time', 'days'), show='headings')
        self.schedule_tree.heading('device', text='Device')
        self.schedule_tree.heading('action', text='Action')
        self.schedule_tree.heading('time', text='Time')
        self.schedule_tree.heading('days', text='Days')
        self.schedule_tree.pack(fill='both', expand=True, side='left')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.schedule_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.schedule_tree.configure(yscrollcommand=scrollbar.set)
        
        # Add/remove buttons
        btn_frame = ttk.Frame(self.schedule_tab)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(btn_frame, text="Add Schedule", command=self.show_add_schedule_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_schedule).pack(side='left', padx=5)
        
        # Populate schedule list
        self.update_schedule_list()
    
    def build_settings_tab(self):
        # Header
        header = ttk.Label(self.settings_tab, text="System Settings", style='Header.TLabel')
        header.pack(pady=10)
        
        # Voice assistant frame
        voice_frame = ttk.LabelFrame(self.settings_tab, text="Voice Assistant Integration", padding=10)
        voice_frame.pack(fill='x', padx=20, pady=10)
        
        self.voice_assistant_var = tk.BooleanVar(value=self.voice_assistant_enabled)
        ttk.Checkbutton(voice_frame, text="Enable Voice Assistant Integration", 
                       variable=self.voice_assistant_var, 
                       command=self.toggle_voice_assistant).pack(anchor='w')
        
        # Status info
        status_frame = ttk.LabelFrame(self.settings_tab, text="System Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(status_frame, text=f"Connected Devices: {len(self.devices)}").pack(anchor='w')
        ttk.Label(status_frame, text=f"Active Schedules: {len(self.schedules)}").pack(anchor='w')
        
        # Backup/Restore
        backup_frame = ttk.LabelFrame(self.settings_tab, text="Backup & Restore", padding=10)
        backup_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(backup_frame, text="Backup Configuration", command=self.backup_config).pack(side='left', padx=5)
        ttk.Button(backup_frame, text="Restore Configuration", command=self.restore_config).pack(side='left', padx=5)
    
    def toggle_device(self, device_name):
        self.devices[device_name]['state'] = not self.devices[device_name]['state']
        self.save_devices()
        
        # Update UI
        state = self.devices[device_name]['state']
        self.device_buttons[device_name]['state_label'].config(text=f"State: {'ON' if state else 'OFF'}")
        self.device_buttons[device_name]['control_button'].config(
            text="Turn Off" if state else "Turn On",
            style="DeviceOn.TButton" if state else "DeviceOff.TButton"
        )
        
        # Simulate device action
        action = "on" if state else "off"
        self.log_action(f"Turned {device_name} {action}")
    
    def set_temperature(self, device_name, temperature):
        self.devices[device_name]['temperature'] = temperature
        self.save_devices()
        self.log_action(f"Set {device_name} temperature to {temperature}°C")
    
    def show_add_schedule_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Schedule")
        dialog.geometry("400x400")
        dialog.resizable(False, False)
        
        # Device selection
        ttk.Label(dialog, text="Device:").pack(pady=(10, 0))
        device_var = tk.StringVar()
        device_combo = ttk.Combobox(dialog, textvariable=device_var, 
                                  values=list(self.devices.keys()))
        device_combo.pack(fill='x', padx=20, pady=5)
        device_combo.current(0)
        
        # Action selection
        ttk.Label(dialog, text="Action:").pack(pady=(10, 0))
        action_var = tk.StringVar(value="Turn On")
        ttk.Radiobutton(dialog, text="Turn On", variable=action_var, value="Turn On").pack(anchor='w', padx=20)
        ttk.Radiobutton(dialog, text="Turn Off", variable=action_var, value="Turn Off").pack(anchor='w', padx=20)
        
        # Time selection
        ttk.Label(dialog, text="Time (HH:MM):").pack(pady=(10, 0))
        time_var = tk.StringVar(value="12:00")
        time_entry = ttk.Entry(dialog, textvariable=time_var)
        time_entry.pack(fill='x', padx=20, pady=5)
        
        # Days selection
        ttk.Label(dialog, text="Days:").pack(pady=(10, 0))
        days_frame = ttk.Frame(dialog)
        days_frame.pack(fill='x', padx=20, pady=5)
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_vars = []
        for i, day in enumerate(days):
            var = tk.BooleanVar(value=True)
            day_vars.append(var)
            cb = ttk.Checkbutton(days_frame, text=day[:3], variable=var)
            cb.grid(row=0, column=i, padx=2)
        
        # Add button
        ttk.Button(dialog, text="Add Schedule", 
                  command=lambda: self.add_schedule(
                      device_var.get(),
                      action_var.get(),
                      time_var.get(),
                      [days[i] for i, var in enumerate(day_vars) if var.get()]
                  )).pack(pady=20)
    
    def add_schedule(self, device, action, time_str, days):
        try:
            # Validate time
            datetime.strptime(time_str, "%H:%M").time()
            
            # Create schedule entry
            schedule_entry = {
                'device': device,
                'action': action,
                'time': time_str,
                'days': days
            }
            
            self.schedules.append(schedule_entry)
            self.save_schedules()
            self.update_schedule_list()
            
            self.log_action(f"Added schedule: {action} {device} at {time_str} on {', '.join(days)}")
            messagebox.showinfo("Success", "Schedule added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Invalid time format. Please use HH:MM.")
    
    def remove_schedule(self):
        selected = self.schedule_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a schedule to remove.")
            return
        
        for item in selected:
            index = int(self.schedule_tree.item(item, 'values')[0]) - 1
            if 0 <= index < len(self.schedules):
                removed = self.schedules.pop(index)
                self.log_action(f"Removed schedule: {removed['action']} {removed['device']} at {removed['time']}")
        
        self.save_schedules()
        self.update_schedule_list()
    
    def update_schedule_list(self):
        self.schedule_tree.delete(*self.schedule_tree.get_children())
        for i, schedule in enumerate(self.schedules, 1):
            days = ', '.join(schedule['days'])
            self.schedule_tree.insert('', 'end', values=(i, schedule['device'], schedule['action'], schedule['time'], days))
    
    def execute_scheduled_action(self, device, action):
        if device not in self.devices:
            return
        
        if action == "Turn On":
            if not self.devices[device]['state']:
                self.toggle_device(device)
        elif action == "Turn Off":
            if self.devices[device]['state']:
                self.toggle_device(device)
    
    def check_schedules(self):
        while self.running:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_day = now.strftime("%A")
            
            for schedule in self.schedules:
                if current_time == schedule['time'] and current_day in schedule['days']:
                    self.execute_scheduled_action(schedule['device'], schedule['action'])
            
            time.sleep(60)  # Check every minute instead of every second
    
    def toggle_voice_assistant(self):
        self.voice_assistant_enabled = self.voice_assistant_var.get()
        status = "enabled" if self.voice_assistant_enabled else "disabled"
        self.log_action(f"Voice assistant {status}")
        messagebox.showinfo("Info", f"Voice assistant integration {status}.")
    
    def backup_config(self):
        try:
            with open('smart_home_backup.json', 'w') as f:
                backup_data = {
                    'devices': self.devices,
                    'schedules': self.schedules,
                    'voice_assistant': self.voice_assistant_enabled
                }
                json.dump(backup_data, f, indent=4)
            messagebox.showinfo("Success", "Configuration backed up successfully!")
            self.log_action("System configuration backed up")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {str(e)}")
    
    def restore_config(self):
        try:
            with open('smart_home_backup.json', 'r') as f:
                backup_data = json.load(f)
                
            self.devices = backup_data.get('devices', self.devices)
            self.schedules = backup_data.get('schedules', self.schedules)
            self.voice_assistant_enabled = backup_data.get('voice_assistant', False)
            self.voice_assistant_var.set(self.voice_assistant_enabled)
            
            self.save_devices()
            self.save_schedules()
            
            # Rebuild UI
            for child in self.device_tab.winfo_children():
                child.destroy()
            self.build_device_tab()
            
            self.update_schedule_list()
            
            messagebox.showinfo("Success", "Configuration restored successfully!")
            self.log_action("System configuration restored from backup")
        except Exception as e:
            messagebox.showerror("Error", f"Restore failed: {str(e)}")
    
    def log_action(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    5
    def on_close(self):
        self.running = False
        self.save_devices()
        self.save_schedules()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartHomeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()