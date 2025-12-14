# 酒精與可燃氣體偵測之智慧通風與除味系統

作者:113453006 陳坤輝

---

## 專案簡介

本系統使用樹莓派搭配多組 MQ 氣體感測器（MQ-2、MQ-9、MQ-135）與 ADS1115 類比轉數位模組，即時量測環境中氣體濃度變化。系統透過多感測器資料融合與邊緣運算邏輯，將環境狀態分類為 Ambient、Alcohol-like 與 Gas-like，並依據狀態自動控制排風扇與除味霧化裝置，以降低異常氣體累積風險並改善室內空氣品質。


##  裝置照片
![Hardware Setup](images/Decice 1.jpg)





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

