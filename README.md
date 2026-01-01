# PID Control Library for Arduino

A simple and efficient PID (Proportional-Integral-Derivative) control library for Arduino projects. This library provides a clean interface for implementing PID controllers with features like anti-windup and output limiting.

## Features

- **Simple API**: Easy to use with minimal setup required
- **Anti-windup Protection**: Prevents integral term from growing unbounded
- **Output Limiting**: Configurable output limits for PWM control
- **Derivative on Measurement**: Avoids derivative kick on setpoint changes
- **Configurable Sample Time**: Control update frequency
- **Enable/Disable Control**: Turn controller on/off without losing state

## Installation

1. Download this library as a ZIP file
2. In Arduino IDE, go to Sketch > Include Library > Add .ZIP Library
3. Select the downloaded ZIP file

Or for PlatformIO:
- Add to your `platformio.ini`:
```ini
lib_deps = 
    PID_Control
```

## Quick Start

```cpp
#include <PID_Control.h>

// Create PID controller on pin 3 with normal polarity
PID_Control pid(3, true);

void setup() {
    // Initialize with Kp=2.0, Ki=0.5, Kd=0.1, setpoint=25.0
    pid.begin(2.0, 0.5, 0.1, 25.0);
}

void loop() {
    float input = readSensor(); // Your sensor reading
    pid.update(input);          // The ONLY method you need to call!
    delay(100);                 // Match sample time
}
```

## API Reference

### Constructor

```cpp
PID_Control(int out_pin, bool polarity)
```
- `out_pin`: PWM pin for output (use -1 for software only)
- `polarity`: true for normal, false for reverse acting

### Main Methods

```cpp
void begin(float Kp, float Ki, float Kd, float setpoint)
```
Initialize PID controller with tuning parameters and setpoint.

```cpp
void update(float input)
```
Update PID controller with new input value. Call this regularly in main loop.

```cpp
void setpoint(float setpoint)
```
Change the target setpoint.

### Control Methods

```cpp
void enable()
void disable()
bool isEnabled()
```
Enable or disable the PID controller.

### Tuning Methods

```cpp
void setPID(float Kp, float Ki, float Kd)
```
Update PID tuning parameters.

### Getter Methods

```cpp
float getKp()
float getKi()
float getKd()
float getSetpoint()
float getOutput()
```
Get current values.

### Configuration Methods

```cpp
void setOutputLimits(float min, float max)
```
Set output limits (default: 0-255 for PWM).

```cpp
void setIntegralLimits(float min, float max)
```
Set integral term limits for anti-windup.

```cpp
void setSampleTime(unsigned long sample_time)
```
Set minimum time between updates in milliseconds (default: 100ms).

```cpp
void reset()
```
Reset internal state (integral, previous values).

## Usage Tips

1. **Sample Time**: Ensure your loop delay matches the sample time for consistent performance
2. **Tuning**: Start with Kp only, then add Ki, finally Kd
3. **Output Limits**: Set appropriate limits for your actuator
4. **Anti-windup**: Use integral limits to prevent overshoot
5. **Derivative Filtering**: The library uses derivative on measurement to avoid spikes

## Examples

See the `examples` folder for:
- `basic_pid`: Simple temperature control example
- `pid_tuning_simple`: Interactive serial-based PID tuning helper
- `pid_tuning_helper`: Advanced tuning interface with comprehensive features

### PID Tuning Examples

The library includes two comprehensive tuning examples to help you find optimal PID values:

1. **pid_tuning_simple**: A user-friendly interface that guides you through the tuning process step by step
   - Interactive serial menu system
   - Real-time value monitoring
   - Step response testing
   - Built-in tuning guide

2. **pid_tuning_helper**: An advanced tuning interface with additional features
   - Detailed system configuration
   - Comprehensive data logging
   - Multiple test modes
   - Professional tuning interface

Both examples follow the practical tuning methodology:
- Start with P-only control
- Add integral to eliminate steady-state error
- Add derivative if needed to reduce overshoot

## Theory

The PID controller calculates output as:
```
Output = Kp * error + Ki * integral(error) - Kd * d(input)/dt
```

Where:
- error = setpoint - input
- Integral is accumulated over time
- Derivative is calculated on input (not error) to avoid setpoint spikes

## License

This library is open source. Feel free to use and modify for your projects.
