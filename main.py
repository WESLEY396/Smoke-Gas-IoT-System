#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import time
import smbus
from datetime import datetime
from collections import deque

import RPi.GPIO as GPIO


# ============================================================
# ADS1115
# ============================================================
ADS_ADDR = 0x48
bus = smbus.SMBus(1)

MUX = {
    0: 0x4000,  # MQ2
    1: 0x5000,  # MQ9
    2: 0x6000,  # MQ135
}
CONFIG_BASE = 0x8583  # single-shot, PGA ±4.096V, 128 SPS


def read_ads1115(channel: int) -> float:
    """Read single-shot voltage from ADS1115 channel."""
    cfg = CONFIG_BASE | MUX[channel]
    bus.write_i2c_block_data(ADS_ADDR, 0x01, [(cfg >> 8) & 0xFF, cfg & 0xFF])
    time.sleep(0.01)

    data = bus.read_i2c_block_data(ADS_ADDR, 0x00, 2)
    raw = (data[0] << 8) | data[1]
    if raw > 32767:
        raw -= 65536

    return raw * 4.096 / 32768.0


# ============================================================
# GPIO
# ============================================================
GREEN_LED, YELLOW_LED, RED_LED = 19, 26, 21
FAN_PIN, MIST_PIN = 17, 27

RELAY_ON, RELAY_OFF = GPIO.HIGH, GPIO.LOW

GPIO.setmode(GPIO.BCM)
GPIO.setup([GREEN_LED, YELLOW_LED, RED_LED], GPIO.OUT)
GPIO.setup(FAN_PIN, GPIO.OUT, initial=RELAY_OFF)
GPIO.setup(MIST_PIN, GPIO.OUT, initial=RELAY_OFF)


def set_led(label: str) -> None:
    """Set LED state based on label."""
    GPIO.output([GREEN_LED, YELLOW_LED, RED_LED], GPIO.LOW)

    if label == "ambient":
        GPIO.output(GREEN_LED, GPIO.HIGH)
    elif label == "alcohol":
        GPIO.output(YELLOW_LED, GPIO.HIGH)
    elif label == "gas":
        GPIO.output(RED_LED, GPIO.HIGH)


# ============================================================
# Parameters
# ============================================================
BASE_DIR = "/home/s113453006/project"
os.makedirs(BASE_DIR, exist_ok=True)

READ_INTERVAL = 0.3

# Threshold lines
AMBIENT_SIGNAL_P95 = 0.748
ALCOHOL_MQ9_P75 = 0.946
GAS_MQ2_P50 = 0.622
GAS_MQ135_P50 = 0.692

# Gas MQ2 absolute minimum (v6.2 key fix)
GAS_MQ2_MIN_ABS = 0.60

# Alcohol / Gas advanced tuning
ALCOHOL_DOMINANCE_MARGIN = 0.08
GAS_NEAR_RATIO = 0.92
ALCOHOL_BLOCK_GAS_RATIO = 0.95  # only for MQ2 (do not use MQ135)

# Fan
FAN_OFF_RATIO = 0.98
FAN_OFF_SIGNAL = AMBIENT_SIGNAL_P95 * FAN_OFF_RATIO
FAN_BOOT_FORCE_ON_S = 30

# Mist
GAS_EXPOSURE_THRESHOLD = 10
MIST_DELAY_S = 10
MIST_DURATION_S = 30

# Debounce / Lock
DEBOUNCE_WINDOW = 10
AMBIENT_HITS = 9
ALCOHOL_HITS = 8
GAS_HITS = 6
LOCK_GAS_NO_DOWNGRADE = True

# Filter
MED_WIN = 5
EMA_ALPHA = 0.3

# Print
PRINT_VERBOSE = True


