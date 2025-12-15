# 酒精與可燃氣體偵測之智慧通風與除味系統

作者:113453006 陳坤輝

---

## 專案簡介

本系統使用樹莓派搭配多組 MQ 氣體感測器（MQ-2、MQ-9、MQ-135）與 ADS1115 類比轉數位模組，即時量測環境中氣體濃度變化。系統透過多感測器資料融合與邊緣運算邏輯，將環境狀態分類為 Ambient、Alcohol-like 與 Gas-like，並依據狀態自動控制排風扇與除味霧化裝置，以降低異常氣體累積風險並改善室內空氣品質。


##  裝置照片
![Hardware Setup](images/device2.JPG)
![Hardware Setup](images/device1.JPG)


##  程式碼功能說明
## 🧩 Code Function Overview

本系統以 Python 撰寫，運行於 Raspberry Pi，核心功能為在邊緣端即時讀取多顆氣體感測器資料，進行狀態判斷，並自動控制通風與除味裝置。整體程式架構採用模組化設計，主要功能如下：

### 1️⃣ Sensor Data Acquisition
- 透過 I²C 介面讀取 ADS1115（16-bit ADC）數值
- 支援多通道類比輸入，分別對應 MQ-2、MQ-9、MQ-135 氣體感測器
- 將原始 ADC 數值轉換為實際電壓值，作為後續分析依據
<img width="846" height="603" alt="image" src="https://github.com/user-attachments/assets/76bac434-a21d-4508-b003-475c13661897" />

### 2️⃣ Signal Pre-processing
- 對感測數據進行濾波處理（Median Filter + Exponential Moving Average）
- 降低瞬間雜訊與環境干擾對判斷結果的影響
- 提升整體系統穩定性與判斷一致性
<img width="755" height="510" alt="image" src="https://github.com/user-attachments/assets/ede4590a-6848-4f1a-a18a-7fdd01ae9a10" />

### 3️⃣ Rule-based State Classification
- 採用規則式（Rule-based）邊緣判斷邏輯，非依賴雲端或 AI 模型
- 根據多感測器特徵組合，將環境狀態分類為：
  - **Ambient**：正常環境狀態
  - **Alcohol-like**：酒精 / VOC 類氣體特徵
  - **Gas-like**：可燃氣體相關特徵
- 透過多條門檻線與感測器交叉判斷，避免單一感測器誤判
<img width="719" height="675" alt="image" src="https://github.com/user-attachments/assets/8d5d09f4-6df8-483e-960f-cb084370ed0c" />

### 4️⃣ Debounce & Hysteresis Mechanism
- 使用時間視窗（Debounce Window）累積多次判斷結果
- 僅在狀態穩定達到指定次數後才切換系統狀態
- 加入 Hysteresis 設計，避免狀態在臨界值附近頻繁切換
<img width="670" height="638" alt="image" src="https://github.com/user-attachments/assets/b190bc2d-bc65-46d2-8bcb-84d8e153ce36" />

### 5️⃣ Event-driven Actuator Control
- 依最終判斷狀態自動控制 GPIO 輸出
- **排風扇（Fan）**
  - 在 Alcohol-like 或 Gas-like 狀態時立即啟動
  - 環境回復正常且低於指定門檻後才關閉
- **霧化裝置（Mist）**
  - 僅在氣體事件結束後才啟動
  - 支援延遲啟動與單次噴霧機制，避免過度除味
<img width="702" height="317" alt="image" src="https://github.com/user-attachments/assets/29d93a32-3bec-4105-9ab2-30b279af85a6" />
<img width="614" height="554" alt="image" src="https://github.com/user-attachments/assets/c5500892-efee-4316-ac15-d1a9cc1a886c" />

### 6️⃣ Status Indication
- 透過 LED 指示目前系統狀態：
  - 綠燈：Ambient
  - 黃燈：Alcohol-like
  - 紅燈：Gas-like
- 提供即時、直覺的視覺回饋
<img width="532" height="184" alt="image" src="https://github.com/user-attachments/assets/c81a430e-99eb-4886-b863-023ce73cb4e7" />

### 7️⃣ Data Logging
- 將每次感測數據、濾波後數值、狀態判斷結果與控制輸出
  以時間序列方式記錄至本地 CSV 檔案
- 方便後續參數調整、系統驗證與分析使用
<img width="690" height="480" alt="image" src="https://github.com/user-attachments/assets/525d301e-5b00-4042-a69f-638f8bc769a4" />

### 8️⃣ Edge IoT Design Characteristics
- 系統所有判斷與控制皆於 Raspberry Pi 本地端即時完成
- 不依賴雲端服務即可獨立運作
- 網路僅作為未來擴充（如資料上傳或遠端監控）用途

  ---

##  零件規格
<img width="559" height="272" alt="image" src="https://github.com/user-attachments/assets/1865aeca-0d91-4e46-8983-f967a2c7595d" />

<img width="559" height="319" alt="image" src="https://github.com/user-attachments/assets/8393035c-3ffc-4997-a209-9c15a21c6492" />

<img width="567" height="368" alt="image" src="https://github.com/user-attachments/assets/72023da2-944d-4f4d-8a29-8e9f67046cd1" />

<img width="562" height="369" alt="image" src="https://github.com/user-attachments/assets/75a9fa35-60f0-48af-9fc0-158859908686" />

<img width="280" height="326" alt="image" src="https://github.com/user-attachments/assets/bcb1b1e5-4f26-4f19-96e8-2e428a3b3cd0" />










##  對應Pin與外接電源電流分配
<img width="552" height="694" alt="image" src="https://github.com/user-attachments/assets/595762b6-dd02-4944-bcc1-189ec53d997d" />

##  接腳對應

<img width="588" height="570" alt="image" src="https://github.com/user-attachments/assets/a7d14552-8630-4524-80ae-a48ed368e4f8" />









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

## 影片Demo
https://www.youtube.com/watch?v=8FOCQ25Tr0I

## 動作說明:
1.先送外接電源驅動繼電器
2.打開程式碼
3.當環境空氣正常時，側板LED顯示為綠燈。
4.拿出酒精小瓶，在感測器前方進行兩次噴灑。
5.當偵測到酒精時，LED燈轉"黃"，吹風與抽風扇啟動。
6.當環境指數降回正常值，霧化器啟動，進行空氣芳香淨化30s。
7.接著拿出打火機，模擬瓦斯外洩，在感測器前方進行數次噴灑。
8.當偵測到瓦斯時，LED燈轉"紅"，吹風與抽風扇啟動。
9.當環境指數降回正常值，霧化器啟動，再次進行空氣芳香淨化30s。
10.Demo 完成。


