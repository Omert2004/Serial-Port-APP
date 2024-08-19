import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import threading
import time

class SerialPortApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Port Terminal")
        
        self.serial_thread = None
        self.serial_running = False
        self.ser = None 
        
        # Create widgets
        self.create_widgets()
        
        self.port = "COM7"  # Default serial port
        self.baudrate = 19200  # Default baud rate
        self.send_periodic = False  # Flag to control periodic sending
        
    def create_widgets(self):
        # Create Frame
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)
        
        # COM port selection
        tk.Label(frame, text="ComPort").grid(row=0, column=0, padx=5, pady=5)
        ComPortNames = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "COM10", "COM11"]
        self.comport = ttk.Combobox(frame, values=ComPortNames, state="readonly")
        self.comport.current(6)  # Set default selection to COM7
        self.comport.grid(row=0, column=1, padx=5, pady=5)

        # Baudrate Selection
        tk.Label(frame, text="Baudrate").grid(row=1, column=0, padx=5, pady=5)
        BaudRateValues = [9600, 19200, 115200]
        self.baudrate_combobox = ttk.Combobox(frame, values=BaudRateValues, state="readonly")
        self.baudrate_combobox.current(1)  # Set default selection to 19200
        self.baudrate_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.baudrate_combobox.bind("<<ComboboxSelected>>", lambda event: self.update_baudrate())

        # Data to be sent
        tk.Label(frame, text="Gönderilecek Veri").grid(row=2, column=0, padx=5, pady=5)
        self.data_entry = tk.Entry(frame, state=tk.NORMAL)  # Enabled for input
        self.data_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Send period
        tk.Label(frame, text="Gönderme Periyodu").grid(row=3, column=0, padx=5, pady=5)
        self.period_entry = tk.Entry(frame, state=tk.NORMAL)  # Enabled for input
        self.period_entry.grid(row=3, column=1, padx=5, pady=5)
        tk.Label(frame, text="Sn").grid(row=3, column=2, padx=5, pady=5)
        
        # Send button
        self.send_button = tk.Button(frame, text="GÖNDER", command=self.toggle_periodic_send, bg="#D3EAF9")
        self.send_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Start and Stop buttons
        self.start_button = tk.Button(frame, text="START", command=self.start_serial, bg="#C0F6BB")
        self.start_button.grid(row=3, column=3, padx=5, pady=5)
        self.stop_button = tk.Button(frame, text="STOP", command=self.stop_serial, bg="#F6BBBC", state=tk.DISABLED)
        self.stop_button.grid(row=3, column=4, padx=5, pady=5)
        
        # Text area for received data
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=20)
        self.text_area.pack(padx=10, pady=10)
        
        # Label for record count
        self.record_count = tk.Label(self.root, text="Kayıt Sayısı: 0")
        self.record_count.pack(padx=10, pady=10)
        
        self.record_counter = 0
    
    def update_baudrate(self):
        """Update the baudrate when the ComboBox selection changes."""
        self.baudrate = int(self.baudrate_combobox.get())
        self.append_text(f"Baudrate changed to {self.baudrate}.\n")
    
    def send_data(self):
        """Send data to the serial port."""
        data = self.data_entry.get()
        if data:
            if self.serial_running and self.ser and self.ser.is_open:
                try:
                    self.ser.write(data.encode())
                    self.append_text(f"Sent: {data}\n")
                except serial.SerialException as e:
                    self.append_text(f"Serial error: {e}\n")
                except Exception as e:
                    self.append_text(f"Unexpected error: {e}\n")
            else:
                self.append_text("Serial port is not open.\n")
        else:
            self.append_text("No data to send.\n")
        
    def toggle_periodic_send(self):
        if self.send_periodic:
            self.send_periodic = False
            self.send_button.config(text="GÖNDER")
        else:
            self.send_periodic = True
            self.send_button.config(text="DURDUR")
            self.start_periodic_send()
    
    def start_periodic_send(self):
        if self.send_periodic:
            self.send_data()
            period = int(self.period_entry.get()) 
            self.root.after(period, self.start_periodic_send)

    def start_serial(self):
        self.port = self.comport.get()
        if not self.serial_running:
            try:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
                self.serial_running = True
                self.serial_thread = threading.Thread(target=self.read_serial)
                self.serial_thread.start()
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                
                # Enable input fields and send button after serial starts
                self.data_entry.config(state=tk.NORMAL)
                self.period_entry.config(state=tk.NORMAL)
                self.send_button.config(state=tk.NORMAL)
                
                self.append_text(f"Connected to {self.port} at {self.baudrate} baud.\n")
            except serial.SerialException as e:
                self.append_text(f"Failed to open serial port: {e}\n")
            except Exception as e:
                self.append_text(f"Unexpected error: {e}\n")

    def stop_serial(self):
        if self.serial_running:
            self.serial_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            # Disable input fields and send button when serial stops
            self.data_entry.config(state=tk.DISABLED)
            self.period_entry.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            self.send_periodic = False
            self.send_button.config(text="GÖNDER")

            if self.ser and self.ser.is_open:
                self.ser.close()
            self.append_text("Serial port closed.\n")

    def read_serial(self):
        try:
            while self.serial_running:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    self.append_text(f"{current_time} - Received: {data}\n")
                    self.record_counter += 1
                    self.record_count.config(text=f"Kayıt Sayısı: {self.record_counter}")
        except serial.SerialException as e:
            self.append_text(f"Serial error: {e}\n")
        except Exception as e:
            self.append_text(f"Unexpected error: {e}\n")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.append_text("Serial port closed.\n")
    
    def append_text(self, text):
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialPortApp(root)
    root.mainloop()
