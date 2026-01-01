/**************************************************************************************************
 * PID Tuning Companion Sketch - Simplified Version using PID_Tune Library
 * 
 * This is a drop-in replacement for the original companion sketch.
 * Uses the PID_Tune library for all communication and control logic.
 **************************************************************************************************/

#include <PID_Control.h>
#include <PID_Tune.h>

// =========================================================================
// CONFIGURATION
// =========================================================================

#define SENSOR_PIN A0              // Analog input pin
#define OUTPUT_PIN 3               // PWM output pin
#define SAMPLE_TIME 100            // PID update time (ms)

// Sensor calibration (adjust for your sensor)
#define SENSOR_MIN 0.0             // Minimum raw value
#define SENSOR_MAX 1023.0          // Maximum raw value
#define VALUE_MIN 0.0              // Minimum measured value
#define VALUE_MAX 100.0            // Maximum measured value
#define VALUE_UNIT "°C"            // Unit

// =========================================================================
// GLOBAL OBJECTS
// =========================================================================

PID_Control pid(OUTPUT_PIN, true);
PID_Tune tuner(pid);

// =========================================================================
// SENSOR READING FUNCTION
// =========================================================================

float readSensor() {
    // Read the raw analog value
    int rawValue = analogRead(SENSOR_PIN);
    
    // Convert to engineering units
    float measuredValue = map(rawValue, SENSOR_MIN, SENSOR_MAX, VALUE_MIN, VALUE_MAX);
    
    return measuredValue;
}

// =========================================================================
// SETUP
// =========================================================================

void setup() {
    // Initialize PID with default values
    pid.begin(2.0, 0.1, 0.05, 25.0);
    pid.setOutputLimits(0, 255);
    pid.setSampleTime(SAMPLE_TIME);
    
    // Initialize tuning interface
    tuner.begin(115200);
    
    // Attach sensor function
    tuner.setSensorCallback(readSensor);
    
    // Enable the tuning interface (but don't start control)
    tuner.enable();
    // Control will be started from the Python app Start button
}

// =========================================================================
// MAIN LOOP
// =========================================================================

void loop() {
    // Update tuning interface (handles all communication)
    tuner.update();
    
    // Run control if enabled
    if (tuner.isRunning()) {
        pid.update(readSensor());
    }
    
    // That's it! Everything else is handled by the library
}
