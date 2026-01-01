/**************************************************************************************************
 * PID Tuning Helper - Simple and Reliable Version
 * 
 * This example helps you tune your PID controller step by step.
 * 
 * HARDWARE SETUP:
 * - Connect sensor to analog pin A0
 * - Connect control output to PWM pin 3
 * - Open Serial Monitor at 115200 baud
 * - Set line ending to "Newline" (NL)
 **************************************************************************************************/

#include <PID_Control.h>

// =========================================================================
// USER CONFIGURATION
// =========================================================================

#define SENSOR_PIN A0              // Sensor input pin
#define OUTPUT_PIN 3               // PWM output pin
#define SAMPLE_TIME 100            // PID update time (ms)

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

// System state
bool running = false;
bool testing = false;
unsigned long testStart = 0;

// Menu state
int currentMenu = 0;  // 0=main, 1= tune P, 2=tune I, 3=tune D

// =========================================================================
// SENSOR READING
// =========================================================================

float readSensor() {
    int raw = analogRead(SENSOR_PIN);
    float value = map(raw, SENSOR_MIN, SENSOR_MAX, VALUE_MIN, VALUE_MAX);
    return value;
}

// =========================================================================
// SETUP
// =========================================================================

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    Serial.println("\n=====================================");
    Serial.println("     PID TUNING HELPER");
    Serial.println("=====================================");
    Serial.println("\nConfigure your sensor in the code");
    Serial.println("then use this menu to tune PID values.\n");
    
    pid.begin(Kp, Ki, Kd, setpoint);
    pid.setOutputLimits(0, 255);
    pid.setSampleTime(SAMPLE_TIME);
    
    showMainMenu();
}

// =========================================================================
// MAIN LOOP
// =========================================================================

void loop() {
    // Read serial input
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        
        if (currentMenu == 0) {
            handleMainMenu(input);
        } else if (currentMenu == 1) {
            handleTuneP(input);
        } else if (currentMenu == 2) {
            handleTuneI(input);
        } else if (currentMenu == 3) {
            handleTuneD(input);
        }
    }
    
    // Update PID
    if (running) {
        float value = readSensor();
        pid.update(value);
        
        // Print values every 2 seconds
        static unsigned long lastPrint = 0;
        if (millis() - lastPrint > 2000) {
            Serial.print("Value: " + String(value, 1));
            Serial.print(" | Setpoint: " + String(setpoint, 1));
            Serial.print(" | Output: " + String(pid.getOutput(), 0));
            Serial.print(" | Error: " + String(setpoint - value, 1));
            Serial.println();
            lastPrint = millis();
        }
        
        // Test mode output
        if (testing) {
            static unsigned long lastTest = 0;
            if (millis() - lastTest > SAMPLE_TIME) {
                float t = (millis() - testStart) / 1000.0;
                Serial.println(String(t, 1) + "," + String(value, 1) + "," + String(setpoint, 1) + "," + String(pid.getOutput(), 0));
                lastTest = millis();
            }
        }
    }
    
    delay(50);
}

// =========================================================================
// MENU HANDLERS
// =========================================================================

void showMainMenu() {
    currentMenu = 0;
    Serial.println("\n-------------------------------------");
    Serial.println("MAIN MENU");
    Serial.println("-------------------------------------");
    Serial.println("Current values:");
    Serial.println("  Kp = " + String(Kp, 2));
    Serial.println("  Ki = " + String(Ki, 3));
    Serial.println("  Kd = " + String(Kd, 3));
    Serial.println("  Setpoint = " + String(setpoint, 1) + " " + VALUE_UNIT);
    Serial.println("  Control = " + String(running ? "ON" : "OFF"));
    Serial.println("-------------------------------------");
    Serial.println("Commands:");
    Serial.println("  1 - Start/Stop control");
    Serial.println("  2 - Change setpoint");
    Serial.println("  3 - Tune P gain");
    Serial.println("  4 - Tune I gain");
    Serial.println("  5 - Tune D gain");
    Serial.println("  6 - Step test");
    Serial.println("  7 - Show current values");
    Serial.println("  h - Show this menu");
    Serial.println("-------------------------------------");
    Serial.print("> ");
}