# ============================================================
# Classifier (v6.2)
# ============================================================
def classify(mq2: float, mq9: float, mq135: float) -> str:
    """Return raw label: ambient / alcohol / gas."""
    sig = max(mq2, mq9, mq135)

    # Ambient guard
    if sig < AMBIENT_SIGNAL_P95:
        return "ambient"

    # Gas: MQ2 must be present
    mq2_present = mq2 >= GAS_MQ2_MIN_ABS

    gas_strict = (
        mq2_present
        and (mq2 >= GAS_MQ2_P50)
        and (mq135 >= GAS_MQ135_P50)
    )
    gas_near = (
        mq2_present
        and (mq2 >= GAS_MQ2_P50 * GAS_NEAR_RATIO)
        and (mq135 >= GAS_MQ135_P50 * GAS_NEAR_RATIO)
    )
    if gas_strict or gas_near:
        return "gas"

    # Alcohol: MQ9 dominates, MQ2 not in gas-like region
    mq9_high = mq9 >= ALCOHOL_MQ9_P75
    dominant = mq9 >= max(mq2, mq135) + ALCOHOL_DOMINANCE_MARGIN
    mq2_not_gas_like = mq2 < GAS_MQ2_P50 * ALCOHOL_BLOCK_GAS_RATIO

    if mq9_high and dominant and mq2_not_gas_like:
        return "alcohol"

    return "ambient"


# ============================================================
# Filter / Debounce
# ============================================================
class Filter:
    """Median(window) + EMA smoothing."""
    def __init__(self):
        self.buf = {k: deque(maxlen=MED_WIN) for k in ("mq2", "mq9", "mq135")}
        self.ema = {k: None for k in self.buf}

    def update(self, mq2: float, mq9: float, mq135: float):
        for k, v in zip(("mq2", "mq9", "mq135"), (mq2, mq9, mq135)):
            self.buf[k].append(v)

            med = sorted(self.buf[k])[len(self.buf[k]) // 2]
            if self.ema[k] is None:
                self.ema[k] = med
            else:
                self.ema[k] = (1 - EMA_ALPHA) * self.ema[k] + EMA_ALPHA * med

        return self.ema["mq2"], self.ema["mq9"], self.ema["mq135"]


class Debounce:
    """Debounce raw labels to a final label."""
    def __init__(self):
        self.h = deque(maxlen=DEBOUNCE_WINDOW)

    def push(self, label: str) -> None:
        self.h.append(label)

    def counts(self):
        return (
            self.h.count("ambient"),
            self.h.count("alcohol"),
            self.h.count("gas"),
        )

    def decide(self, prev: str) -> str:
        amb, alc, gas = self.counts()

        if gas >= GAS_HITS:
            return "gas"
        if alc >= ALCOHOL_HITS:
            return "alcohol"
        if amb >= AMBIENT_HITS:
            return "ambient"

        return prev


# ============================================================
# CSV
# ============================================================
def open_csv():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BASE_DIR, f"log_v6_2_{ts}.csv")

    f = open(path, "w", newline="", encoding="utf-8")
    w = csv.writer(f)
    w.writerow([
        "Time",
        "MQ2", "MQ9", "MQ135",
        "MQ2_f", "MQ9_f", "MQ135_f",
        "raw", "final",
        "deb_amb", "deb_alc", "deb_gas",
        "fan", "mist", "exposure",
    ])
    return f, w, path


