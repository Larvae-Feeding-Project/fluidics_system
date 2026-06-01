#include <avr/wdt.h>

// Pin Definitions
const int startStopPin = 7; // To Pump Pin 7 (Purple)
const int dirPin = 3;       // To Pump Pin 3 (Red)
const int speedPin = 5;     // To Pump Pin 5 (Orange - 0-10kHz input)

void setup() {
  // Start serial communication at 115200 baud for Python
  Serial.begin(115200);

  // Initialize switches in an OPEN state (Disconnected - "open switch")
  pinMode(startStopPin, INPUT);
  pinMode(dirPin, INPUT);

  // Set the frequency/speed pin as an output
  pinMode(speedPin, OUTPUT);
  
  Serial.println("Arduino Ready. Waiting for commands...");
}

void loop() {
  // Check if data is available from fluidics module
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace/newlines
    command.toUpperCase();

    // --- START / STOP (PULSE TOGGLE) ---
    if (command == "TOGGLE") {
      // Connect to Ground (close circuit)
      pinMode(startStopPin, OUTPUT);
      digitalWrite(startStopPin, LOW); 
      
      // Hold for the pump to register
      delay(300); 
      
      // Release the button (open circuit)
      pinMode(startStopPin, INPUT); 
      
      Serial.println("ACK: PUMP TOGGLED");
    }

    // --- DIRECTION ---
    else if (command == "DIR_FWD") {
      pinMode(dirPin, INPUT); // Open circuit
      Serial.println("ACK: DIRECTION FORWARD");
    } 
    else if (command == "DIR_REV") {
      pinMode(dirPin, OUTPUT);
      digitalWrite(dirPin, LOW); // Close circuit to ground
      Serial.println("ACK: DIRECTION REVERSE");
    }

    // --- SPEED CONTROL (0 - 10,000 Hz) ---
    else if (command.startsWith("SPEED:")) {
      int freq = command.substring(6).toInt(); // Extract the number
      
      // Constrain to the pump's max 10kHz limit
      freq = constrain(freq, 0, 10000); 

      if (freq < 31) { // Send 0 if under hardware limit
        // tone() function limit is ~31Hz
        noTone(speedPin);
        Serial.println("ACK: SPEED 0 (Signal Off)");
      } else { // Send requested speed
        tone(speedPin, freq);
        Serial.println("ACK: SPEED " + String(freq) + " Hz");
      }
    }

    // --- EMERGENCY STOP & REBOOT ---
    else if (command == "ESTOP") {
      // Instantly kill the hardware outputs
      noTone(speedPin);
      pinMode(startStopPin, INPUT);

      // Reboot ack
      Serial.println("ACK: REBOOTING ARDUINO");
      delay(100);

      // Turn on the watchdog timer with a 15 millisecond timeout
      wdt_enable(WDTO_15MS);

      // Enter an infinite loop for reboot
      while(1) {}
    }
    
    // --- ERROR HANDLING ---
    else {
      Serial.println("ERR: UNKNOWN COMMAND");
    }
  }
}
