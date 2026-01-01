# PID Tuning Application

A user-friendly Python GUI for tuning PID controllers with real-time visualization and analysis capabilities.

## Features

- **Real-time Plotting**: Live visualization of process value, setpoint, and control output
- **Interactive Control**: Adjust PID parameters and setpoint on the fly
- **Step Response Testing**: Built-in step test for system analysis
- **Data Logging**: Export data to CSV for further analysis
- **Intuitive Interface**: Clean, professional GUI design

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
   - Open `pid_tuning_companion/pid_tuning_companion.ino` in Arduino IDE
   - Configure sensor and output pins in the sketch if needed
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

3. **Tune Your PID Controller**:
   - Adjust PID parameters (Kp, Ki, Kd)
   - Click "Apply PID" to send values to Arduino
   - Click "Start" to begin control
   - Monitor performance in real-time plot
   - Use "Step Test" to analyze system response

4. **Save Your Data**:
   - Click "Save Data" to export CSV file
   - Data includes timestamps and all process variables

## Arduino Configuration

Edit these values in the Arduino sketch to match your system:

```cpp
#define SENSOR_PIN A0              // Analog input pin
#define OUTPUT_PIN 3               // PWM output pin
#define SAMPLE_TIME 100            // PID update time (ms)

// Sensor calibration
#define SENSOR_MIN 0.0             // Minimum raw value
#define SENSOR_MAX 1023.0          // Maximum raw value
#define VALUE_MIN 0.0              // Minimum measured value
#define VALUE_MAX 100.0            // Maximum measured value
#define VALUE_UNIT "°C"            // Unit
```

## Tuning Tips

1. **Start with P-only control** (Ki=0, Kd=0)
2. **Increase Kp** until you get slight overshoot
3. **Add Ki** to eliminate steady-state error
4. **Add Kd** if needed to reduce overshoot
5. **Use step tests** to verify performance

## Communication Protocol

The application uses JSON commands over serial:

**To Arduino**:
```json
{"cmd": "set_params", "kp": 2.0, "ki": 0.1, "kd": 0.05}
{"cmd": "set_sp", "value": 25.0}
{"cmd": "start"}
{"cmd": "stop"}
{"cmd": "step_test", "amplitude": 10.0}
```

**From Arduino**:
```json
{"type": "data", "pv": 25.3, "sp": 25.0, "output": 128, "error": -0.3, "time": 1234}
{"type": "status", "running": true, "kp": 2.0, "ki": 0.1, "kd": 0.05}
```

## Troubleshooting

- **Cannot connect**: Check COM port and ensure Arduino is connected
- **No data**: Verify Arduino sketch is uploaded and running
- **Erratic plot**: Check sensor wiring and calibration
- **Control not working**: Verify output wiring and polarity

## Future Enhancements

- Auto-tuning algorithms (Ziegler-Nichols, Cohen-Coon)
- Performance metrics calculation (rise time, settling time, overshoot)
- Multiple plot layouts
- Configuration save/load
- System identification tools