# ============================================================
# Main
# ============================================================
def main():
    csv_f, log, csv_path = open_csv()
    boot_t0 = time.time()

    filt = Filter()
    deb = Debounce()

    final_label = "ambient"
    last_label = "ambient"

    exposure = 0
    mist_state = "OFF"
    mist_pending = None
    mist_end = None
    mist_used = False

    fan_on = False

    print("=== MQ Gas System v6.2 (MQ2 gate) ===")

    try:
        while True:
            now = time.time()

            # Read raw voltages
            mq2 = read_ads1115(0)
            mq9 = read_ads1115(1)
            mq135 = read_ads1115(2)

            # Filtered voltages used for classification
            mq2f, mq9f, mq135f = filt.update(mq2, mq9, mq135)

            # Raw -> Debounced label
            raw = classify(mq2f, mq9f, mq135f)
            deb.push(raw)

            decided = deb.decide(final_label)

            # Gas lock: prevent gas -> alcohol downgrade
            if LOCK_GAS_NO_DOWNGRADE and final_label == "gas" and decided == "alcohol":
                decided = "gas"

            final_label = decided

            # ----------------------------------------------------
            # Exposure counter (used for mist scheduling)
            # ----------------------------------------------------
            if final_label in ("gas", "alcohol"):
                exposure += 1
                if last_label == "ambient":
                    mist_used = False

            # ----------------------------------------------------
            # Fan control
            # ----------------------------------------------------
            boot_force = (now - boot_t0) < FAN_BOOT_FORCE_ON_S
            immediate = (raw in ("gas", "alcohol")) or (max(mq2f, mq9f, mq135f) >= AMBIENT_SIGNAL_P95)

            if boot_force or immediate:
                fan_on = True
            elif final_label == "ambient" and max(mq2f, mq9f, mq135f) < FAN_OFF_SIGNAL:
                fan_on = False

            GPIO.output(FAN_PIN, RELAY_ON if fan_on else RELAY_OFF)

            # ----------------------------------------------------
            # Mist control
            #   - stop immediately when gas/alcohol
            #   - schedule only on transition (gas/alcohol -> ambient)
            # ----------------------------------------------------
            if final_label in ("gas", "alcohol"):
                GPIO.output(MIST_PIN, RELAY_OFF)
                mist_state = "OFF"
                mist_pending = None

            elif last_label in ("gas", "alcohol") and final_label == "ambient":
                if exposure >= GAS_EXPOSURE_THRESHOLD and not mist_used:
                    mist_pending = now + MIST_DELAY_S
                exposure = 0

            if mist_pending is not None and now >= mist_pending:
                GPIO.output(MIST_PIN, RELAY_ON)
                mist_state = "ON"
                mist_end = now + MIST_DURATION_S
                mist_pending = None
                mist_used = True

            if mist_state == "ON" and mist_end is not None and now >= mist_end:
                GPIO.output(MIST_PIN, RELAY_OFF)
                mist_state = "OFF"

            # LED
            set_led(final_label)

            # ----------------------------------------------------
            # Print
            # ----------------------------------------------------
            if PRINT_VERBOSE:
                sig_f = max(mq2f, mq9f, mq135f)
                deb_amb, deb_alc, deb_gas = deb.counts()
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"MQ2={mq2:.3f}(f={mq2f:.3f}) "
                    f"MQ9={mq9:.3f}(f={mq9f:.3f}) "
                    f"MQ135={mq135:.3f}(f={mq135f:.3f}) | "
                    f"sig_f={sig_f:.3f} | "
                    f"raw={raw} -> final={final_label} | "
                    f"deb(amb/alc/gas)={deb_amb}/{deb_alc}/{deb_gas} | "
                    f"fan={'ON' if fan_on else 'OFF'} "
                    f"mist={mist_state} "
                    f"exp={exposure}"
                )

            # ----------------------------------------------------
            # CSV
            # ----------------------------------------------------
            deb_amb, deb_alc, deb_gas = deb.counts()
            log.writerow([
                datetime.now().strftime("%H:%M:%S"),
                f"{mq2:.3f}", f"{mq9:.3f}", f"{mq135:.3f}",
                f"{mq2f:.3f}", f"{mq9f:.3f}", f"{mq135f:.3f}",
                raw, final_label,
                deb_amb, deb_alc, deb_gas,
                int(fan_on), mist_state, exposure
            ])
            csv_f.flush()

            last_label = final_label
            time.sleep(READ_INTERVAL)

    except KeyboardInterrupt:
        pass

    finally:
        GPIO.output([FAN_PIN, MIST_PIN], RELAY_OFF)
        GPIO.cleanup()

        try:
            csv_f.close()
        except Exception:
            pass

        print("Done:", csv_path)


if __name__ == "__main__":
    main()
