"""Memory tracking utilities for task execution monitoring.

Tracks per-process RAM and GPU VRAM usage during task execution.
Uses psutil for per-process RAM and pynvml (with nvidia-smi fallback)
for per-process VRAM.
"""

import os
import platform
import subprocess
import sys
import threading

import psutil


def _get_macos_phys_footprint() -> int | None:
    """Return macOS phys_footprint in bytes via task_info(), or None.

    phys_footprint is the metric Activity Monitor uses — it includes all
    physical memory attributed to the process: mmap'd regions, GPU memory
    backed by RAM, and memory-mapped files. RSS undercounts on macOS when
    torch/MPS uses mmap for tensor storage.
    """
    if sys.platform != "darwin":
        return None
    try:
        import ctypes
        import ctypes.util

        libc = ctypes.CDLL(ctypes.util.find_library("c"))

        TASK_VM_INFO = 22
        KERN_SUCCESS = 0

        # struct task_vm_info (from XNU osfmk/mach/task_info.h):
        #   mach_vm_size_t virtual_size;                 offset   0 (8 bytes)
        #   integer_t      region_count;                  offset   8 (4 bytes)
        #   integer_t      page_size;                     offset  12 (4 bytes)
        #   mach_vm_size_t resident_size;                 offset  16 (8 bytes)
        #   mach_vm_size_t resident_size_peak;            offset  24
        #   mach_vm_size_t device;                        offset  32
        #   mach_vm_size_t device_peak;                   offset  40
        #   mach_vm_size_t internal;                      offset  48
        #   mach_vm_size_t internal_peak;                 offset  56
        #   mach_vm_size_t external;                      offset  64
        #   mach_vm_size_t external_peak;                 offset  72
        #   mach_vm_size_t reusable;                      offset  80
        #   mach_vm_size_t reusable_peak;                 offset  88
        #   mach_vm_size_t purgeable_volatile_pmap;       offset  96
        #   mach_vm_size_t purgeable_volatile_resident;   offset 104
        #   mach_vm_size_t purgeable_volatile_virtual;    offset 112
        #   mach_vm_size_t compressed;                    offset 120
        #   mach_vm_size_t compressed_peak;               offset 128
        #   mach_vm_size_t compressed_lifetime;           offset 136
        #   mach_vm_size_t phys_footprint;  /* rev1 */    offset 144  <-- target
        PHYS_FOOTPRINT_OFFSET = 144
        buf = (ctypes.c_char * 512)()
        count = ctypes.c_uint32(512 // 4)  # count in natural_t units

        libc.mach_task_self.restype = ctypes.c_uint32
        task = libc.mach_task_self()

        ret = libc.task_info(task, TASK_VM_INFO, buf, ctypes.byref(count))
        if ret != KERN_SUCCESS:
            return None

        return ctypes.c_uint64.from_buffer(buf, PHYS_FOOTPRINT_OFFSET).value
    except Exception:
        return None


def get_ram_usage() -> int:
    """Return current process RAM usage in MB.

    On macOS, uses phys_footprint from task_info() — the same metric Activity
    Monitor shows. It captures all physical memory attributed to the process
    including mmap'd regions and GPU memory backed by RAM, which RSS misses
    when torch/MPS is active.

    On Windows/Linux, uses RSS (Resident Set Size).
    """
    # macOS: use phys_footprint (captures torch mmap + Metal GPU allocations)
    if sys.platform == "darwin":
        phys = _get_macos_phys_footprint()
        if phys is not None:
            return phys >> 20  # bytes -> MB
        # Fallback: memory_full_info().uss is more complete than RSS on macOS
        try:
            return psutil.Process(os.getpid()).memory_full_info().uss >> 20
        except Exception:
            pass

    # Windows/Linux: RSS is accurate for per-process measurement
    try:
        return psutil.Process(os.getpid()).memory_info().rss >> 20
    except Exception:
        pass
    # Fallback: /proc/self/status (Linux only)
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except Exception:
        pass
    return 0


def get_vram_usage() -> int | None:
    """Return VRAM used on GPU 0 in MB, or None if no NVIDIA GPU.

    Reads system-wide VRAM for the primary compute GPU only (index 0).
    Falls back to nvidia-smi if pynvml is unavailable.
    """
    # Try pynvml — read GPU 0 only
    try:
        import pynvml

        pynvml.nvmlInit()
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return mem.used >> 20  # bytes -> MB
        finally:
            pynvml.nvmlShutdown()
    except Exception:
        pass

    # Fallback to nvidia-smi — query GPU 0 only
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "-i", "0",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            line = result.stdout.strip().splitlines()[0].strip()
            if line:
                return int(float(line))
    except Exception:
        pass

    return None


def format_mb(mb: int) -> str:
    """Format MB value into human-readable string."""
    if mb >= 1024 * 1024:
        return f"{mb / (1024 * 1024):.2f} PB"
    elif mb >= 1024:
        return f"{mb / 1024:.1f} GB"
    return f"{mb} MB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds into human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}m {secs:.1f}s"


def log_task_stats(
    task_id: str,
    endpoint: str,
    model: str,
    peak_ram_mb: int,
    peak_vram_mb: int | None,
    duration: float,
) -> None:
    """Log task completion statistics to stdout.

    Args:
        task_id: Unique task identifier
        endpoint: The API endpoint that triggered this task
        model: The model type used (from settings['model_type'])
        peak_ram_mb: Peak process RSS during task (MB)
        peak_vram_mb: Peak process VRAM during task (MB), or None
        duration: Elapsed time in seconds
    """
    lines = [
        "",
        "=" * 60,
        f"Task ID:     {task_id}",
        f"Endpoint:    {endpoint}",
        f"Model:       {model}",
        f"Peak RAM:    {format_mb(peak_ram_mb)}",
    ]
    if peak_vram_mb is not None:
        lines.append(f"Peak VRAM:   {format_mb(peak_vram_mb)}")
    else:
        lines.append("Peak VRAM:   N/A (no NVIDIA GPU)")
    lines.append(f"Duration:    {format_duration(duration)}")
    lines.append("=" * 60)
    print("\n".join(lines))


class TaskMemoryTracker:
    """Track peak per-process RAM and GPU VRAM for a single task.

    Creates a baseline snapshot on init, then call sample() periodically
    (e.g. every 10s) to update peak values.
    """

    def __init__(self) -> None:
        self._peak_ram_mb: int = 0
        self._peak_vram_mb: int | None = None
        self._lock = threading.Lock()
        # Capture initial baseline
        self._peak_ram_mb = get_ram_usage()
        self._peak_vram_mb = get_vram_usage()

    def sample(self) -> None:
        """Take a sample and update peak values."""
        ram_mb = get_ram_usage()
        vram_mb = get_vram_usage()
        with self._lock:
            if ram_mb > self._peak_ram_mb:
                self._peak_ram_mb = ram_mb
            if vram_mb is not None:
                if self._peak_vram_mb is None or vram_mb > self._peak_vram_mb:
                    self._peak_vram_mb = vram_mb

    @property
    def peak_ram_mb(self) -> int:
        return self._peak_ram_mb

    @property
    def peak_vram_mb(self) -> int | None:
        return self._peak_vram_mb
