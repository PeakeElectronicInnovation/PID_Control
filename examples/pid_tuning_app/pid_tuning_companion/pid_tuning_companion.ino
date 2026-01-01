/**************************************************************************************************
 * PID Tuning Companion Sketch - Enhanced Version
 * 
 * This sketch communicates with the Python PID Tuning App via serial.
 * Uses JSON protocol for robust data exchange.
 * 
 * Commands received (JSON):
 * {"cmd": "set_params", "kp": 2.0, "ki": 0.1, "kd": 0.05}
 * {"cmd": "set_sp", "value": 25.0}
 * {"cmd": "start"}
 * {"cmd": "stop"}
 * {"cmd": "get_status"}
 * {"cmd": "step_test", "amplitude": 10.0}
 * 
 * Data sent (JSON, 10Hz):
 * {"type": "data", "pv": 25.3, "sp": 25.0, "output": 128, "error": -0.3, "time": 1234}
 * {"type": "status", "running": true, "kp": 2.0, "ki": 0.1, "kd": 0.05}
 * {"type": "step_test_started", "amplitude": 10.0}
 * {"type": "step_test_complete"}
 **************************************************************************************************/

#include <PID_Control.h>
#include <ArduinoJson.h>

// =========================================================================
// CONFIGURATION
// =========================================================================

#define SENSOR_PIN A0              // Analog input pin
#define OUTPUT_PIN 3               // PWM output pin
#define SAMPLE_TIME 100            // PID update time (ms)
#define SERIAL_RATE 115200         // Serial baud rate
#define DATA_RATE 100              // Data send rate (ms)
#define STEP_TEST_DURATION 5000    // Step test duration (ms)

// Sensor calibration (adjust for your sensor)
#define SENSOR_MIN 0.0             // Minimum raw value
#define SENSOR_MAX 1023.0          // Maximum raw value
#define VALUE_MIN 0.0              // Minimum measured value
#define VALUE_MAX 100.0            // Maximum measured value
#define VALUE_UNIT "°C"            // Unit

// =========================================================================
// GLOBAL VARIABLES
// =========================================================================

PID_Control pid(OUTPUT_PIN, true);

// PID parameters
float Kp = 2.0;
float Ki = 0.1;
float Kd = 0.05;
float setpoint = 25.0;
int loopPeriod = 100;  // Control loop period in ms (default 100ms)

// System state
bool running = false;
bool stepTestActive = false;
float stepTestAmplitude = 10.0;
float originalSetpoint = 25.0;
unsigned long stepTestStartTime = 0;

// Anti-windup settings
bool antiWindupEnabled = true;
bool outputLimitEnabled = true;
float outputMin = 0.0;
float outputMax = 255.0;
bool integralLimitEnabled = false;
float integralMin = -40.0;
float integralMax = 40.0;

// Timing
unsigned long lastDataSend = 0;

// JSON document for parsing
StaticJsonDocument<400> doc;

// =========================================================================
// SETUP
// =========================================================================

void setup() {
    Serial.begin(SERIAL_RATE);
    while (!Serial) delay(10);
    
    // Initialize PID
    pid.begin(Kp, Ki, Kd, setpoint);
    pid.setOutputLimits(0, 255);
    pid.setSampleTime(SAMPLE_TIME);
    
    // Send initial status
    sendStatus();
    
    Serial.println("PID Tuning Interface Ready");
}

// =========================================================================
// MAIN LOOP
// =========================================================================

void loop() {
    // Check for incoming commands
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        processCommand(input);
    }
    
    // Update PID controller only when running
    if (running) {
        float processValue = readSensor();
        pid.update(processValue);
        
        // Handle step test timing
        if (stepTestActive) {
            if (millis() - stepTestStartTime > STEP_TEST_DURATION) {
                // End step test
                pid.setpoint(originalSetpoint);
                stepTestActive = false;
                Serial.println("{\"type\": \"step_test_complete\"}");
                sendStatus();
            }
        }
    } else {
        // Ensure output is 0 when not running
        analogWrite(OUTPUT_PIN, 0);
    }
    
    // Send data at regular intervals
    if (millis() - lastDataSend > DATA_RATE) {
        sendData();
        lastDataSend = millis();
    }
    
    delay(10);
}

// =========================================================================
// SENSOR READING
// =========================================================================

float readSensor() {
    int raw = analogRead(SENSOR_PIN);
    float value = map(raw, SENSOR_MIN, SENSOR_MAX, VALUE_MIN, VALUE_MAX);
    return value;
}

// =========================================================================
// COMMAND PROCESSING
// =========================================================================

