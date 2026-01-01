#!/usr/bin/env python3
"""
PID Tuning Application - Version 0.0.0 (Beta)
A comprehensive GUI for tuning PID controllers with analysis tools.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import json
import threading
import queue
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib as mpl
import numpy as np
import csv
from collections import deque

# Custom dark dropdown class to replace stubborn combobox
class DarkDropdown(tk.Menubutton):
    def __init__(self, master, textvariable=None, values=None, width=None, state='normal', **kwargs):
        # Default styling
        kwargs.setdefault('bg', '#2a2a2a')
        kwargs.setdefault('fg', '#e0e0e0')
        kwargs.setdefault('activebackground', '#3a3a3a')
        kwargs.setdefault('activeforeground', '#e0e0e0')
        kwargs.setdefault('bd', 1)
        kwargs.setdefault('relief', 'solid')
        kwargs.setdefault('font', 'Calibri 9')
        kwargs.setdefault('direction', 'below')
        
        super().__init__(master, **kwargs)
        
        self.textvariable = textvariable
        self.values = values or []
        self.state = state
        self._width = width
        
        # Create menu
        self.menu = tk.Menu(self, tearoff=0, bg='#2a2a2a', fg='#e0e0e0',
                           activebackground='#3a3a3a', activeforeground='#e0e0e0',
                           font='Calibri 9')
        self.configure(menu=self.menu)
        
        # Set initial text
        if textvariable and textvariable.get():
            self.configure(text=textvariable.get())
        
        # Build menu items
        self._build_menu()
        
        # Bind variable changes
        if textvariable:
            textvariable.trace_add('write', self._on_var_change)
    
    def _build_menu(self):
        """Build the dropdown menu"""
        self.menu.delete(0, tk.END)
        for value in self.values:
            self.menu.add_command(label=str(value), command=lambda v=value: self._select(v))
    
    def _select(self, value):
        """Handle selection"""
        if self.state != 'disabled':
            if self.textvariable:
                self.textvariable.set(value)
            self.configure(text=str(value))
    
    def _on_var_change(self, *args):
        """Update display when variable changes"""
        if self.textvariable:
            self.configure(text=str(self.textvariable.get()))
    
    def configure(self, **kwargs):
        """Override configure to handle width"""
        if 'width' in kwargs:
            self._width = kwargs['width']
        super().configure(**kwargs)
    
    def bind(self, sequence=None, func=None, add=None):
        """Override bind to handle events"""
        if sequence == '<<ComboboxSelected>>':
            # Store the callback for later use
            self._selection_callback = func
        else:
            super().bind(sequence, func, add)

# Custom dark combobox class
class DarkCombobox(ttk.Combobox):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # Force styling after widget is created
        self.after(10, self._force_dark_style)
        self.after(100, self._force_dark_style)
        
    def _force_dark_style(self):
        """Force dark styling on internal widgets"""
        try:
            # Get all child widgets
            for child in self.winfo_children():
                if child.winfo_class() == 'Entry':
                    child.configure(bg='#2a2a2a', fg='#e0e0e0',
                                  insertbackground='#e0e0e0',
                                  selectbackground='#3a3a3a',
                                  selectforeground='#e0e0e0')
                elif child.winfo_class() == 'Frame':
                    for grandchild in child.winfo_children():
                        if grandchild.winfo_class() == 'Entry':
                            grandchild.configure(bg='#2a2a2a', fg='#e0e0e0',
                                               insertbackground='#e0e0e0',
                                               selectbackground='#3a3a3a',
                                               selectforeground='#e0e0e0')
        except:
            pass

# Configure dark theme for matplotlib
mpl.rcParams['figure.facecolor'] = '#1a1a1a'
mpl.rcParams['axes.facecolor'] = '#1a1a1a'
mpl.rcParams['axes.edgecolor'] = '#555555'
mpl.rcParams['axes.labelcolor'] = '#e0e0e0'
mpl.rcParams['xtick.color'] = '#e0e0e0'
mpl.rcParams['ytick.color'] = '#e0e0e0'
mpl.rcParams['grid.color'] = '#333333'
mpl.rcParams['text.color'] = '#e0e0e0'
mpl.rcParams['legend.facecolor'] = '#1a1a1a'
mpl.rcParams['legend.edgecolor'] = '#555555'
mpl.rcParams['legend.framealpha'] = 0.8

class StepResponseAnalyzer:
    """Analyze step response to calculate performance metrics"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.time = []
        self.pv = []
        self.sp = []
        self.output = []
        self.step_start_time = None
        self.initial_value = 0
        self.final_value = 0
        self.step_amplitude = 0
        
    def add_data(self, t, pv, sp, output):
        self.time.append(t)
        self.pv.append(pv)
        self.sp.append(sp)
        self.output.append(output)
        
    def analyze(self):
        if len(self.time) < 10:
            return None
            
        # Find step start
        for i in range(1, len(self.sp)):
            if abs(self.sp[i] - self.sp[i-1]) > 0.1:
                self.step_start_time = self.time[i]
                self.initial_value = np.mean(self.pv[max(0, i-10):i])
                self.final_value = self.sp[i]
                self.step_amplitude = self.final_value - self.initial_value
                break
        else:
            return None
            
        # Calculate metrics
        metrics = {}
        
        # Rise time (10% to 90% of final value)
        rise_10 = self.initial_value + 0.1 * self.step_amplitude
        rise_90 = self.initial_value + 0.9 * self.step_amplitude
        
        rise_start_idx = None
        rise_end_idx = None
        
        for i in range(int(self.step_start_time * 10), len(self.pv)):
            if rise_start_idx is None and self.pv[i] >= rise_10:
                rise_start_idx = i
            if rise_end_idx is None and self.pv[i] >= rise_90:
                rise_end_idx = i
                break
                
        if rise_start_idx and rise_end_idx:
            metrics['rise_time'] = (self.time[rise_end_idx] - self.time[rise_start_idx])
            
        # Overshoot
        max_pv = max(self.pv[int(self.step_start_time * 10):])
        metrics['overshoot'] = ((max_pv - self.final_value) / self.step_amplitude) * 100
        
        # Settling time (within 2% of final value)
        settling_band = 0.02 * self.step_amplitude
        for i in range(len(self.pv) - 1, int(self.step_start_time * 10), -1):
            if abs(self.pv[i] - self.final_value) > settling_band:
                metrics['settling_time'] = self.time[i] - self.step_start_time
                break
        else:
            metrics['settling_time'] = self.time[-1] - self.step_start_time
            
        # Steady-state error
        steady_state_pv = np.mean(self.pv[-20:])
        metrics['steady_state_error'] = self.final_value - steady_state_pv
        
        return metrics

class PIDTuningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PID Tuning Application - Version 0.0.0 (Beta)")
        self.root.geometry("1400x1000")
        
        # Configure dark theme
        self.setup_dark_theme()
        
        # Data storage
        self.data_queue = queue.Queue()
        self.time_window = tk.IntVar(value=60)  # seconds
        self.max_points = 864000  # Maximum: 24 hours at 10Hz (864,000 points)
        
        # Initialize deques with fixed maximum size for 24 hours
        self.time_data = deque(maxlen=self.max_points)
        self.pv_data = deque(maxlen=self.max_points)
        self.sp_data = deque(maxlen=self.max_points)
        self.output_data = deque(maxlen=self.max_points)
        self.error_data = deque(maxlen=self.max_points)
        self.p_term_data = deque(maxlen=self.max_points)
        self.i_term_data = deque(maxlen=self.max_points)
        self.d_term_data = deque(maxlen=self.max_points)
        
        # Step response analysis
        self.analyzer = StepResponseAnalyzer()
        self.step_test_active = False
        
        # Serial connection
        self.serial_port = None
        self.serial_thread = None
        self.running = False
        
        # Current values with formatted display
        self.current_pv = tk.DoubleVar(value=0.0)
        self.current_sp = tk.DoubleVar(value=25.0)
        self.current_output = tk.DoubleVar(value=0.0)
        self.current_error = tk.DoubleVar(value=0.0)
        
        # Formatted display strings
        self.pv_display = tk.StringVar(value="  0.00")
        self.sp_display = tk.StringVar(value=" 25.00")
        self.output_display = tk.StringVar(value="  0")
        self.error_display = tk.StringVar(value="  0.00")
        
        # PID component displays
        self.p_display = tk.StringVar(value="   0.00")
        self.i_display = tk.StringVar(value="   0.00")
        self.d_display = tk.StringVar(value="   0.00")
        
        # PID parameters
        self.kp_var = tk.DoubleVar(value=2.0)
        self.ki_var = tk.DoubleVar(value=0.1)
        self.kd_var = tk.DoubleVar(value=0.05)
        self.sp_var = tk.DoubleVar(value=25.0)
        
        # Control loop period
        self.loop_period_var = tk.IntVar(value=100)  # Default 100ms
        
        # Anti-windup settings
        self.anti_windup_enabled = tk.BooleanVar(value=True)
        self.output_limit_enabled = tk.BooleanVar(value=True)
        self.output_min_var = tk.DoubleVar(value=0)
        self.output_max_var = tk.DoubleVar(value=255)
        self.integral_limit_enabled = tk.BooleanVar(value=False)  # User-defined integral limits
        self.integral_min_var = tk.DoubleVar(value=-40)
        self.integral_max_var = tk.DoubleVar(value=40)
        
        # Auto Y-scale settings
        self.auto_y_scale_pv = tk.BooleanVar(value=True)  # Auto-scale PV/SP chart
        self.auto_y_scale_output = tk.BooleanVar(value=False)  # Auto-scale Output chart
        self.auto_y_scale_error = tk.BooleanVar(value=False)  # Auto-scale Error chart
        
        # Min/Max tracking variables
        self.pv_min = tk.StringVar(value="N/A")
        self.pv_max = tk.StringVar(value="N/A")
        self.error_min = tk.StringVar(value="N/A")
        self.error_max = tk.StringVar(value="N/A")
        self.output_min = tk.StringVar(value="N/A")
        self.output_max = tk.StringVar(value="N/A")
        
        self.setup_gui()
        self.update_plot_timer()
        
        # Bind Alt+F4 to close window
        self.root.bind('<Alt-F4>', lambda e: self.root.quit())
        
    def setup_dark_theme(self):
        """Configure dark theme for the application"""
        # Configure root window
        self.root.configure(bg='#0d0d0d')
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors - much darker theme
        bg_color = '#1a1a1a'
        fg_color = '#e0e0e0'
        select_color = '#2a2a2a'
        button_color = '#2a2a2a'
        hover_color = '#3a3a3a'
        
        # Configure styles with modern dark theme
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Calibri', 9))
        style.configure('TLabelframe', background=bg_color, foreground=fg_color, 
                       borderwidth=1, relief='solid')
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color, font=('Calibri', 10, 'bold'))
        style.configure('TButton', background=button_color, foreground=fg_color, 
                       font=('Calibri', 9), borderwidth=1, relief='solid', focuscolor='none')
        style.map('TButton', background=[('active', hover_color), ('pressed', '#4a4a4a')])
        style.configure('TEntry', fieldbackground='#2a2a2a', foreground=fg_color, 
                       borderwidth=1, relief='solid', insertcolor=fg_color)
        style.configure('TCombobox', fieldbackground='#2a2a2a', foreground=fg_color, 
                       background=button_color, borderwidth=1, relief='solid', 
                       arrowcolor=fg_color, selectbackground='#3a3a3a',
                       selectforeground=fg_color)
        style.configure('TCheckbutton', background=bg_color, foreground=fg_color, 
                       font=('Calibri', 9), focuscolor='none')
        style.configure('TNotebook', background=bg_color, foreground=fg_color, borderwidth=1)
        style.configure('TNotebook.Tab', background=button_color, foreground=fg_color, 
                       font=('Calibri', 9), padding=[20, 8], borderwidth=1)
        style.map('TNotebook.Tab', background=[('selected', select_color), ('active', hover_color)])
        
        # Configure darker borders
        style.map('TLabelframe', bordercolor=[('!disabled', '#2a2a2a')])
        style.map('TButton', bordercolor=[('!disabled', '#2a2a2a')])
        style.map('TEntry', bordercolor=[('!disabled', '#2a2a2a')])
        style.map('TCombobox', bordercolor=[('!disabled', '#2a2a2a')])
        style.map('TNotebook', bordercolor=[('!disabled', '#2a2a2a')])
        
        # Configure modern fonts using root window
        self.root.option_add('*Font', 'Calibri 9')
        self.root.option_add('*TCombobox*Listbox.font', 'Calibri 9')
        self.root.option_add('*TCombobox*Listbox.selectBackground', select_color)
        self.root.option_add('*TCombobox*Listbox.selectForeground', fg_color)
        
    def setup_gui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Main Control
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Control")
        self.setup_main_tab()
        
        # Tab 2: Tuning Guide
        self.guide_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.guide_tab, text="Tuning Guide")
        self.setup_guide_tab()
        
    def setup_main_tab(self):
        # Main container
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel - Controls
        self.setup_control_panel(main_frame)
        
        # Right panel - Plot
        self.setup_plot_panel(main_frame)
        
        # Bottom panel - Status bar
        self.setup_status_bar(main_frame)
        
    def setup_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="Control Panel", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        row = 0
        
        # Serial connection
        ttk.Label(control_frame, text="Serial Connection", font=('Calibri', 10, 'bold')).grid(row=row, column=0, columnspan=4, pady=(0, 5), sticky=(tk.W, tk.E))
        row += 1
        
        ttk.Label(control_frame, text="Port:").grid(row=row, column=0, sticky=tk.W)
        self.port_var = tk.StringVar()
        self.port_combo = DarkDropdown(control_frame, textvariable=self.port_var, width=50)
        self.port_combo.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0))
        self.refresh_ports()
        ttk.Button(control_frame, text="Refresh", command=self.refresh_ports).grid(row=row, column=3, padx=(5, 0))
        row += 1
        
        self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(5, 15))
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Current values display
        ttk.Label(control_frame, text="Current Values", font=('Calibri', 10, 'bold')).grid(row=row, column=0, columnspan=4, pady=(0, 5), sticky=(tk.W, tk.E))
        row += 1
        
        values_frame = ttk.Frame(control_frame)
        values_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        # Process Value
        ttk.Label(values_frame, text="Process Value:").grid(row=0, column=0, sticky=tk.W)
        self.pv_label = ttk.Label(values_frame, textvariable=self.pv_display, font=('Courier New', 12, 'bold'), foreground='blue')
        self.pv_label.grid(row=0, column=1, sticky=tk.E, padx=(5, 0))
        ttk.Label(values_frame, text="°C").grid(row=0, column=2, sticky=tk.W)
        
        # Setpoint
        ttk.Label(values_frame, text="Setpoint:").grid(row=1, column=0, sticky=tk.W)
        self.sp_label = ttk.Label(values_frame, textvariable=self.sp_display, font=('Courier New', 12, 'bold'), foreground='green')
        self.sp_label.grid(row=1, column=1, sticky=tk.E, padx=(5, 0))
        ttk.Label(values_frame, text="°C").grid(row=1, column=2, sticky=tk.W)
        
        # Output
        ttk.Label(values_frame, text="Output:").grid(row=2, column=0, sticky=tk.W)
        self.output_label = ttk.Label(values_frame, textvariable=self.output_display, font=('Courier New', 12, 'bold'), foreground='red')
        self.output_label.grid(row=2, column=1, sticky=tk.E, padx=(5, 0))
        ttk.Label(values_frame, text="/255").grid(row=2, column=2, sticky=tk.W)
        
        # Error
        ttk.Label(values_frame, text="Error:").grid(row=3, column=0, sticky=tk.W)
        self.error_label = ttk.Label(values_frame, textvariable=self.error_display, font=('Courier New', 10))
        self.error_label.grid(row=3, column=1, sticky=tk.E, padx=(5, 0))
        ttk.Label(values_frame, text="°C").grid(row=3, column=2, sticky=tk.W)
        row += 1
        
        # PID Components
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(control_frame, text="PID Components", font=('Calibri', 10, 'bold')).grid(row=row, column=0, columnspan=4, pady=(0, 5), sticky=(tk.W, tk.E))
        row += 1
        
        pid_frame = ttk.Frame(control_frame)
        pid_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        # P term
        ttk.Label(pid_frame, text="P term:").grid(row=0, column=0, sticky=tk.W)
        self.p_label = ttk.Label(pid_frame, textvariable=self.p_display, font=('Courier New', 10, 'bold'), foreground='orange')
        self.p_label.grid(row=0, column=1, sticky=tk.E, padx=(5, 0))
        
        # I term
        ttk.Label(pid_frame, text="I term:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.i_label = ttk.Label(pid_frame, textvariable=self.i_display, font=('Courier New', 10, 'bold'), foreground='purple')
        self.i_label.grid(row=0, column=3, sticky=tk.E, padx=(5, 0))
        
        # D term
        ttk.Label(pid_frame, text="D term:").grid(row=1, column=0, sticky=tk.W)
        self.d_label = ttk.Label(pid_frame, textvariable=self.d_display, font=('Courier New', 10, 'bold'), foreground='brown')
        self.d_label.grid(row=1, column=1, sticky=tk.E, padx=(5, 0))
        
        # Loop period
        self.loop_period_display = tk.StringVar(value="100 ms")
        ttk.Label(pid_frame, text="Loop Period:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Label(pid_frame, textvariable=self.loop_period_display, font=('Courier New', 10, 'bold'), foreground='cyan').grid(row=1, column=3, sticky=tk.E, padx=(5, 0))
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # PID Configuration
        ttk.Label(control_frame, text="PID Configuration", font=('Calibri', 10, 'bold')).grid(row=row, column=0, columnspan=4, pady=(0, 5), sticky=(tk.W, tk.E))
        row += 1
        
        params_frame = ttk.Frame(control_frame)
        params_frame.grid(row=row, column=0, columnspan=4)
        
        # Kp
        ttk.Label(params_frame, text="Kp:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(params_frame, textvariable=self.kp_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
        
        # Ki
        ttk.Label(params_frame, text="Ki:").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(params_frame, textvariable=self.ki_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=(5, 10))
        
        # Kd
        ttk.Label(params_frame, text="Kd:").grid(row=0, column=4, sticky=tk.W)
        ttk.Entry(params_frame, textvariable=self.kd_var, width=10).grid(row=0, column=5, sticky=tk.W, padx=(5, 10))
        
        # Setpoint
        ttk.Label(params_frame, text="Setpoint:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(params_frame, textvariable=self.sp_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(5, 10), pady=(5, 0))
        
        # Control Loop Period
        ttk.Label(params_frame, text="Loop Period:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        period_combo = DarkDropdown(params_frame, textvariable=self.loop_period_var,
                                   values=[1, 2, 5, 10, 20, 50, 100, 200, 500, 1000],
                                   width=80, state='readonly',
                                   text=str(self.loop_period_var.get()))
        period_combo.grid(row=1, column=3, sticky=tk.W, padx=(5, 10), pady=(5, 0))
        ttk.Label(params_frame, text="ms", font=('Calibri', 8)).grid(row=1, column=4, sticky=tk.W, pady=(5, 0))
        row += 1
        
        # Anti-windup settings (now part of PID Configuration)
        anti_frame = ttk.Frame(control_frame)
        anti_frame.grid(row=row, column=0, columnspan=4, pady=(10, 0))
        
        # First row - Enable checkboxes
        ttk.Checkbutton(anti_frame, text="Enable Anti-Windup", variable=self.anti_windup_enabled).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        ttk.Checkbutton(anti_frame, text="Output Limits", variable=self.output_limit_enabled).grid(row=0, column=2, columnspan=2, sticky=tk.W)
        
        # Second row - Output limits
        ttk.Label(anti_frame, text="Output Min:").grid(row=1, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(anti_frame, textvariable=self.output_min_var, width=8).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(anti_frame, text="Output Max:").grid(row=1, column=2, sticky=tk.W, padx=(10, 5))
        ttk.Entry(anti_frame, textvariable=self.output_max_var, width=8).grid(row=1, column=3, sticky=tk.W)
        
        # Third row - Integral limits
        ttk.Checkbutton(anti_frame, text="Custom Integral Limits", variable=self.integral_limit_enabled).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(anti_frame, text="Integral Min:").grid(row=3, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Entry(anti_frame, textvariable=self.integral_min_var, width=8).grid(row=3, column=1, sticky=tk.W)
        
        ttk.Label(anti_frame, text="Integral Max:").grid(row=3, column=2, sticky=tk.W, padx=(10, 5))
        ttk.Entry(anti_frame, textvariable=self.integral_max_var, width=8).grid(row=3, column=3, sticky=tk.W)
        
        # Explanation label
        ttk.Label(anti_frame, text="(If disabled, integral limits = 50% of output limits)", 
                 font=('Calibri', 8), foreground='gray').grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Buttons at the bottom of configuration section
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=row+1, column=0, columnspan=4, pady=(10, 5))
        
        ttk.Button(button_frame, text="Apply Config", command=self.apply_pid).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Reset", command=self.reset_pid).pack(side=tk.LEFT)
        row += 2
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Control buttons
        ttk.Label(control_frame, text="Control", font=('Calibri', 10, 'bold')).grid(row=row, column=0, columnspan=4, pady=(0, 5), sticky=(tk.W, tk.E))
        row += 1
        
        # Create a centered frame for control buttons
        control_btn_frame = ttk.Frame(control_frame)
        control_btn_frame.grid(row=row, column=0, columnspan=4, pady=5, sticky=(tk.W, tk.E))
        
        # Center the buttons within the frame
        center_frame = ttk.Frame(control_btn_frame)
        center_frame.pack(expand=True)
        
        self.start_btn = ttk.Button(center_frame, text="▶ Start", command=self.start_control, state='disabled')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(center_frame, text="■ Stop", command=self.stop_control, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Plot settings
        ttk.Label(control_frame, text="Plot Settings", font=('Calibri', 10, 'bold')).grid(row=row, column=0, columnspan=4, pady=(0, 5), sticky=(tk.W, tk.E))
        row += 1
        
        ttk.Label(control_frame, text="Time Window:").grid(row=row, column=0, sticky=tk.W)
        time_combo = DarkDropdown(control_frame, textvariable=self.time_window, 
                                  values=[30, 60, 120, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400], 
                                  width=100, state='readonly',
                                  text=str(self.time_window.get()))
        time_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(20, 0))
        ttk.Label(control_frame, text="seconds").grid(row=row, column=2, sticky=tk.W, padx=(5, 0))
        time_combo.bind('<<ComboboxSelected>>', self.update_time_window)
        row += 1
        
        # Time window description
        time_desc = {
            30: "30 seconds",
            60: "1 minute",
            120: "2 minutes",
            300: "5 minutes",
            900: "15 minutes",
            1800: "30 minutes",
            3600: "1 hour",
            7200: "2 hours",
            14400: "4 hours",
            28800: "8 hours",
            86400: "24 hours"
        }
        current_desc = time_desc.get(self.time_window.get(), "Custom")
        self.time_window_label = ttk.Label(control_frame, text=f"Showing: {current_desc}", 
                                          font=('Calibri', 8), foreground='gray')
        self.time_window_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(2, 5))
        
        # Auto Y-scale options
        ttk.Checkbutton(control_frame, text="Auto Y-Scale (PV/SP)", variable=self.auto_y_scale_pv,
                       command=self.update_plot).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        row += 1
        
        ttk.Checkbutton(control_frame, text="Auto Y-Scale (Output)", variable=self.auto_y_scale_output,
                       command=self.update_plot).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        
        ttk.Checkbutton(control_frame, text="Auto Y-Scale (Error)", variable=self.auto_y_scale_error,
                       command=self.update_plot).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Min/Max tracking
        ttk.Label(control_frame, text="Min/Max Tracking", font=('Calibri', 10, 'bold')).grid(row=row, column=0, columnspan=4, pady=(0, 5), sticky=(tk.W, tk.E))
        row += 1
        
        minmax_frame = ttk.Frame(control_frame)
        minmax_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        # PV Min/Max
        ttk.Label(minmax_frame, text="PV Min:", font=('Calibri', 9, 'bold')).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(minmax_frame, textvariable=self.pv_min, font=('Courier New', 9)).grid(row=0, column=1, sticky=tk.W, padx=(5, 20))
        ttk.Label(minmax_frame, text="PV Max:", font=('Calibri', 9, 'bold')).grid(row=0, column=2, sticky=tk.W)
        ttk.Label(minmax_frame, textvariable=self.pv_max, font=('Courier New', 9)).grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Error Min/Max
        ttk.Label(minmax_frame, text="Error Min:", font=('Calibri', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(minmax_frame, textvariable=self.error_min, font=('Courier New', 9)).grid(row=1, column=1, sticky=tk.W, padx=(5, 20), pady=(5, 0))
        ttk.Label(minmax_frame, text="Error Max:", font=('Calibri', 9, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        ttk.Label(minmax_frame, textvariable=self.error_max, font=('Courier New', 9)).grid(row=1, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        # Output Min/Max
        ttk.Label(minmax_frame, text="Output Min:", font=('Calibri', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(minmax_frame, textvariable=self.output_min, font=('Courier New', 9)).grid(row=2, column=1, sticky=tk.W, padx=(5, 20), pady=(5, 0))
        ttk.Label(minmax_frame, text="Output Max:", font=('Calibri', 9, 'bold')).grid(row=2, column=2, sticky=tk.W, pady=(5, 0))
        ttk.Label(minmax_frame, textvariable=self.output_max, font=('Courier New', 9)).grid(row=2, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        # Clear button
        clear_btn = ttk.Button(minmax_frame, text="Clear Min/Max", command=self.clear_minmax)
        clear_btn.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Data management
        ttk.Label(control_frame, text="Data Management", font=('Calibri', 10, 'bold')).grid(row=row, column=0, columnspan=4, pady=(0, 5), sticky=(tk.W, tk.E))
        row += 1
        
        data_frame = ttk.Frame(control_frame)
        data_frame.grid(row=row, column=0, columnspan=4)
        
        ttk.Button(data_frame, text="💾 Save Data", command=self.save_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(data_frame, text="🗑 Clear Plot", command=self.clear_plot).pack(side=tk.LEFT)
        
    def setup_plot_panel(self, parent):
        plot_frame = ttk.LabelFrame(parent, text="Real-time Plot", padding="5")
        plot_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create matplotlib figure with very dark background and tight layout
        self.fig = Figure(figsize=(10, 8), dpi=80, facecolor='#0d0d0d')
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.05, 
                                hspace=0.25, wspace=0.05)
        self.ax1 = self.fig.add_subplot(311)
        self.ax2 = self.fig.add_subplot(312)
        self.ax3 = self.fig.add_subplot(313)
        
        # Configure axes with very dark theme
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='#e0e0e0')
            ax.spines['bottom'].set_color('#2a2a2a')
            ax.spines['top'].set_color('#2a2a2a')
            ax.spines['left'].set_color('#2a2a2a')
            ax.spines['right'].set_color('#2a2a2a')
            ax.spines['bottom'].set_linewidth(0.5)
            ax.spines['top'].set_linewidth(0.5)
            ax.spines['left'].set_linewidth(0.5)
            ax.spines['right'].set_linewidth(0.5)
            ax.grid(True, alpha=0.2, color='#333333')
        
        self.ax1.set_ylabel('Temperature (°C)', color='#e0e0e0')
        self.ax1.set_title('Process Value & Setpoint', color='#e0e0e0')
        self.ax1.set_ylim(0, 100)
        
        self.ax2.set_ylabel('Output', color='#e0e0e0')
        self.ax2.set_title('Control Output', color='#e0e0e0')
        self.ax2.set_ylim(-10, 265)
        
        self.ax3.set_ylabel('Error (°C)', color='#e0e0e0')
        self.ax3.set_xlabel('Time (s)', color='#e0e0e0')
        self.ax3.set_title('Error Signal', color='#e0e0e0')
        self.ax3.set_ylim(-20, 20)
        
        # Create plot lines with vibrant colors for dark theme
        self.pv_line, = self.ax1.plot([], [], '#00b4d8', label='Process Value', linewidth=2.5)
        self.sp_line, = self.ax1.plot([], [], '#52b788', label='Setpoint', linewidth=2.5, linestyle='--')
        self.output_line, = self.ax2.plot([], [], '#f72585', label='Output', linewidth=2.5)
        self.error_line, = self.ax3.plot([], [], '#ffbe0b', label='Error', linewidth=2)
        
        self.ax1.legend(loc='upper right', facecolor='#1a1a1a', edgecolor='#2a2a2a', 
                       labelcolor='#e0e0e0', framealpha=0.9)
        self.ax2.legend(loc='upper right', facecolor='#1a1a1a', edgecolor='#2a2a2a', 
                       labelcolor='#e0e0e0', framealpha=0.9)
        self.ax3.legend(loc='upper right', facecolor='#1a1a1a', edgecolor='#2a2a2a', 
                       labelcolor='#e0e0e0', framealpha=0.9)
        
        # Embed in tkinter
        canvas_frame = ttk.Frame(plot_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar with dark theme styling
        # Create a custom toolbar frame to avoid matplotlib icon issues
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(fill=tk.X, pady=(2, 0))
        
        # Configure toolbar frame background
        toolbar_frame.configure(style='Dark.TFrame')
        
        # Create custom toolbar buttons with text labels
        button_frame = ttk.Frame(toolbar_frame, style='Dark.TFrame')
        button_frame.pack(side=tk.LEFT, padx=5)
        
        # Home button
        home_btn = ttk.Button(button_frame, text="⌂ Home", command=lambda: self.canvas.toolbar.home())
        home_btn.pack(side=tk.LEFT, padx=2)
        
        # Back button
        back_btn = ttk.Button(button_frame, text="← Back", command=lambda: self.canvas.toolbar.back())
        back_btn.pack(side=tk.LEFT, padx=2)
        
        # Forward button
        forward_btn = ttk.Button(button_frame, text="→ Forward", command=lambda: self.canvas.toolbar.forward())
        forward_btn.pack(side=tk.LEFT, padx=2)
        
        # Pan button
        pan_btn = ttk.Button(button_frame, text="⇄ Pan", command=lambda: self.canvas.toolbar.pan())
        pan_btn.pack(side=tk.LEFT, padx=2)
        
        # Zoom button
        zoom_btn = ttk.Button(button_frame, text="⇕ Zoom", command=lambda: self.canvas.toolbar.zoom())
        zoom_btn.pack(side=tk.LEFT, padx=2)
        
        # Save button
        save_btn = ttk.Button(button_frame, text="💾 Save", command=lambda: self.canvas.toolbar.save_figure())
        save_btn.pack(side=tk.LEFT, padx=2)
        
        # Configure the matplotlib toolbar but hide it
        self.canvas.toolbar = NavigationToolbar2Tk(self.canvas, canvas_frame)
        self.canvas.toolbar.pack_forget()  # Hide the default toolbar
        
    def setup_guide_tab(self):
        guide_frame = ttk.Frame(self.guide_tab, padding="20")
        guide_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable text widget with dark theme
        text_frame = ttk.Frame(guide_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        guide_text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                           font=('Calibri', 11), bg='#1a1a1a', fg='#e0e0e0',
                           insertbackground='#e0e0e0', selectbackground='#3a3a3a',
                           selectforeground='#e0e0e0')
        guide_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=guide_text.yview)
        
        # Add tuning guide content
        guide_content = """
PID TUNING GUIDE
================

1. UNDERSTANDING PID TERMS
--------------------------

Proportional (P)
- Responds to current error
- Higher Kp = faster response but can cause oscillation
- Too low = sluggish response

Integral (I)
- Eliminates steady-state error
- Accumulates error over time
- Too high = oscillation and overshoot

Derivative (D)
- Predicts future error
- Reduces overshoot
- Can amplify noise

2. TUNING PROCEDURE
-------------------

Step 1: Start with P-only
- Set Ki = 0, Kd = 0
- Start with Kp = 1.0
- Increase Kp until you get slight overshoot for fast reacting systems, slight undershoot for slower systems
- Good response: fast, minimal overshoot

Step 2: Add Integral
- Keep Kp from step 1
- Start with Ki = 0.01
- Increase until steady-state error is eliminated
- Watch for slow oscillation buildup
- Note the maximum required I term value to sustain the setpoint. The integral limits can be set to custom values, ensure the value you set is above the maximum I term value seen in steady state

Step 3: Add Derivative (Optional)
- Many systems work fine with PI only
- Start with Kd = 0.01
- Increase to reduce overshoot
- Keep low to avoid noise amplification
- Check D term values while testing, very low values may indicate that D gain is not necessary

Tip: note the 

3. COMMON PROBLEMS
------------------

Problem: Oscillation
Solution: Reduce Kp or Ki

Problem: Slow response
Solution: Increase Kp

Problem: Steady-state error
Solution: Increase Ki

Problem: Excessive overshoot
Solution: Reduce Kp or increase Kd

Problem: Noisy output
Solution: Reduce Kd or filter sensor

4. QUICK TUNING PRESETS
-----------------------

Temperature Control:
- Kp: 2-5
- Ki: 0.01-0.1
- Kd: 0-0.1

Motor Speed:
- Kp: 0.5-2
- Ki: 0.1-1
- Kd: 0-0.05

Position Control:
- Kp: 1-10
- Ki: 0-0.1
- Kd: 0.1-1

5. STEP RESPONSE ANALYSIS
--------------------------

Run a step test and analyze:
- Rise time: How fast it responds
- Settling time: How long to stabilize
- Overshoot: How much it exceeds setpoint
- Steady-state error: Final error value

Good values depend on your system:
- Fast systems: Rise time < 1s
- Slow systems: Rise time depends on process
- Overshoot: < 10% is usually good
- Settling time: 3-5x rise time

6. TIPS FOR BEST RESULTS
------------------------

1. Make step changes in setpoint
2. Wait for system to settle between changes
3. Test at different operating points
4. Consider process changes (load, environment)
5. Save good tunings for reference
6. Document your tuning process

7. ADVANCED TECHNIQUES
-----------------------

Feedforward:
- Add known disturbances compensation
- Reduces error before it occurs

Cascaded Control:
- Use multiple PID loops
- Fast inner loop, slow outer loop

Gain Scheduling:
- Different PID values for different conditions
- Useful for nonlinear systems

Remember: Tuning is both science and art.
Start with these guidelines, then fine-tune
for your specific application.
"""
        
        guide_text.insert('1.0', guide_content)
        guide_text.config(state='disabled')
        
    def setup_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        self.connection_status = ttk.Label(status_frame, text="● Disconnected", foreground="red")
        self.connection_status.pack(side=tk.RIGHT, padx=(0, 10))
        
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.values = ports
        self.port_combo._build_menu()
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
            self.port_combo.configure(text=ports[0])
            
    def toggle_connection(self):
        if self.serial_port is None:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a serial port")
            return
            
        try:
            self.serial_port = serial.Serial(port, 115200, timeout=1)
            self.serial_thread = threading.Thread(target=self.serial_read_thread, daemon=True)
            self.serial_thread.start()
            
            self.connect_btn.config(text="Disconnect")
            self.connection_status.config(text="● Connected", foreground="green")
            self.status_var.set(f"Connected to {port}")
            
            # Enable control buttons
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='normal')
            
            # Request initial status
            self.send_command("get_status")
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            
    def disconnect_serial(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
            
        self.connect_btn.config(text="Connect")
        self.connection_status.config(text="● Disconnected", foreground="red")
        self.status_var.set("Disconnected")
        
        # Disable control buttons
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        
    def serial_read_thread(self):
        buffer = ""
        while self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8')
                    buffer += data
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            try:
                                msg = json.loads(line)
                                self.data_queue.put(msg)
                            except json.JSONDecodeError:
                                pass
                                
            except Exception as e:
                print(f"Serial error: {e}")
                break
                
    def process_data(self):
        try:
            while True:
                msg = self.data_queue.get_nowait()
                
                if msg['type'] == 'data':
                    # Update current values
                    pv = msg['pv']
                    sp = msg['sp']
                    output = msg['output']
                    error = msg['error']
                    
                    # Get PID components if available
                    P = msg.get('P', 0.0)
                    I = msg.get('I', 0.0)
                    D = msg.get('D', 0.0)
                    
                    self.current_pv.set(pv)
                    self.current_sp.set(sp)
                    self.current_output.set(output)
                    self.current_error.set(error)
                    
                    # Update formatted displays with fixed width
                    self.pv_display.set(f"{pv:6.2f}")
                    self.sp_display.set(f"{sp:6.2f}")
                    self.output_display.set(f"{output:4.0f}")
                    self.error_display.set(f"{error:6.2f}")
                    
                    # Update PID component displays
                    self.p_display.set(f"{P:7.2f}")
                    self.i_display.set(f"{I:7.2f}")
                    self.d_display.set(f"{D:7.2f}")
                    
                    # Add to plot data
                    t = msg['time'] / 1000.0  # Convert to seconds
                    self.time_data.append(t)
                    self.pv_data.append(msg['pv'])
                    self.sp_data.append(msg['sp'])
                    self.output_data.append(msg['output'])
                    self.error_data.append(msg['error'])
                    self.p_term_data.append(P)
                    self.i_term_data.append(I)
                    self.d_term_data.append(D)
                    
                    # Add to analyzer if step test is active
                    if self.step_test_active:
                        self.analyzer.add_data(t, msg['pv'], msg['sp'], msg['output'])
                    
                    # Update min/max values
                    self.update_minmax(pv, sp, output, error)
                    
                elif msg['type'] == 'status':
                    # Update PID parameters display
                    self.kp_var.set(msg['kp'])
                    self.ki_var.set(msg['ki'])
                    self.kd_var.set(msg['kd'])
                    self.sp_var.set(msg['sp'])
                    self.running = msg['running']
                    
                    # Update loop period display
                    if 'loop_period' in msg:
                        self.loop_period_var.set(msg['loop_period'])
                        self.loop_period_display.set(f"{msg['loop_period']} ms")
                    
                    # Update anti-windup settings
                    if 'anti_windup' in msg:
                        self.anti_windup_enabled.set(msg['anti_windup'])
                    if 'output_limit' in msg:
                        self.output_limit_enabled.set(msg['output_limit'])
                    if 'output_min' in msg:
                        self.output_min_var.set(msg['output_min'])
                    if 'output_max' in msg:
                        self.output_max_var.set(msg['output_max'])
                    if 'integral_limit' in msg:
                        self.integral_limit_enabled.set(msg['integral_limit'])
                    if 'integral_min' in msg:
                        self.integral_min_var.set(msg['integral_min'])
                    if 'integral_max' in msg:
                        self.integral_max_var.set(msg['integral_max'])
                    
                    # Update button states
                    if self.running:
                        self.start_btn.config(state='disabled')
                        self.stop_btn.config(state='normal')
                    else:
                        self.start_btn.config(state='normal')
                        self.stop_btn.config(state='disabled')
                        
                elif msg['type'] == 'step_test_started':
                    self.step_test_active = True
                    self.analyzer.reset()
                    self.status_var.set("Step test running...")
                    
                elif msg['type'] == 'step_test_complete':
                    self.step_test_active = False
                    self.status_var.set("Step test complete")
                    
        except queue.Empty:
            pass
            
    def update_plot(self):
        if len(self.time_data) > 0:
            # Update x-axis limits first
            x_min = max(0, self.time_data[-1] - self.time_window.get())
            x_max = self.time_data[-1]
            
            # Find indices for visible data
            visible_start = 0
            for i, t in enumerate(self.time_data):
                if t >= x_min:
                    visible_start = i
                    break
            
            # Get visible data slices
            visible_time = list(self.time_data)[visible_start:]
            visible_pv = list(self.pv_data)[visible_start:]
            visible_sp = list(self.sp_data)[visible_start:]
            visible_output = list(self.output_data)[visible_start:]
            visible_error = list(self.error_data)[visible_start:]
            
            # Update data lines with all data (for scrolling)
            self.pv_line.set_data(self.time_data, self.pv_data)
            self.sp_line.set_data(self.time_data, self.sp_data)
            self.output_line.set_data(self.time_data, self.output_data)
            self.error_line.set_data(self.time_data, self.error_data)
            
            # Update x-axis limits
            self.ax1.set_xlim(x_min, x_max)
            self.ax2.set_xlim(x_min, x_max)
            self.ax3.set_xlim(x_min, x_max)
            
            # Auto Y-scale based on visible data only
            if self.auto_y_scale_pv.get() and len(visible_pv) > 0:
                y_min = min(min(visible_pv), min(visible_sp)) - 5
                y_max = max(max(visible_pv), max(visible_sp)) + 5
                self.ax1.set_ylim(y_min, y_max)
            
            if self.auto_y_scale_output.get() and len(visible_output) > 0:
                y_min = min(visible_output) - 10
                y_max = max(visible_output) + 10
                self.ax2.set_ylim(y_min, y_max)
            
            if self.auto_y_scale_error.get() and len(visible_error) > 0:
                y_min = min(visible_error) - 2
                y_max = max(visible_error) + 2
                self.ax3.set_ylim(y_min, y_max)
            
            self.canvas.draw()
                
    def update_plot_timer(self):
        self.process_data()
        self.update_plot()
        self.root.after(100, self.update_plot_timer)  # Update every 100ms
        
    def send_command(self, cmd, **kwargs):
        if self.serial_port:
            msg = {"cmd": cmd}
            msg.update(kwargs)
            try:
                self.serial_port.write((json.dumps(msg) + '\n').encode('utf-8'))
            except Exception as e:
                print(f"Send error: {e}")
                
    def apply_pid(self):
        self.send_command("set_params", 
                        kp=self.kp_var.get(),
                        ki=self.ki_var.get(),
                        kd=self.kd_var.get(),
                        anti_windup=self.anti_windup_enabled.get(),
                        output_limit=self.output_limit_enabled.get(),
                        output_min=self.output_min_var.get(),
                        output_max=self.output_max_var.get(),
                        integral_limit=self.integral_limit_enabled.get(),
                        integral_min=self.integral_min_var.get(),
                        integral_max=self.integral_max_var.get(),
                        loop_period=self.loop_period_var.get())
        self.send_command("set_sp", value=self.sp_var.get())
        
    def reset_pid(self):
        self.kp_var.set(2.0)
        self.ki_var.set(0.1)
        self.kd_var.set(0.05)
        self.apply_pid()
        
    def start_control(self):
        self.send_command("start")
        
    def stop_control(self):
        self.send_command("stop")
        
    def step_test(self):
        self.send_command("step_test", amplitude=10.0)
        
    def save_data(self):
        if len(self.time_data) == 0:
            messagebox.showwarning("No Data", "No data to save")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"pid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Time (s)', 'Process Value', 'Setpoint', 'Output', 'Error', 
                                   'P Term', 'I Term', 'D Term'])
                    
                    t0 = self.time_data[0] if self.time_data else 0
                    for i in range(len(self.time_data)):
                        writer.writerow([
                            self.time_data[i] - t0,
                            self.pv_data[i],
                            self.sp_data[i],
                            self.output_data[i],
                            self.error_data[i],
                            self.p_term_data[i],
                            self.i_term_data[i],
                            self.d_term_data[i]
                        ])
                        
                messagebox.showinfo("Success", f"Data saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
                
    def clear_plot(self):
        self.time_data.clear()
        self.pv_data.clear()
        self.sp_data.clear()
        self.output_data.clear()
        self.error_data.clear()
        self.p_term_data.clear()
        self.i_term_data.clear()
        self.d_term_data.clear()
        self.update_plot()
        
    def update_time_window(self, event=None):
        # Time window description
        time_desc = {
            30: "30 seconds",
            60: "1 minute",
            120: "2 minutes",
            300: "5 minutes",
            900: "15 minutes",
            1800: "30 minutes",
            3600: "1 hour",
            7200: "2 hours",
            14400: "4 hours",
            28800: "8 hours",
            86400: "24 hours"
        }
        
        # Update the description label
        current_desc = time_desc.get(self.time_window.get(), "Custom")
        self.time_window_label.config(text=f"Showing: {current_desc}")
        
        self.update_plot()
    
    def update_minmax(self, pv, sp, output, error):
        """Update min/max tracking values"""
        # PV min/max
        current_pv_min = self.pv_min.get()
        if current_pv_min == "N/A":
            self.pv_min.set(f"{pv:.2f}")
        else:
            self.pv_min.set(f"{min(pv, float(current_pv_min)):.2f}")
            
        current_pv_max = self.pv_max.get()
        if current_pv_max == "N/A":
            self.pv_max.set(f"{pv:.2f}")
        else:
            self.pv_max.set(f"{max(pv, float(current_pv_max)):.2f}")
        
        # Error min/max
        current_error_min = self.error_min.get()
        if current_error_min == "N/A":
            self.error_min.set(f"{error:.2f}")
        else:
            self.error_min.set(f"{min(error, float(current_error_min)):.2f}")
            
        current_error_max = self.error_max.get()
        if current_error_max == "N/A":
            self.error_max.set(f"{error:.2f}")
        else:
            self.error_max.set(f"{max(error, float(current_error_max)):.2f}")
        
        # Output min/max
        current_output_min = self.output_min.get()
        if current_output_min == "N/A":
            self.output_min.set(f"{output:.0f}")
        else:
            self.output_min.set(f"{min(output, float(current_output_min)):.0f}")
            
        current_output_max = self.output_max.get()
        if current_output_max == "N/A":
            self.output_max.set(f"{output:.0f}")
        else:
            self.output_max.set(f"{max(output, float(current_output_max)):.0f}")
    
    def clear_minmax(self):
        """Clear all min/max tracking values"""
        self.pv_min.set("N/A")
        self.pv_max.set("N/A")
        self.error_min.set("N/A")
        self.error_max.set("N/A")
        self.output_min.set("N/A")
        self.output_max.set("N/A")

def main():
    root = tk.Tk()
    app = PIDTuningApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
