# PID Tuning Application v1.0.0

A professional Python GUI for tuning PID controllers with real-time visualization, step response analysis, and safety monitoring capabilities.

## Features

### Real-time Control
- **Live Plotting**: Visualization of PV, SP, Output, and PID components (P, I, D)
- **Interactive Control**: Adjust PID parameters and setpoint in real-time
- **Start/Stop Control**: Manual control with safety interlocks
- **Debug Messages**: Real-time feedback from Arduino

### Analysis Tools
- **Step Response Testing**: Automatic step tests with performance metrics
- **Min/Max Tracking**: Track process variable extremes
- **Data Export**: Export data to CSV for further analysis
- **Configurable Time Windows**: View data from 30 seconds to 24 hours

### Safety Features
- **Error State Monitoring**: Visual indication of safety errors
- **Debug Mode**: View command acknowledgments and status changes
- **Safe Startup**: Control does not start automatically

### User Interface
- **Dark Theme**: Easy on the eyes for extended use
- **Intuitive Layout**: All controls clearly organized
- **Keyboard Shortcuts**: Quick access to common functions
  - Ctrl+S: Start control
  - Ctrl+X: Stop control
  - Ctrl+D: Clear debug messages
  - Ctrl+Q: Quit application

## Requirements

- Python 3.7 or higher
- Arduino or compatible microcontroller
- Python packages (see requirements.txt):
  - matplotlib
  - pyserial
  - numpy

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Upload Arduino Sketch**:
   - Choose one of the companion sketches:
     - `pid_tuning_companion_simple/` - Minimal example
     - `pid_tuning_companion/` - Full-featured example
   - Configure sensor and output pins if needed
   - Upload to your Arduino

3. **Connect Hardware**:
   - Sensor to analog pin A0 (default)
   - Control output to PWM pin 3 (default)
   - Connect Arduino to computer via USB

## Usage

1. **Start the Application**:
   ```bash
   python pid_tuning_app.py
   ```

2. **Connect to Arduino**:
   - Select the correct COM port from the dropdown
   - Click "Connect"
   - Status will show "Connected" and debug messages will appear

3. **Tune Your PID Controller**:
   - Adjust PID parameters (Kp, Ki, Kd)
   - Click "Apply Config" to send values to Arduino
   - Click "Start" to begin control
   - Monitor performance in real-time plots
   - Use "Step Test" to analyze system response

4. **Monitor Safety**:
   - Watch debug messages for command confirmations
   - Check for error states in status bar
   - Use "Stop" to immediately halt control

5. **Save Your Data**:
   - Click "Save Data" to export CSV file
   - Data includes timestamps and all process variables

## Arduino Configuration

### Minimal Companion Sketch
```cpp
#define SENSOR_PIN A0              // Analog input pin
#define OUTPUT_PIN 3               // PWM output pin
#define SAMPLE_TIME 100            // PID update time (ms)

// Sensor calibration
#define SENSOR_MIN 0.0             // Minimum raw value
#define SENSOR_MAX 1023.0          // Maximum raw value
#define VALUE_MIN 0.0              // Minimum measured value
#define VALUE_MAX 100.0            // Maximum measured value
```

### Safety Features Configuration
```cpp
// In setup() after pid.begin():
pid.setStaleDataDetection(0.1, 5000);  // Min rate, max time
pid.enableStaleDataDetection();
pid.setSafeValueLimits(-10.0, 110.0);   // Safe range
pid.enableSafeValueLimits();
```

## Communication Protocol

The application uses JSON commands over serial at 115200 baud:

### Commands to Arduino
```json
{"cmd": "set_params", "kp": 2.0, "ki": 0.1, "kd": 0.05}
{"cmd": "set_sp", "value": 25.0}
{"cmd": "start"}
{"cmd": "stop"}
{"cmd": "step_test", "amplitude": 10.0}
{"cmd": "get_status"}
```

### Messages from Arduino
```json
{"type": "data", "pv": 25.3, "sp": 25.0, "output": 128, "error": -0.3, 
 "P": 10.2, "I": 5.1, "D": -0.5, "time": 1234}
{"type": "status", "running": true, "kp": 2.0, "ki": 0.1, "kd": 0.05}
{"type": "debug", "debug": "Control started"}
{"type": "error", "message": "Safety error triggered"}
```

## Tuning Guide

### 1. Initial Setup
- Start with conservative PID values
- Ensure safety features are configured
- Verify sensor readings are reasonable

### 2. Proportional Tuning
- Set Ki=0, Kd=0
- Increase Kp until oscillation starts
- Reduce Kp to 50% of oscillating value

### 3. Integral Tuning
- Add small Ki value
- Increase until steady-state error is eliminated
- Watch for windup and overshoot

### 4. Derivative Tuning
- Add Kd if system has overshoot
- Adjust to dampen oscillations
- Be careful with noisy sensors

### 5. Verification
- Use step tests to verify performance
- Check response to setpoint changes
- Test disturbance rejection

## Troubleshooting

### Connection Issues
- **Cannot connect**: Check COM port and ensure Arduino is connected
- **Port not listed**: Install Arduino drivers or check USB cable
- **Connection drops**: Reduce baud rate or check USB cable quality

### Data Issues
- **No data**: Verify Arduino sketch is uploaded and running
- **Garbled data**: Check baud rate matches (115200)
- **Stale values**: Check sensor wiring and configuration

### Control Issues
- **Control not working**: Verify output wiring and polarity
- **Oscillation**: Reduce Kp or add damping (Kd)
- **Slow response**: Increase Kp or add integral (Ki)
- **Cannot stop**: Check if error state is active

### Safety Features
- **Frequent errors**: Adjust safety thresholds
- **Stale data error**: Increase rate threshold or timeout
- **Out of range error**: Check sensor or adjust limits

## Advanced Features

### Step Response Analysis
The step test provides automatic calculation of:
- Rise time (10% to 90% of final value)
- Overshoot percentage
- Settling time (within 2% of setpoint)
- Steady-state error

### Data Export
CSV export includes:
- Timestamp (ms)
- Process Value (PV)
- Setpoint (SP)
- Control Output
- Error
- P, I, and D terms

### Multiple Serial Ports
The app supports any serial port:
- Standard Arduino: Serial
- Arduino Mega: Serial1, Serial2, Serial3
- ESP32: Multiple UART ports
- USB-to-Serial adapters

## Building Executable

To create a standalone executable:
```bash
python build_exe.py
```
This creates a Windows .exe file in the `dist` folder.

## Version History

### v1.0.0
- Added safety features monitoring
- Improved UI with debug messages
- Step response analysis
- Min/max tracking
- Configurable time windows
- Enhanced error handling

### v0.9.0
- Initial release
- Basic PID tuning
- Real-time plotting
- Data export

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review the Arduino examples
3. Test with the minimal companion sketch
4. Report issues with details about your setup
