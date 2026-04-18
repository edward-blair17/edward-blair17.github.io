``
**Computer Science Capstone Portfolio**
Edward Blair | Southern New Hampshire University

**Project Overview**
This repository contains the professional artifacts developed during my Computer Science program at SNHU. These projects demonstrate my ability to engineer modular software, optimize performance through advanced algorithms, and manage data via secure full-stack architectures.

**Professional Self-Assessment**
I am a software engineer focused on building maintainable, scalable, and resilient systems. My journey has evolved from writing simple scripts to delivering sophisticated full-stack solutions with a security-first mindset. I value engineered code that follows professional standards and design patterns.

**Artifacts**

**Software Design and Engineering (Modular Thermostat System)**
Source: CS-350 Emerging Systems Architectures
Description: A transformation of a reactive thermostat prototype into a modular, professional-grade system.
Key Technical Focus: I moved away from monolithic code to a modular design pattern using specialized Toolboxes. This ensures the software is hardware-agnostic, scalable, and easy to maintain in a professional production environment.

**Algorithms and Data Structures (Enhanced Sensor Logic)**
Source: CS-350 (Logic Enhancement)
Description: This artifact focuses on the computational depth of the thermostat system, specifically addressing the real-world problem of sensor jitter.
Key Technical Focus: Implementation of a Moving Average algorithm utilizing a Rolling Buffer (deque) data structure. This manages the trade-off between responsiveness and stability, ensuring the system operates on clean, smoothed data.

**Databases (Animal Shelter REST API)**
Source: CS-340 Client/Server Development
Description: A full-stack migration of an animal shelter dashboard from Python to a modern Node.js/Express.js architecture.
Key Technical Focus: Transitioned to a multi-tier architecture with a secure REST API. It features Non-blocking I/O for high-concurrency and secure credential management via external configuration files.

**Installation and Environment Setup**

**C++ Thermostat Projects (Artifacts 1 and 2)**
These artifacts were developed and tested in a Linux Terminal environment on a Raspberry Pi.
  1. Environment: Ensure the Raspberry Pi is updated and the build-essential package is installed.
  2. Build command: Open the terminal and run: g++ -o ThermostatSystem main.cpp Toolboxes.cpp
  3. Run command: Execute the compiled binary: ./ThermostatSystem

**Node.js/MongoDB Database Project (Artifact 3)**
This requires Node.js and a MongoDB instance (local or Atlas).
  1. Install Dependencies: npm install
  2. Configure: Update secure_config.json with your MongoDB connection string and credentials.
  3. Launch: node server.js

**Technical Skills Demonstrated**
Architectures: Modular Design, Multi-tier REST APIs, Agile/Scrum.
Languages: C++, JavaScript, Python, HTML/CSS.
Frameworks: Node.js, Express.js, Angular (MEAN Stack).
Data Management: MongoDB (NoSQL), CRUD Operations, Data Smoothing Algorithms.
Security: JWT Authentication, Credential Masking, Defensive Programming.
