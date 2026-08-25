import os

import clr
from PySide6.QtCore import QThread, Signal

class MonitorSensor:
    """管理 .NET 硬件对象的创建、绑定与读取"""

    def __init__(self, refpath: str):
        if not os.path.exists(refpath):
            raise FileNotFoundError(refpath)
        self._ref = refpath
        add_reference = getattr(clr, "AddReference", None)
        if not add_reference:
            raise RuntimeError(f"crl.AddReference not found!")
        add_reference(self._ref)
        from OpenHardwareMonitor.Hardware import Computer, SensorType, HardwareType  # type: ignore

        self._hw_cpu = None
        self._hw_gpu = None
        self._hw_ram = None

        self._cpu_load = None
        self._cpu_temp = None
        self._gpu_load = None
        self._gpu_temp = None
        self._ram_load = None

        self.computer = Computer()
        self.computer.CPUEnabled = True
        self.computer.GPUEnabled = True
        self.computer.RAMEnabled = True
        self.computer.Open()
        # 只读取 CPU占用率、温度 | GPU（1独立显卡）占用率、温度 | RAM占用率
        for hw in self.computer.Hardware:
            hw.Update()
            t = hw.HardwareType

            if t == HardwareType.CPU:
                self._hw_cpu = hw
                for s in hw.Sensors:
                    if s.SensorType == SensorType.Load and s.Name == "CPU Total":
                        self._cpu_load = s
                    if s.SensorType == SensorType.Temperature and s.Name == "CPU Package":
                        self._cpu_temp = s

            elif t in (HardwareType.GpuNvidia, HardwareType.GpuAti):
                self._hw_gpu = hw
                for s in hw.Sensors:
                    if s.SensorType == SensorType.Load and s.Name == "GPU Memory":
                        self._gpu_load = s
                    if s.SensorType == SensorType.Temperature:
                        self._gpu_temp = s

            elif t == HardwareType.RAM:
                self._hw_ram = hw
                for s in hw.Sensors:
                    if s.SensorType == SensorType.Load:
                        self._ram_load = s

    def readvalue(self):
        """统一读取所有硬件"""
        cpuload = cputemp = gpuload = gputemp = ramload = 0.0

        if self._hw_cpu:
            self._hw_cpu.Update()
            cpu_load_v = self._cpu_load.Value
            cpu_temp_v = self._cpu_temp.Value
            if cpu_load_v: cpuload = float(cpu_load_v)
            if cpu_temp_v: cputemp = float(cpu_temp_v)

        if self._hw_gpu:
            self._hw_gpu.Update()
            gpu_load_v = self._gpu_load.Value
            gpu_temp_v = self._gpu_temp.Value
            if gpu_load_v: gpuload = float(gpu_load_v)
            if gpu_temp_v: gputemp = float(gpu_temp_v)

        if self._hw_ram:
            self._hw_ram.Update()
            ram_load_v = self._ram_load.Value
            if ram_load_v: ramload = float(ram_load_v)

        return {"CPULoad": cpuload, "CPUTemp": cputemp, "GPULoad": gpuload, "GPUTemp": gputemp, "RAMLoad": ramload}

    def close(self):
        self.computer.Close()

class MonitorThread(QThread):
    """后台轮询线程"""
    reads = Signal(dict)
    msg = Signal(str)

    def __init__(self, refpath: str, interval=500):
        super().__init__()
        self._ref = refpath
        self._interval = interval
        self._running = False
        self._sensor = None

    def run(self):
        self._running = True
        try:
            self._sensor = MonitorSensor(self._ref)
        except Exception as e:
            self.msg.emit(str(e))
            return
        while self._running:
            monit_data = self._sensor.readvalue()
            self.reads.emit(monit_data)
            self.msleep(self._interval)
        self._sensor.close()

    def stop(self):
        self._running = False
        self.wait()