void handleMainMenu(String cmd) {
    if (cmd == "1") {
        running = !running;
        if (running) {
            pid.enable();
            Serial.println("\n>>> CONTROL STARTED <<<");
            Serial.println("Press 1 again to stop");
        } else {
            pid.disable();
            testing = false;
            Serial.println("\n>>> CONTROL STOPPED <<<");
        }
    }
    else if (cmd == "2") {
        Serial.print("\nEnter new setpoint (" + String(VALUE_MIN) + "-" + String(VALUE_MAX) + "): ");
        // Wait for input
        while (!Serial.available()) delay(10);
        float sp = Serial.parseFloat();
        if (sp >= VALUE_MIN && sp <= VALUE_MAX) {
            setpoint = sp;
            pid.setpoint(setpoint);
            Serial.println("Setpoint = " + String(setpoint, 1));
        } else {
            Serial.println("Invalid value!");
        }
    }
    else if (cmd == "3") {
        showTuneP();
    }
    else if (cmd == "4") {
        showTuneI();
    }
    else if (cmd == "5") {
        showTuneD();
    }
    else if (cmd == "6") {
        runStepTest();
    }
    else if (cmd == "7") {
        float v = readSensor();
        Serial.println("\nCurrent values:");
        Serial.println("  Input: " + String(v, 1) + " " + VALUE_UNIT);
        Serial.println("  Setpoint: " + String(setpoint, 1) + " " + VALUE_UNIT);
        Serial.println("  Output: " + String(pid.getOutput(), 0));
        Serial.println("  Error: " + String(setpoint - v, 1) + " " + VALUE_UNIT);
    }
    else if (cmd == "h") {
        showMainMenu();
        return;
    }
    else {
        Serial.println("Unknown command");
    }
    
    if (currentMenu == 0) {
        delay(1500);
        showMainMenu();
    }
}

// =========================================================================
// TUNING FUNCTIONS
// =========================================================================

void showTuneP() {
    currentMenu = 1;
    Serial.println("\n=====================================");
    Serial.println("TUNE PROPORTIONAL GAIN");
    Serial.println("=====================================");
    Serial.println("Tips:");
    Serial.println("• Start with P-only (Ki=0, Kd=0)");
    Serial.println("• Increase until slight overshoot");
    Serial.println("• Avoid oscillations");
    Serial.println("\nCommands:");
    Serial.println("  + - Increase Kp by 20%");
    Serial.println("  - - Decrease Kp by 20%");
    Serial.println("  0 - Set Ki and Kd to 0");
    Serial.println("  s - Quick step test");
    Serial.println("  x - Return to main menu");
    Serial.println("  OR enter a value directly");
    Serial.println("\nCurrent Kp = " + String(Kp, 2));
    Serial.print("Kp> ");
}

void handleTuneP(String cmd) {
    if (cmd == "+") {
        Kp *= 1.2;
        pid.setPID(Kp, 0, 0);
        Serial.println("Kp = " + String(Kp, 2));
    }
    else if (cmd == "-") {
        Kp /= 1.2;
        pid.setPID(Kp, 0, 0);
        Serial.println("Kp = " + String(Kp, 2));
    }
    else if (cmd == "0") {
        Ki = 0;
        Kd = 0;
        pid.setPID(Kp, 0, 0);
        Serial.println("Set to P-only: Kp=" + String(Kp, 2) + ", Ki=0, Kd=0");
    }
    else if (cmd == "s") {
        quickStepTest();
    }
    else if (cmd == "x") {
        pid.setPID(Kp, Ki, Kd);
        showMainMenu();
        return;
    }
    else if (cmd.length() > 0) {
        float newKp = cmd.toFloat();
        if (newKp >= 0 && newKp <= 100) {
            Kp = newKp;
            pid.setPID(Kp, 0, 0);
            Serial.println("Kp = " + String(Kp, 2));
        } else {
            Serial.println("Enter value between 0 and 100");
        }
    }
    
    Serial.print("Kp> ");
}

void showTuneI() {
    currentMenu = 2;
    Serial.println("\n=====================================");
    Serial.println("TUNE INTEGRAL GAIN");
    Serial.println("=====================================");
    Serial.println("Tips:");
    Serial.println("• Eliminates steady-state error");
    Serial.println("• Start small (0.01-0.1)");
    Serial.println("• Too much causes oscillation");
    Serial.println("\nCommands:");
    Serial.println("  + - Increase Ki by 50%");
    Serial.println("  - - Decrease Ki by 50%");
    Serial.println("  s - Quick step test");
    Serial.println("  x - Return to main menu");
    Serial.println("  OR enter a value directly");
    Serial.println("\nCurrent Ki = " + String(Ki, 3));
    Serial.print("Ki> ");
}

