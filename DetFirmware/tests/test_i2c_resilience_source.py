from pathlib import Path
import re


SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.cpp"
I2C_MUX = Path(__file__).resolve().parents[1] / "src" / "i2c_mux.h"


def test_i2c_bus_uses_short_timeout_and_recovery_path():
    source = SOURCE.read_text(encoding="utf-8")

    assert "#define I2C_TRANSACTION_TIMEOUT_MS" in source
    assert "Wire.setTimeOut(I2C_TRANSACTION_TIMEOUT_MS)" in source
    assert "recoverI2CBus()" in source
    assert "recordI2CBusFault" in source
    assert "I2C_RECOVER:" in source


def test_sensor_task_feeds_watchdog_per_angle_channel_without_recovering_on_device_failure():
    source = SOURCE.read_text(encoding="utf-8")
    body = _function_body(source, "TaskSensors")
    read_idx = body.index("readMt6701AngleWithStatus(g_angleChannels[i], &angleStatus)")
    feed_idx = body.index("feedTaskWatchdog()", read_idx)

    assert feed_idx > read_idx
    assert "recordI2CBusFault(angleStatus == I2C_READ_MUX_ERROR)" in body
    assert "recordI2CReadResult(angleOk)" not in body


def test_angle_reader_distinguishes_mux_failure_from_device_read_failure():
    source = I2C_MUX.read_text(encoding="utf-8")

    assert "enum I2CReadStatus" in source
    assert "I2C_READ_MUX_ERROR" in source
    assert "I2C_READ_DEVICE_ERROR" in source
    assert "readMt6701AngleWithStatus" in source


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"void {name}\([^)]*\) \{{", source)
    assert match is not None, f"{name} not found"
    start = match.end()
    depth = 1
    pos = start
    while pos < len(source) and depth:
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
        pos += 1
    assert depth == 0, f"{name} body not closed"
    return source[start : pos - 1]
