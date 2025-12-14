# Smoke & Gas Smart Control System (Edge IoT)

This project implements an **Edge IoT-based gas detection and ventilation control system**
using Raspberry Pi and multiple MQ gas sensors.

The system performs **on-device sensing, rule-based state classification, and automatic actuation**
without relying on cloud services.

---

## 🔧 System Overview

- Platform: Raspberry Pi 4
- Sensors:
  - MQ-2 (Combustible gas / smoke-like response)
  - MQ-9 (Alcohol / CO sensitive)
  - MQ-135 (VOC / air quality variation)
- ADC: ADS1115 (16-bit)
- Actuators:
  - DC Fan (ventilation)
  - Ultrasonic mist module (odor removal)

---

## 🧠 Core Features

- Multi-sensor gas feature fusion
- Rule-based edge classification:
  - Ambient
  - Alcohol-like
  - Gas-like
- Debounce & hysteresis for stable state transition
- Event-driven fan and mist control
- Local CSV logging (time-series data)

---

## 🏗️ System Architecture

![Architecture](docs/architecture.png)

---

## 📂 Project Structure