void handleTuneI(String cmd) {
    if (cmd == "+") {
        Ki *= 1.5;
        pid.setPID(Kp, Ki, 0);
        Serial.println("Ki = " + String(Ki, 3));
    }
    else if (cmd == "-") {
        Ki /= 1.5;
        pid.setPID(Kp, Ki, 0);
        Serial.println("Ki = " + String(Ki, 3));
    }
    else if (cmd == "s") {
        quickStepTest();
    }
    else if (cmd == "x") {
        pid.setPID(Kp, Ki, Kd);
        showMainMenu();
        return;
    }
    else if (cmd.length() > 0) {
        float newKi = cmd.toFloat();
        if (newKi >= 0 && newKi <= 10) {
            Ki = newKi;
            pid.setPID(Kp, Ki, 0);
            Serial.println("Ki = " + String(Ki, 3));
        } else {
            Serial.println("Enter value between 0 and 10");
        }
    }
    
    Serial.print("Ki> ");
}

void showTuneD() {
    currentMenu = 3;
    Serial.println("\n=====================================");
    Serial.println("TUNE DERIVATIVE GAIN");
    Serial.println("=====================================");
    Serial.println("Tips:");
    Serial.println("• Reduces overshoot");
    Serial.println("• Optional - PI often works fine");
    Serial.println("• Start very small (0.01-0.1)");
    Serial.println("\nCommands:");
    Serial.println("  + - Increase Kd by 50%");
    Serial.println("  - - Decrease Kd by 50%");
    Serial.println("  s - Quick step test");
    Serial.println("  x - Return to main menu");
    Serial.println("  OR enter a value directly");
    Serial.println("\nCurrent Kd = " + String(Kd, 3));
    Serial.print("Kd> ");
}

void handleTuneD(String cmd) {
    if (cmd == "+") {
        Kd *= 1.5;
        pid.setPID(Kp, Ki, Kd);
        Serial.println("Kd = " + String(Kd, 3));
    }
    else if (cmd == "-") {
        Kd /= 1.5;
        pid.setPID(Kp, Ki, Kd);
        Serial.println("Kd = " + String(Kd, 3));
    }
    else if (cmd == "s") {
        quickStepTest();
    }
    else if (cmd == "x") {
        showMainMenu();
        return;
    }
    else if (cmd.length() > 0) {
        float newKd = cmd.toFloat();
        if (newKd >= 0 && newKd <= 10) {
            Kd = newKd;
            pid.setPID(Kp, Ki, Kd);
            Serial.println("Kd = " + String(Kd, 3));
        } else {
            Serial.println("Enter value between 0 and 10");
        }
    }
    
    Serial.print("Kd> ");
}

// =========================================================================
// TEST FUNCTIONS
// =========================================================================

void runStepTest() {
    if (!running) {
        Serial.println("\nStart control first (option 1)");
        return;
    }
    
    Serial.print("\nEnter test setpoint (Enter for +10): ");
    while (!Serial.available()) delay(10);
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    float testSp = setpoint + 10.0;
    if (input.length() > 0) {
        testSp = input.toFloat();
    }
    
    Serial.println("\nStep test to " + String(testSp, 1));
    Serial.println("Time,Value,Setpoint,Output");
    Serial.println("Press any key to stop...");
    
    testing = true;
    testStart = millis();
    pid.setpoint(testSp);
    
    while (!Serial.available()) {
        delay(100);
    }
    
    pid.setpoint(setpoint);
    testing = false;
    Serial.println("\nTest complete");
}

void quickStepTest() {
    if (!running) {
        Serial.println("Start control first!");
        return;
    }
    
    Serial.println("\nQuick 10-second step test...");
    float oldSp = setpoint;
    float testSp = setpoint + 10.0;
    if (testSp > VALUE_MAX) testSp = setpoint - 10.0;
    
    Serial.println("Time,Value,Setpoint,Output");
    
    testing = true;
    testStart = millis();
    pid.setpoint(testSp);
    
    delay(10000);
    
    pid.setpoint(oldSp);
    testing = false;
    Serial.println("\nDone");
}
