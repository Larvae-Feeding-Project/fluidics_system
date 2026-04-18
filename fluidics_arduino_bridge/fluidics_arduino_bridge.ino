// Pin Definitions
const int startStopPin = 3; // To Pump Pin 11 (Purple)
const int dirPin = 4;       // To Pump Pin 5 (Red)
const int speedPin = 5;     // To Pump Pin 7 (Orange - 0-10kHz input)

void setup() {
  // Start serial communication at 115200 baud for Python
  Serial.begin(115200);

  // Initialize switches in an OPEN state (High Impedance / Disconnected)
  // This safely simulates an open physical switch.
  pinMode(startStopPin, INPUT);
  pinMode(dirPin, INPUT);

  // Set the frequency/speed pin as an output
  pinMode(speedPin, OUTPUT);
  
  Serial.println("Arduino Ready. Waiting for commands...");
}

void loop() {
  // Check if data is available from Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace/newlines
    command.toUpperCase();

    // --- START / STOP ---
    if (command == "START") {
      // Pull to Ground to close the circuit
      pinMode(startStopPin, OUTPUT);
      digitalWrite(startStopPin, LOW); 
      Serial.println("ACK: PUMP RUNNING");
    } 
    else if (command == "STOP") {
      // Set to High Impedance to open the circuit
      pinMode(startStopPin, INPUT); 
      Serial.println("ACK: PUMP STOPPED");
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
    // Example command from Python: "SPEED:5000" (for 50% speed)
    else if (command.startsWith("SPEED:")) {
      int freq = command.substring(6).toInt(); // Extract the number
      
      // Constrain to the pump's max 10kHz limit
      freq = constrain(freq, 0, 10000); 

      if (freq < 31) {
        // The Arduino tone() function cannot reliably generate below ~31Hz.
        // If it's too low, we just turn off the signal.
        noTone(speedPin);
        Serial.println("ACK: SPEED 0 (Signal Off)");
      } else {
        tone(speedPin, freq);
        Serial.println("ACK: SPEED " + String(freq) + " Hz");
      }
    }
    
    // --- ERROR HANDLING ---
    else {
      Serial.println("ERR: UNKNOWN COMMAND");
    }
  }
}