void processCommand(String input) {
    // Parse JSON
    DeserializationError error = deserializeJson(doc, input);
    
    if (error) {
        Serial.println("{\"error\": \"Invalid JSON\"}");
        return;
    }
    
    String cmd = doc["cmd"];
    
    if (cmd == "set_params") {
        Kp = doc["kp"] | Kp;
        Ki = doc["ki"] | Ki;
        Kd = doc["kd"] | Kd;
        
        // Handle loop period
        if (doc.containsKey("loop_period")) {
            loopPeriod = doc["loop_period"];
            pid.setSampleTime(loopPeriod);
        }
        
        // Handle anti-windup settings
        if (doc.containsKey("anti_windup")) {
            antiWindupEnabled = doc["anti_windup"];
        }
        if (doc.containsKey("output_limit")) {
            outputLimitEnabled = doc["output_limit"];
        }
        if (doc.containsKey("output_min")) {
            outputMin = doc["output_min"];
        }
        if (doc.containsKey("output_max")) {
            outputMax = doc["output_max"];
        }
        if (doc.containsKey("integral_limit")) {
            integralLimitEnabled = doc["integral_limit"];
        }
        if (doc.containsKey("integral_min")) {
            integralMin = doc["integral_min"];
        }
        if (doc.containsKey("integral_max")) {
            integralMax = doc["integral_max"];
        }
        
        // Apply settings to PID
        pid.setPID(Kp, Ki, Kd);
        if (outputLimitEnabled) {
            pid.setOutputLimits(outputMin, outputMax);
        }
        if (antiWindupEnabled) {
            if (integralLimitEnabled) {
                // Use user-defined integral limits
                pid.setIntegralLimits(integralMin, integralMax);
            } else {
                // Set integral limits based on output limits to prevent windup
                pid.setIntegralLimits(outputMin * 0.5, outputMax * 0.5);
            }
        } else {
            // Disable integral limits
            pid.setIntegralLimits(-10000.0, 10000.0);
        }
        
        sendStatus();
    }
    else if (cmd == "set_sp") {
        setpoint = doc["value"] | setpoint;
        if (!stepTestActive) {
            pid.setpoint(setpoint);
        }
        sendStatus();
    }
    else if (cmd == "start") {
        running = true;
        pid.enable();
        sendStatus();
    }
    else if (cmd == "stop") {
        running = false;
        pid.disable();
        stepTestActive = false;
        pid.setpoint(setpoint);
        sendStatus();
    }
    else if (cmd == "get_status") {
        sendStatus();
    }
    else if (cmd == "step_test") {
        if (running) {
            stepTestAmplitude = doc["amplitude"] | 10.0;
            startStepTest();
        }
    }
    else {
        Serial.println("{\"error\": \"Unknown command\"}");
    }
}

// =========================================================================
// DATA TRANSMISSION
// =========================================================================

void sendData() {
    float pv = readSensor();
    float sp = pid.getSetpoint();
    float output = pid.getOutput();
    float error = sp - pv;
    unsigned long time = millis();
    
    // Get PID components
    float P = pid.getProportional();
    float I = pid.getIntegral();
    float D = pid.getDerivative();
    
    // Debug output every 5 seconds
    static unsigned long lastDebug = 0;
    if (millis() - lastDebug > 5000) {
        Serial.print("{\"type\": \"debug\", ");
        Serial.print("\"running\": " + String(running ? "true" : "false") + ", ");
        Serial.print("\"enabled\": " + String(pid.isEnabled() ? "true" : "false") + ", ");
        Serial.print("\"raw_output\": " + String(output, 2));
        Serial.println("}");
        lastDebug = millis();
    }
    
    Serial.print("{\"type\": \"data\", ");
    Serial.print("\"pv\": " + String(pv, 2) + ", ");
    Serial.print("\"sp\": " + String(sp, 2) + ", ");
    Serial.print("\"output\": " + String(output, 0) + ", ");
    Serial.print("\"error\": " + String(error, 2) + ", ");
    Serial.print("\"P\": " + String(P, 2) + ", ");
    Serial.print("\"I\": " + String(I, 2) + ", ");
    Serial.print("\"D\": " + String(D, 2) + ", ");
    Serial.println("\"time\": " + String(time) + "}");
}

void sendStatus() {
    Serial.print("{\"type\": \"status\", ");
    Serial.print("\"running\": " + String(running ? "true" : "false") + ", ");
    Serial.print("\"kp\": " + String(Kp, 3) + ", ");
    Serial.print("\"ki\": " + String(Ki, 4) + ", ");
    Serial.print("\"kd\": " + String(Kd, 4) + ", ");
    Serial.print("\"sp\": " + String(setpoint, 2) + ", ");
    Serial.print("\"loop_period\": " + String(loopPeriod) + ", ");
    Serial.print("\"anti_windup\": " + String(antiWindupEnabled ? "true" : "false") + ", ");
    Serial.print("\"output_limit\": " + String(outputLimitEnabled ? "true" : "false") + ", ");
    Serial.print("\"output_min\": " + String(outputMin, 1) + ", ");
    Serial.print("\"output_max\": " + String(outputMax, 1) + ", ");
    Serial.print("\"integral_limit\": " + String(integralLimitEnabled ? "true" : "false") + ", ");
    Serial.print("\"integral_min\": " + String(integralMin, 1) + ", ");
    Serial.print("\"integral_max\": " + String(integralMax, 1));
    Serial.println("}");
}

// =========================================================================
// STEP TEST
// =========================================================================

void startStepTest() {
    originalSetpoint = setpoint;
    float testSp = setpoint + stepTestAmplitude;
    
    // Clamp to valid range
    if (testSp > VALUE_MAX) testSp = setpoint - stepTestAmplitude;
    if (testSp < VALUE_MIN) testSp = setpoint + stepTestAmplitude;
    
    pid.setpoint(testSp);
    stepTestActive = true;
    stepTestStartTime = millis();
    
    Serial.println("{\"type\": \"step_test_started\", \"amplitude\": " + String(stepTestAmplitude) + "}");
}
