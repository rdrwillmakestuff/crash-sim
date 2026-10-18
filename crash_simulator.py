#!/usr/bin/env python3
"""
Crash Simulator
---------------
A fake crash-screen toy for Windows. It only draws pictures on top of your
screen. Nothing on your computer is changed, closed, or broken.

How to run:    python crash_simulator.py
Stop effect:   Ctrl+Shift+Q   (on the panel, Ctrl+Shift+Q quits)
Quit:          the red X on the panel
Every crash freezes the screen for a second and mutes your PC's sound first.
Sound comes back when the panel returns.
Optional:      pip install pillow
               -> makes the old-style Mac curtain darken smoothly.

Errors get added one at a time. This version has: Blue Screen of Death,
Black Screen of Death, Green Screen of Death, Mac Kernel Panic,
Linux Kernel Panic, No Bootable Device.
Phone errors: Your Device Is Corrupt, No Command, iPhone Recovery Mode,
Download Mode, Boot Loop.
Console errors: CE-34878-0, Not Turned Off Properly, PS4 Safe Mode, SU-30746-0,
Blue Light of Death, Xbox "Something went wrong", Switch Error 2162-0002.
Game Mode: Combo Challenge (your best score is saved in your home folder).
"""

import json
import math
import os
import random
import sys
import tkinter as tk
import tkinter.font as tkfont

IS_WIN = sys.platform.startswith("win")
if IS_WIN:
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)   # sharp text, true screen size
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

KEY = "#010203"          # this color becomes see-through
BSOD_BLUE = "#0078D7"
GSOD_GREEN = "#107C10"
PW, PH = 460, 526         # panel size
OLD_BLUE = "#0000AA"      # XP / Windows 7 blue screen color
STYLES = ["New (modern)", "Old (classic)"]

DELAYS = [(0, "Now"), (5, "5 seconds"), (10, "10 seconds"), (30, "30 seconds")]

STOP_CODES = [
    "CRITICAL_PROCESS_DIED",
    "IRQL_NOT_LESS_OR_EQUAL",
    "SYSTEM_SERVICE_EXCEPTION",
    "PAGE_FAULT_IN_NONPAGED_AREA",
    "KERNEL_SECURITY_CHECK_FAILURE",
    "DPC_WATCHDOG_VIOLATION",
    "VIDEO_TDR_FAILURE",
    "MEMORY_MANAGEMENT",
    "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED",
    "UNEXPECTED_STORE_EXCEPTION",
    "KMODE_EXCEPTION_NOT_HANDLED",
]
STOP_HEX = {
    "CRITICAL_PROCESS_DIED": 0xEF,
    "IRQL_NOT_LESS_OR_EQUAL": 0x0A,
    "SYSTEM_SERVICE_EXCEPTION": 0x3B,
    "PAGE_FAULT_IN_NONPAGED_AREA": 0x50,
    "KERNEL_SECURITY_CHECK_FAILURE": 0x139,
    "DPC_WATCHDOG_VIOLATION": 0x133,
    "VIDEO_TDR_FAILURE": 0x116,
    "MEMORY_MANAGEMENT": 0x1A,
    "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED": 0x7E,
    "UNEXPECTED_STORE_EXCEPTION": 0x154,
    "KMODE_EXCEPTION_NOT_HANDLED": 0x1E,
}
WHAT_FAILED = {
    "VIDEO_TDR_FAILURE": "nvlddmkm.sys",
    "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED": "atikmdag.sys",
    "KMODE_EXCEPTION_NOT_HANDLED": "ndis.sys",
}

EVENTS = [
    dict(key="bsod", name="Blue Screen of Death", desc="Stop code, % counter, then a restart",
         color=BSOD_BLUE, ready=True),
    dict(key="black", name="Black Screen of Death", desc="The 2025 Windows 11 version",
         color="#151515", ready=True),
    dict(key="green", name="Green Screen of Death", desc="Windows Insider build crash",
         color=GSOD_GREEN, ready=True),
    dict(key="mac", name="Mac Kernel Panic", desc="Gray \"restart your computer\" screen",
         color="#6B6B6B", ready=True),
    dict(key="linux", name="Linux Kernel Panic", desc="Wall of console text",
         color="#202020", ready=True),
    dict(key="noboot", name="No Bootable Device", desc="The BIOS can't find a drive",
         color="#000000", ready=True),
]

PHONE_EVENTS = [
    dict(key="corrupt", name="Your Device Is Corrupt", desc="Android red warning at startup",
         color="#000000", ready=True),
    dict(key="nocmd", name="No Command", desc="Android recovery screen",
         color="#202020", ready=True),
    dict(key="iphone", name="iPhone Recovery Mode", desc="\"Connect to a computer\" screen",
         color="#000000", ready=True),
    dict(key="download", name="Download Mode", desc="\"Do not turn off target!!\"",
         color="#1F4FA0", ready=True),
    dict(key="bootloop", name="Boot Loop", desc="The startup screen restarts forever",
         color="#111111", ready=True),
]
PHONE_DISPLAYS = ["Phone-shaped", "Full screen"]

CONSOLE_EVENTS = [
    dict(key="ce34878", name="CE-34878-0", desc="PS4 game crash popup",
         color="#1B2440", ready=True),
    dict(key="notoff", name="Not Turned Off Properly", desc="PS4 checks storage after a power cut",
         color="#000000", ready=True),
    dict(key="safemode", name="PS4 Safe Mode", desc="The menu when it won't start normally",
         color="#000000", ready=True),
    dict(key="su30746", name="SU-30746-0", desc="\"Cannot start the PS4\"",
         color="#000000", ready=True),
    dict(key="bluelight", name="Blue Light of Death", desc="No picture, just a pulsing blue light",
         color="#0A1A3A", ready=True),
    dict(key="xboxerr", name="Xbox \"Something went wrong\"", desc="Green error screen with a code",
         color="#107C10", ready=True),
    dict(key="switcherr", name="Switch Error 2162-0002", desc="\"The software was closed\"",
         color="#2D2D2D", ready=True),
]
GAME_LABELS = [
    ("bsod", "Blue Screen"), ("black", "Black Screen"), ("green", "Green Screen"),
    ("mac", "Mac Panic"), ("linux", "Linux Panic"), ("noboot", "No Boot Device"),
    ("corrupt", "Device Corrupt"), ("nocmd", "No Command"), ("iphone", "iPhone Recovery"),
    ("download", "Download Mode"), ("bootloop", "Boot Loop"), ("ce34878", "CE-34878-0"),
    ("notoff", "Not Turned Off"), ("safemode", "PS4 Safe Mode"), ("su30746", "SU-30746-0"),
    ("bluelight", "Blue Light"), ("xboxerr", "Xbox Error"), ("switcherr", "Switch Error"),
]
GAME_NAME = dict(GAME_LABELS)
BEST_FILE = os.path.join(os.path.expanduser("~"), ".crash_simulator_best.txt")
# (name, seconds you start with, extra seconds per error in the list)
DIFFICULTIES = [("Easy", 8.0, 4.0), ("Normal", 6.0, 3.0), ("Hard", 4.0, 2.0)]
BOARD_GROUPS = [("PC", ["bsod", "black", "green", "mac", "linux", "noboot"]),
                ("Phone", ["corrupt", "nocmd", "iphone", "download", "bootloop"]),
                ("Console", ["ce34878", "notoff", "safemode", "su30746", "bluelight",
                             "xboxerr", "switcherr"])]

FAKE_GAMES = ["Galaxy Racers 2", "Block Kingdom", "Neon Strike: Overdrive", "Dino Kart Rally",
              "Shadow Ninja Legends", "Mega Monster Arena"]


# ---------------------------------------------------------------- windows ---
class SystemMute:
    """Mutes / un-mutes the PC's speakers through Windows Core Audio.
    Does nothing (safely) if anything goes wrong or it's not Windows."""

    CLSID_ENUM = "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
    IID_ENUM = "{A95664D2-9614-4F35-A746-DE8DB63617E6}"
    IID_VOLUME = "{5CDF2C82-841E-4546-9722-0CF74078229A}"

    def __init__(self):
        self.vol = None
        self.we_muted = False
        if not IS_WIN:
            return
        try:
            import uuid

            class GUID(ctypes.Structure):
                _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort),
                            ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]

            def guid(text):
                u = uuid.UUID(text)
                g = GUID(u.fields[0], u.fields[1], u.fields[2])
                g.Data4[:] = list(u.bytes[8:])
                return g

            self.GUID = GUID
            ole = ctypes.windll.ole32
            ole.CoInitialize(None)
            enum = ctypes.c_void_p()
            hr = ole.CoCreateInstance(ctypes.byref(guid(self.CLSID_ENUM)), None, 0x17,
                                      ctypes.byref(guid(self.IID_ENUM)), ctypes.byref(enum))
            if hr != 0:
                return
            dev = ctypes.c_void_p()
            self._call(enum, 4, (ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)),
                       0, 1, ctypes.byref(dev))                     # default speakers
            vol = ctypes.c_void_p()
            self._call(dev, 3, (ctypes.POINTER(GUID), ctypes.c_ulong, ctypes.c_void_p,
                                ctypes.POINTER(ctypes.c_void_p)),
                       ctypes.byref(guid(self.IID_VOLUME)), 0x17, None, ctypes.byref(vol))
            self._keep = (enum, dev)
            self.vol = vol
        except Exception:
            self.vol = None

    @staticmethod
    def _call(obj, index, argtypes, *args):
        vtbl = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        fn = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, *argtypes)(vtbl[index])
        return fn(obj, *args)

    def _get(self):
        state = ctypes.c_int(0)
        self._call(self.vol, 15, (ctypes.POINTER(ctypes.c_int),), ctypes.byref(state))
        return bool(state.value)

    def _set(self, on):
        self._call(self.vol, 14, (ctypes.c_int, ctypes.c_void_p), 1 if on else 0, None)

    def mute(self):
        if not self.vol or self.we_muted:
            return
        try:
            if not self._get():          # only mute if it wasn't muted already
                self._set(True)
                self.we_muted = True
        except Exception:
            pass

    def restore(self):
        if not self.vol or not self.we_muted:
            return
        self.we_muted = False
        try:
            self._set(False)
        except Exception:
            pass


def screenshot_ppm(w, h):
    """Take a screenshot with plain Windows calls (no Pillow needed).
    Returns PPM image bytes that Tk can show, or None."""
    if not IS_WIN:
        return None
    try:
        u, g = ctypes.windll.user32, ctypes.windll.gdi32
        vp = ctypes.c_void_p
        u.GetDC.restype = vp
        u.GetDC.argtypes = [vp]
        u.ReleaseDC.argtypes = [vp, vp]
        g.CreateCompatibleDC.restype = vp
        g.CreateCompatibleDC.argtypes = [vp]
        g.CreateCompatibleBitmap.restype = vp
        g.CreateCompatibleBitmap.argtypes = [vp, ctypes.c_int, ctypes.c_int]
        g.SelectObject.restype = vp
        g.SelectObject.argtypes = [vp, vp]
        g.BitBlt.argtypes = [vp, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             vp, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
        g.GetDIBits.argtypes = [vp, vp, ctypes.c_uint, ctypes.c_uint, vp, vp, ctypes.c_uint]
        g.DeleteObject.argtypes = [vp]
        g.DeleteDC.argtypes = [vp]

        class BMIH(ctypes.Structure):
            _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                        ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                        ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                        ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                        ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                        ("biClrImportant", ctypes.c_uint32)]

        class BMI(ctypes.Structure):
            _fields_ = [("h", BMIH), ("colors", ctypes.c_uint32 * 3)]

        screen = u.GetDC(None)
        mem = g.CreateCompatibleDC(screen)
        bmp = g.CreateCompatibleBitmap(screen, w, h)
        old = g.SelectObject(mem, bmp)
        g.BitBlt(mem, 0, 0, w, h, screen, 0, 0, 0x00CC0020)       # copy the screen
        bmi = BMI()
        bmi.h.biSize = ctypes.sizeof(BMIH)
        bmi.h.biWidth = w
        bmi.h.biHeight = -h                                       # top-down rows
        bmi.h.biPlanes = 1
        bmi.h.biBitCount = 32
        buf = ctypes.create_string_buffer(w * h * 4)
        rows = g.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bmi), 0)
        g.SelectObject(mem, old)
        g.DeleteObject(bmp)
        g.DeleteDC(mem)
        u.ReleaseDC(None, screen)
        if rows != h:
            return None
        raw = buf.raw
        rgb = bytearray(w * h * 3)
        rgb[0::3] = raw[2::4]
        rgb[1::3] = raw[1::4]
        rgb[2::3] = raw[0::4]
        return b"P6 %d %d 255\n" % (w, h) + bytes(rgb)
    except Exception:
        return None


# ---------------------------------------------------------------- drawing ---
def _rgb(c):
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def mix(a, b, t):
    a, b = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(cv, x1, y1, x2, y2, c1, c2, tags=("panel",)):
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    h = y2 - y1
    for i in range(h):
        cv.create_line(x1, y1 + i, x2, y1 + i, fill=mix(c1, c2, i / max(1, h - 1)), tags=tags)


# ---------------------------------------------------------------- app -------
class CrashSimulator:
    def __init__(self):
        self.mute = SystemMute()
        r = self.root = tk.Tk()
        r.title("Crash Simulator")
        r.configure(bg=KEY)
        r.attributes("-fullscreen", True)
        r.attributes("-topmost", True)
        if IS_WIN:
            r.attributes("-transparentcolor", KEY)
        r.update_idletasks()
        self.W, self.H = r.winfo_screenwidth(), r.winfo_screenheight()

        self.cv = tk.Canvas(r, width=self.W, height=self.H, bg=KEY,
                            highlightthickness=0, bd=0)
        self.cv.pack(fill="both", expand=True)

        self.px = (self.W - PW) // 2
        self.py = (self.H - PH) // 2
        self.tab = "sandbox"
        self.maximized = False
        self.phone_disp_i = 0
        self.hover = None
        self.spots = []
        self.delay_i = 0
        self.code_i = 0
        self.style_i = 0
        self.any_key = None
        self.key_handler = None
        self._frames = []
        self.busy = False
        self.jobs = []
        self.drag = None
        self._img = None
        self.percent_item = None

        cv = self.cv
        cv.bind("<Motion>", self.on_motion)
        cv.bind("<Button-1>", self.on_press)
        cv.bind("<B1-Motion>", self.on_drag)
        cv.bind("<ButtonRelease-1>", lambda e: setattr(self, "drag", None))
        r.bind_all("<Control-Shift-Q>", self.on_stop_key)
        r.bind_all("<Control-Shift-q>", self.on_stop_key)
        r.bind_all("<Key>", self.on_any_key)
        r.protocol("WM_DELETE_WINDOW", self.quit)

        self.draw_panel()
        r.after(300, self.force_focus)
        self.game = None
        self.best = self.load_best()
        self.diff_i = 1
        self.maximized = False
        self.saved_pos = (self.px, self.py)
        cv.bind("<Double-Button-1>", self.on_double)
        r.bind("<Map>", self.on_restore)
        self.game_tick()

    # ----- helpers -----------------------------------------------------------
    def force_focus(self):
        r = self.root
        try:
            if r.state() == "iconic":      # a crash pops up even while minimized
                r.deiconify()
            r.lift()
            r.attributes("-topmost", True)
            r.focus_force()
            if IS_WIN:
                u, k = ctypes.windll.user32, ctypes.windll.kernel32
                hwnd = u.GetParent(r.winfo_id())
                fg = u.GetForegroundWindow()
                fg_thread = u.GetWindowThreadProcessId(fg, None)
                me = k.GetCurrentThreadId()
                u.AttachThreadInput(fg_thread, me, True)
                u.SetForegroundWindow(hwnd)
                u.AttachThreadInput(fg_thread, me, False)
        except Exception:
            pass

    def grab_pil(self):
        """Screenshot as a Pillow image, or None if Pillow isn't installed."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            if img.size != (self.W, self.H):
                img = img.resize((self.W, self.H))
            return img.convert("RGB")
        except Exception:
            return None

    def grab_screen(self):
        img = self.grab_pil()
        if img is not None:
            try:
                from PIL import ImageTk
                return ImageTk.PhotoImage(img)
            except Exception:
                pass
        ppm = screenshot_ppm(self.W, self.H)      # works without Pillow
        if ppm:
            try:
                return tk.PhotoImage(data=ppm, format="ppm")
            except Exception:
                pass
        return None

    FREEZE_MS = 1200

    def freeze(self):
        """Sound cuts out and the screen locks up, like a real crash starting."""
        self.mute.mute()
        self._pil = self.grab_pil()
        img = None
        if self._pil is not None:
            try:
                from PIL import ImageTk
                img = ImageTk.PhotoImage(self._pil)
            except Exception:
                img = None
        if img is None:
            img = self.grab_screen()
        if img is not None:
            self._img = img
            self.cv.create_image(0, 0, image=img, anchor="nw", tags="fx")
        self.cv.config(cursor="none")

    def dim_frozen(self, amount=0.65):
        """Darken the frozen screen (smoothly with Pillow, dotted without)."""
        if getattr(self, "_pil", None) is not None:
            try:
                from PIL import Image, ImageTk
                dark = Image.blend(self._pil, Image.new("RGB", self._pil.size, (0, 0, 0)), amount)
                self._dim = ImageTk.PhotoImage(dark)
                self.cv.create_image(0, 0, image=self._dim, anchor="nw", tags="fx")
                return
            except Exception:
                pass
        self.cv.create_rectangle(0, 0, self.W, self.H, fill="#000000", outline="",
                                 stipple="gray75", tags="fx")

    def on_any_key(self, e=None):
        if self.key_handler and e is not None:
            self.key_handler(e.keysym)
            return
        cb, self.any_key = self.any_key, None
        if cb:
            cb()

    def round_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.cv.create_polygon(pts, smooth=True, **kw)

    def power_icon(self, cx, cy, r, width, color="#FFFFFF"):
        cv = self.cv
        cv.create_arc(cx - r, cy - r, cx + r, cy + r, start=120, extent=300, style="arc",
                      outline=color, width=width, tags="fx")
        cv.create_line(cx, cy - r - width // 2, cx, cy - r * 0.15, fill=color, width=width,
                       capstyle="round", tags="fx")

    def later(self, ms, fn):
        self.jobs.append(self.root.after(ms, fn))

    def cancel_jobs(self):
        for j in self.jobs:
            try:
                self.root.after_cancel(j)
            except Exception:
                pass
        self.jobs = []

    # ----- hit areas ---------------------------------------------------------
    def spot(self, sid, x1, y1, x2, y2, cb):
        self.spots.append((sid, x1 - self.px, y1 - self.py, x2 - self.px, y2 - self.py, cb))

    def spot_at(self, x, y):
        for sid, x1, y1, x2, y2, cb in reversed(self.spots):
            if self.px + x1 <= x < self.px + x2 and self.py + y1 <= y < self.py + y2:
                return sid, cb
        return None

    def on_motion(self, e):
        if self.drag or self.busy:
            return
        hit = self.spot_at(e.x, e.y)
        sid = hit[0] if hit else None
        if sid != self.hover:
            self.hover = sid
            self.draw_panel()

    def on_press(self, e):
        if self.busy:
            return
        hit = self.spot_at(e.x, e.y)
        if hit and hit[1]:
            hit[1]()
            return
        if (not self.maximized and self.px <= e.x < self.px + PW
                and self.py <= e.y < self.py + 30):
            self.drag = (e.x, e.y)

    def on_drag(self, e):
        if not self.drag:
            return
        nx = min(max(self.px + e.x - self.drag[0], 80 - PW), self.W - 80)
        ny = min(max(self.py + e.y - self.drag[1], 0), self.H - 30)
        self.cv.move("panel", nx - self.px, ny - self.py)
        self.px, self.py = nx, ny
        self.drag = (e.x, e.y)

    # ----- panel widgets (Windows 7 style) -----------------------------------
    def w7button(self, sid, x1, y1, x2, y2, text, cb):
        cv = self.cv
        if self.hover == sid:
            tops, bots, border = ("#EAF6FD", "#D9F0FC"), ("#BEE6FD", "#A7D9F5"), "#3C7FB1"
        else:
            tops, bots, border = ("#F2F2F2", "#EBEBEB"), ("#DDDDDD", "#CFCFCF"), "#707070"
        mid = (y1 + y2) // 2
        vgrad(cv, x1 + 1, y1 + 1, x2, mid, *tops)
        vgrad(cv, x1 + 1, mid, x2, y2, *bots)
        cv.create_rectangle(x1, y1, x2, y2, outline=border, tags="panel")
        cv.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=text, font=("Segoe UI", -12),
                       fill="#000000", tags="panel")
        self.spot(sid, x1, y1, x2 + 1, y2 + 1, cb)

    def combo(self, sid, x1, y1, x2, y2, text, cb):
        cv = self.cv
        hov = self.hover == sid
        cv.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF",
                            outline="#3C7FB1" if hov else "#ABADB3", tags="panel")
        bx = x2 - 18
        if hov:
            vgrad(cv, bx, y1 + 1, x2, y2, "#EAF6FD", "#BEE6FD")
            cv.create_line(bx, y1 + 1, bx, y2, fill="#3C7FB1", tags="panel")
        my = (y1 + y2) // 2
        cv.create_polygon(bx + 5, my - 2, bx + 13, my - 2, bx + 9, my + 2,
                          fill="#000000", outline="", tags="panel")
        cv.create_text(x1 + 6, my, text=text, font=("Segoe UI", -12), fill="#000000",
                       anchor="w", tags="panel")
        self.spot(sid, x1, y1, x2 + 1, y2 + 1, cb)

    def lock_icon(self, x, y, color="#8A8A8A", s=1.0):
        cv = self.cv
        cv.create_arc(x + 1 * s, y - 6 * s, x + 7 * s, y + 2 * s, start=0, extent=180,
                      style="arc", outline=color, width=max(1, int(1.6 * s)), tags="panel")
        cv.create_rectangle(x, y, x + 8 * s, y + 6 * s, fill=color, outline="", tags="panel")

    def draw_panel(self):
        cv = self.cv
        cv.delete("panel")
        self.spots = []
        T = "panel"
        if self.maximized:          # the window fills the whole screen
            self.px, self.py = 0, 0
            x, y, x2, y2 = 0, 0, self.W, self.H
        else:
            x, y = self.px, self.py
            x2, y2 = x + PW, y + PH

        # glass frame + title bar
        vgrad(cv, x, y, x2, y + 30, "#D3E3F5", "#A9C5E6")
        vgrad(cv, x, y + 30, x2, y2, "#A9C5E6", "#BDD3EC")
        vgrad(cv, x + 1, y + 1, x2 - 1, y + 13, "#EEF4FB", "#D3E3F5")
        if not self.maximized:
            cv.create_rectangle(x, y, x2 - 1, y2 - 1, outline="#34506F", tags=T)
            cv.create_rectangle(x + 1, y + 1, x2 - 2, y2 - 2, outline="#E6EFF9", tags=T)

        # little monitor icon + title with glow
        cv.create_rectangle(x + 10, y + 8, x + 26, y + 19, fill="#2B7BD3", outline="#0E3F75", tags=T)
        cv.create_line(x + 18, y + 19, x + 18, y + 22, fill="#0E3F75", tags=T)
        cv.create_line(x + 13, y + 22, x + 24, y + 22, fill="#0E3F75", width=2, tags=T)
        f = ("Segoe UI", -12)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            cv.create_text(x + 33 + dx, y + 15 + dy, text="Crash Simulator", font=f,
                           fill="#EEF4FB", anchor="w", tags=T)
        cv.create_text(x + 33, y + 15, text="Crash Simulator", font=f, fill="#111111",
                       anchor="w", tags=T)

        # caption buttons
        rx = x2 - 7
        cx1 = rx - 43
        hov = self.hover == "close"
        vgrad(cv, cx1, y + 1, rx, y + 10, "#F9CFC5" if hov else "#F3B9AD", "#EA7F63" if hov else "#D96B53")
        vgrad(cv, cx1, y + 10, rx, y + 20, "#E04A2C" if hov else "#C73A21", "#F2A58A" if hov else "#E08A6F")
        cv.create_rectangle(cx1, y + 1, rx, y + 20, outline="#7A2617", tags=T)
        mx, my = (cx1 + rx) // 2, y + 10
        cv.create_line(mx - 5, my - 4, mx + 5, my + 4, fill="#FFFFFF", width=2, tags=T)
        cv.create_line(mx - 5, my + 4, mx + 5, my - 4, fill="#FFFFFF", width=2, tags=T)
        self.spot("close", cx1, y + 1, rx + 1, y + 21, self.quit)
        for bx1, bx2, glyph in ((cx1 - 25, cx1, "max"), (cx1 - 51, cx1 - 25, "min")):
            hv = self.hover == glyph
            vgrad(cv, bx1, y + 1, bx2, y + 10, "#F4FAFF" if hv else "#EEF4FB",
                  "#BFE0FA" if hv else "#CCDCF0")
            vgrad(cv, bx1, y + 10, bx2, y + 20, "#7FC1F2" if hv else "#B3CAE6",
                  "#A8D8FA" if hv else "#CADBF0")
            cv.create_rectangle(bx1, y + 1, bx2, y + 20, outline="#4C678C", tags=T)
            gx = (bx1 + bx2) // 2
            if glyph == "max" and self.maximized:      # "restore" icon: two windows
                cv.create_rectangle(gx - 2, y + 5, gx + 5, y + 11, outline="#2B3F5C", tags=T)
                cv.create_line(gx - 2, y + 6, gx + 6, y + 6, fill="#2B3F5C", width=2, tags=T)
                cv.create_rectangle(gx - 6, y + 9, gx + 1, y + 15, fill="#DCE8F5",
                                    outline="#2B3F5C", tags=T)
                cv.create_line(gx - 6, y + 10, gx + 2, y + 10, fill="#2B3F5C", width=2, tags=T)
            elif glyph == "max":
                cv.create_rectangle(gx - 5, y + 6, gx + 4, y + 14, outline="#2B3F5C", tags=T)
                cv.create_line(gx - 5, y + 7, gx + 5, y + 7, fill="#2B3F5C", width=2, tags=T)
            else:
                cv.create_rectangle(gx - 4, y + 13, gx + 4, y + 15, fill="#FFFFFF",
                                    outline="#2B3F5C", tags=T)
            self.spot(glyph, bx1, y + 1, bx2 + 1, y + 21,
                      self.toggle_max if glyph == "max" else self.minimize)

        # client area
        if self.maximized:
            cx, cy, cx2, cy2 = x, y + 30, x2, y2
        else:
            cx, cy, cx2, cy2 = x + 8, y + 30, x2 - 8, y2 - 8
        cv.create_rectangle(cx, cy, cx2, cy2, fill="#F0F0F0", outline="#7C92B2", tags=T)
        if self.maximized:          # Control Panel style layout for the big window
            self.draw_max_layout(cx, cy, cx2, cy2)
            if self.busy:
                cv.itemconfigure("panel", state="hidden")
            return
        # the tabs + page keep their normal size
        body_w, body_h = PW - 16, PH - 38
        bx = cx + max(0, (cx2 - cx - body_w) // 2)
        by = cy + max(0, (cy2 - cy - body_h) // 2)
        bx2 = bx + body_w
        page_top = by + 32
        page_bot = by + body_h - 30
        cv.create_rectangle(bx + 8, page_top, bx2 - 8, page_bot, fill="#FFFFFF",
                            outline="#898C95", tags=T)

        # tabs
        tx = bx + 10
        for tid, label, w in (("sandbox", "PC Errors", 76), ("phone", "Phone Errors", 90),
                              ("console", "Console Errors", 102), ("game", "Game Mode", 100)):
            sel = self.tab == tid
            hv = self.hover == "tab_" + tid
            top = page_top - 24 if sel else page_top - 21
            if sel:
                cv.create_rectangle(tx - 2, top, tx + w + 2, page_top, fill="#FFFFFF",
                                    outline="#898C95", tags=T)
                cv.create_line(tx - 1, page_top, tx + w + 2, page_top, fill="#FFFFFF", tags=T)
            else:
                vgrad(cv, tx, top, tx + w, page_top, "#EAF6FD" if hv else "#F5F5F5",
                      "#D3EDFB" if hv else "#E0E0E0")
                cv.create_rectangle(tx, top, tx + w, page_top,
                                    outline="#3C7FB1" if hv else "#898C95", tags=T)
            ty = (top + page_top) // 2
            cv.create_text(tx + w // 2, ty, text=label, font=("Segoe UI", -12),
                           fill="#000000", tags=T)
            self.spot("tab_" + tid, tx, top, tx + w, page_top, lambda t=tid: self.set_tab(t))
            tx += w + 4

        # status bar
        vgrad(cv, cx + 1, cy2 - 22, cx2, cy2, "#F4F7FC", "#DFE7F2")
        cv.create_line(cx + 1, cy2 - 22, cx2, cy2 - 22, fill="#C3CCD9", tags=T)
        cv.create_text(cx + 10, cy2 - 11, text="Ctrl+Shift+Q stops an effect",
                       font=("Segoe UI", -11), fill="#333333", anchor="w", tags=T)
        cv.create_text(cx2 - 10, cy2 - 11, text="Double-click the title bar to maximize"
                       if not self.maximized else "Double-click the title bar to restore",
                       font=("Segoe UI", -11), fill="#6A6A6A", anchor="e", tags=T)

        pl, pr, pt = bx + 22, bx2 - 22, page_top + 14
        if self.tab == "sandbox":
            self.draw_sandbox(pl, pr, pt)
        elif self.tab == "phone":
            self.draw_phones(pl, pr, pt)
        elif self.tab == "console":
            self.draw_consoles(pl, pr, pt)
        else:
            self.draw_game(pl, pr, pt, page_bot)

        if self.busy:
            cv.itemconfigure("panel", state="hidden")

    def draw_sandbox(self, pl, pr, pt):
        cv, T = self.cv, "panel"
        cv.create_text(pl, pt, text="Pick an error to play", font=("Segoe UI", -16),
                       fill="#1E3287", anchor="nw", tags=T)
        cv.create_text(pl, pt + 24, text="It covers your whole screen. Nothing on your PC is changed.",
                       font=("Segoe UI", -12), fill="#5A5A5A", anchor="nw", tags=T)
        ry = self.draw_rows(EVENTS, pl, pr, pt + 50)
        self.draw_after_rows(pl, pr, ry)

    def draw_rows(self, events, pl, pr, ry, phone=False, console=False):
        cv, T = self.cv, "panel"
        for ev in events:
            k, ready = ev["key"], ev["ready"]
            if ready and self.hover in ("row_" + k, "run_" + k):
                cv.create_rectangle(pl - 6, ry, pr + 6, ry + 33, fill="#E8F4FC",
                                    outline="#9ACFEF", tags=T)
            ix, iy = pl, ry + 6
            edge = "#3A3A3A" if ready else "#A8A8A8"
            fill = ev["color"] if ready else "#D2D2D2"
            if console:   # little console box with a light strip
                cv.create_rectangle(ix, iy + 4, ix + 26, iy + 16, fill=fill, outline=edge,
                                    tags=T)
                cv.create_line(ix + 3, iy + 12, ix + 23, iy + 12,
                               fill="#4DA3FF" if ready else "#BBBBBB", width=2, tags=T)
            elif phone:   # little phone icon
                cv.create_rectangle(ix + 7, iy - 2, ix + 20, iy + 21, fill=fill, outline=edge,
                                    width=2, tags=T)
                if k == "corrupt":
                    cv.create_text(ix + 13, iy + 9, text="!", font=("Segoe UI", -11, "bold"),
                                   fill="#E53935", tags=T)
            else:
                cv.create_rectangle(ix, iy, ix + 26, iy + 18, fill=fill, outline=edge, tags=T)
                cv.create_line(ix + 8, iy + 21, ix + 19, iy + 21, fill=edge, width=2, tags=T)
            if k == "bsod":
                cv.create_text(ix + 13, iy + 9, text=":(", font=("Segoe UI", -9),
                               fill="#FFFFFF", tags=T)
            cv.create_text(pl + 36, ry + 11, text=ev["name"], font=("Segoe UI", -12),
                           fill="#000000" if ready else "#8C8C8C", anchor="w", tags=T)
            cv.create_text(pl + 36, ry + 25, text=ev["desc"], font=("Segoe UI", -11),
                           fill="#6D6D6D" if ready else "#A6A6A6", anchor="w", tags=T)
            if ready:
                self.spot("row_" + k, pl - 6, ry, pr + 7, ry + 34, None)
                self.w7button("run_" + k, pr - 72, ry + 5, pr, ry + 28, "Run",
                              lambda kk=k: self.start_event(kk))
            else:
                cv.create_text(pr, ry + 17, text="Coming soon", font=("Segoe UI", -11),
                               fill="#9A9A9A", anchor="e", tags=T)
            ry += 34
        return ry

    def draw_after_rows(self, pl, pr, ry):
        cv, T = self.cv, "panel"
        cv.create_line(pl, ry + 6, pr, ry + 6, fill="#E3E3E3", tags=T)
        oy = ry + 20
        cv.create_text(pl, oy + 11, text="Start after:", font=("Segoe UI", -12),
                       fill="#000000", anchor="w", tags=T)
        self.combo("delay", pl + 90, oy, pl + 210, oy + 22, DELAYS[self.delay_i][1], self.next_delay)
        oy += 32
        codes = ["Random"] + STOP_CODES
        cv.create_text(pl, oy + 11, text="Stop code:", font=("Segoe UI", -12),
                       fill="#000000", anchor="w", tags=T)
        self.combo("code", pl + 90, oy, pr, oy + 22, codes[self.code_i], self.next_code)
        oy += 32
        cv.create_text(pl, oy + 11, text="Style:", font=("Segoe UI", -12),
                       fill="#000000", anchor="w", tags=T)
        self.combo("style", pl + 90, oy, pl + 250, oy + 22, STYLES[self.style_i], self.next_style)
        cv.create_text(pl + 260, oy + 11, text="(changes most errors)", font=("Segoe UI", -11),
                       fill="#8C8C8C", anchor="w", tags=T)

    def draw_phones(self, pl, pr, pt):
        cv, T = self.cv, "panel"
        cv.create_text(pl, pt, text="Pick a phone error to play", font=("Segoe UI", -16),
                       fill="#1E3287", anchor="nw", tags=T)
        cv.create_text(pl, pt + 24, text="Your monitor turns into a crashed phone screen.",
                       font=("Segoe UI", -12), fill="#5A5A5A", anchor="nw", tags=T)
        ry = self.draw_rows(PHONE_EVENTS, pl, pr, pt + 50, phone=True)
        cv.create_line(pl, ry + 6, pr, ry + 6, fill="#E3E3E3", tags=T)
        oy = ry + 20
        cv.create_text(pl, oy + 11, text="Start after:", font=("Segoe UI", -12),
                       fill="#000000", anchor="w", tags=T)
        self.combo("delay", pl + 90, oy, pl + 210, oy + 22, DELAYS[self.delay_i][1], self.next_delay)
        oy += 32
        cv.create_text(pl, oy + 11, text="Display:", font=("Segoe UI", -12),
                       fill="#000000", anchor="w", tags=T)
        self.combo("pdisp", pl + 90, oy, pl + 210, oy + 22, PHONE_DISPLAYS[self.phone_disp_i],
                   self.next_phone_disp)

    def draw_consoles(self, pl, pr, pt):
        cv, T = self.cv, "panel"
        cv.create_text(pl, pt, text="Pick a console error to play", font=("Segoe UI", -16),
                       fill="#1E3287", anchor="nw", tags=T)
        cv.create_text(pl, pt + 24, text="Your monitor acts like a game console that crashed.",
                       font=("Segoe UI", -12), fill="#5A5A5A", anchor="nw", tags=T)
        ry = self.draw_rows(CONSOLE_EVENTS, pl, pr, pt + 50, console=True)
        cv.create_line(pl, ry + 6, pr, ry + 6, fill="#E3E3E3", tags=T)
        oy = ry + 20
        cv.create_text(pl, oy + 11, text="Start after:", font=("Segoe UI", -12),
                       fill="#000000", anchor="w", tags=T)
        self.combo("delay", pl + 90, oy, pl + 210, oy + 22, DELAYS[self.delay_i][1], self.next_delay)

    def next_phone_disp(self):
        self.phone_disp_i = (self.phone_disp_i + 1) % len(PHONE_DISPLAYS)
        self.draw_panel()

    # ----- Game Mode: Combo Challenge ---------------------------------------
    def load_best(self):
        """Best score for each difficulty, saved in your home folder."""
        best = {name: 0 for name, _, _ in DIFFICULTIES}
        try:
            with open(BEST_FILE) as f:
                text = f.read().strip()
            if text.startswith("{"):
                best.update({k: int(v) for k, v in json.loads(text).items() if k in best})
            elif text:                      # older versions saved a single number
                best["Normal"] = int(text)
        except Exception:
            pass
        return best

    def save_best(self):
        try:
            with open(BEST_FILE, "w") as f:
                json.dump(self.best, f)
        except Exception:
            pass

    @property
    def diff(self):
        return DIFFICULTIES[self.diff_i]

    def next_diff(self):
        self.diff_i = (self.diff_i + 1) % len(DIFFICULTIES)
        self.draw_panel()

    def round_time(self, length):
        _, base, per = self.diff
        return base + per * length

    def new_chain(self, length):
        return random.sample([k for k, _ in GAME_LABELS], length)

    def start_game(self):
        self.game = dict(round=0, score=0, chain=[], idx=0, time=0.0, total=1.0,
                         msg="", msg_color="#000000", over=False, new_best=False,
                         combo=0, best_combo=0, correct=0, mistakes=0, phase="intro",
                         bad_key=None, token=0, gave_up=False)
        self.next_round()

    def next_round(self):
        g = self.game
        g["round"] += 1
        length = min(2 + g["round"], 8)
        g["chain"] = self.new_chain(length)
        g["idx"] = 0
        g["time"] = g["total"] = self.round_time(length)
        g["phase"] = "intro"            # "Round 2... get ready" (the clock waits)
        g["token"] += 1
        tok = g["token"]
        self.draw_panel()

        def go():
            if self.game is g and g["token"] == tok and not g["over"]:
                g["phase"] = "play"
                self.draw_panel()
        self.root.after(1700, go)

    def multiplier(self):
        return 1 + self.game["combo"] // 3      # x2 after 3 in a row, x3 after 6...

    def game_tick(self):
        """Counts the clock down 10 times a second (paused while an error is flashing,
        during the round intro, or when you're on another tab)."""
        g = self.game
        if (g and not g["over"] and g["phase"] == "play" and not self.busy
                and self.tab == "game"):
            g["time"] -= 0.1
            if g["time"] <= 0:
                g["time"] = 0
                self.game_over()
            else:
                self.update_timer()
        self.root.after(100, self.game_tick)

    @staticmethod
    def fmt_time(t):
        return "%d:%04.1f" % (int(t) // 60, t % 60)

    def update_timer(self):
        g = self.game
        try:
            low = g["time"] < 5
            self.cv.itemconfigure("gtimer", text=self.fmt_time(g["time"]),
                                  fill="#C62828" if low else "#1E3287")
            x1, y1, x2, y2 = self.gbar_box
            frac = max(0.0, min(1.0, g["time"] / g["total"]))
            fx = x1 + 1 + int((x2 - x1 - 2) * frac)
            mid = (y1 + y2) // 2
            self.cv.coords("gbar_top", x1 + 1, y1 + 1, fx, mid)
            self.cv.coords("gbar_bot", x1 + 1, mid, fx, y2 - 1)
            red = frac < 0.3
            self.cv.itemconfigure("gbar_top", fill="#F28B82" if red else "#6CE16F")
            self.cv.itemconfigure("gbar_bot", fill="#D93025" if red else "#06B025")
        except Exception:
            pass

    def game_over(self, gave_up=False):
        g = self.game
        g["over"] = True
        g["gave_up"] = gave_up
        name = self.diff[0]
        if g["score"] > self.best.get(name, 0):
            self.best[name] = g["score"]
            g["new_best"] = True
            self.save_best()
        self.draw_panel()

    def game_pick(self, key):
        g = self.game
        if not g or g["over"] or self.busy or g["phase"] != "play":
            return
        if key == g["chain"][g["idx"]]:
            g["combo"] += 1
            g["best_combo"] = max(g["best_combo"], g["combo"])
            g["correct"] += 1
            g["score"] += 10 * g["round"] * self.multiplier()
            g["idx"] += 1
            g["msg"] = ""
            g["bad_key"] = None
            self.flash(key, self.after_flash)
        else:
            g["combo"] = 0
            g["mistakes"] += 1
            g["time"] = max(0.0, g["time"] - 3)
            g["msg"] = "Wrong! That was %s.  -3 seconds" % GAME_NAME[key]
            g["msg_color"] = "#C62828"
            g["bad_key"] = key
            if g["time"] <= 0:
                self.game_over()
            else:
                self.draw_panel()
                self.shake_panel()

    def shake_panel(self):
        for i, dx in enumerate((7, -14, 12, -10, 7, -2)):
            self.root.after(i * 35, lambda dx=dx: self.cv.move("panel", dx, 0))
        self.root.after(6 * 35 + 20, lambda: None if self.busy else self.draw_panel())

    def after_flash(self):
        g = self.game
        if not g:
            return
        if g["idx"] >= len(g["chain"]):
            bonus = int(g["time"]) * 5
            g["score"] += bonus
            g["msg"] = "List complete!  +%d time bonus" % bonus
            g["msg_color"] = "#2E7D32"
            self.next_round()
        else:
            self.draw_panel()

    def give_up(self):
        if self.game and not self.game["over"]:
            self.game_over(gave_up=True)

    # a quick 1.3 second glimpse of an error's main screen
    def flash(self, key, then):
        self.busy = True
        self.hover = None
        self.cv.itemconfigure("panel", state="hidden")
        self.force_focus()
        code = self.pick_code()
        bl = lambda: self.console_black()

        def black_then(fn):
            return lambda: (bl(), fn())
        shows = {
            "bsod": lambda: self.draw_bsod(code),
            "black": lambda: self.draw_blackscreen(code),
            "green": lambda: self.draw_bsod(code, bg=GSOD_GREEN, who="Your Windows Insider Build"),
            "mac": black_then(self.mac_old_box),
            "linux": lambda: self.linux_new(random.choice(self.LINUX_PANICS)[0]),
            "noboot": black_then(lambda: (self.nb_setup("#AAAAAA"), self.nb_lines.extend(
                ["Reboot and Select proper Boot device",
                 "or Insert Boot Media in selected Boot device and press a key"]),
                self.nb_show())),
            "corrupt": self.corrupt_screen,
            "nocmd": self.nocmd_screen,
            "iphone": self.iphone_screen,
            "download": self.download_screen,
            "bootloop": lambda: (setattr(self, "bl_round", 0), self.bootloop_warning()),
            "ce34878": black_then(self.ce_dialog),
            "notoff": self.notoff_screen,
            "safemode": lambda: (setattr(self, "safe_sel", 0), setattr(self, "safe_mode", "menu"),
                                 self.safe_draw()),
            "su30746": lambda: (setattr(self, "su_tries", 0), self.su_screen()),
            "bluelight": black_then(self.bluelight_start),
            "xboxerr": lambda: (setattr(self, "xbox_code", "E102  00000000  80070002"),
                                self.xbox_screen()),
            "switcherr": black_then(self.switch_dialog),
        }
        try:
            shows[key]()
        except Exception:
            pass
        self.flash_toast()
        self.root.after(1300, lambda: (self.flash_end(), then()))

    def flash_toast(self):
        """A small Windows 7 style tooltip on the flash: how far along the list you are."""
        g = self.game
        if not g:
            return
        cv = self.cv
        text = "✓  %d of %d" % (g["idx"], len(g["chain"]))
        if self.multiplier() > 1:
            text += "     Combo x%d" % self.multiplier()
        f = tkfont.Font(family="Segoe UI", size=-14)
        w, h = f.measure(text) + 28, 30
        x1, y1 = (self.W - w) // 2, 24
        vgrad(cv, x1, y1, x1 + w, y1 + h, "#FFFFFF", "#E4E5F0", tags=("fx",))
        cv.create_rectangle(x1, y1, x1 + w, y1 + h, outline="#767676", tags="fx")
        cv.create_text(x1 + w // 2, y1 + h // 2, text=text, font=f, fill="#1E7B1E", tags="fx")

    def flash_end(self):
        self.cancel_jobs()
        self.cv.delete("fx")
        self.cv.config(cursor="")
        self._img = None
        self.any_key = None
        self.key_handler = None
        self.percent_item = None
        self.busy = False

    def chip_flow(self, items, pl, pr, y):
        """Draws the list of errors to trigger as chips that wrap onto new lines."""
        cv, T = self.cv, "panel"
        g = self.game
        f_norm = tkfont.Font(family="Segoe UI", size=-12)
        f_bold = tkfont.Font(family="Segoe UI", size=-12, weight="bold")
        x, h, gap = pl, 22, 6
        for i, key in enumerate(items):
            done, nxt = i < g["idx"], i == g["idx"]
            label = ("✓ " if done else "%d. " % (i + 1)) + GAME_NAME[key]
            font = f_bold if nxt else f_norm
            w = font.measure(label) + 16
            if x + w > pr and x > pl:
                x = pl
                y += h + 5
            if done:
                vgrad(cv, x, y, x + w, y + h, "#EDF8ED", "#D2EDD2")
                edge, color = "#8CC98C", "#2E7D32"
            elif nxt:
                vgrad(cv, x, y, x + w, y + h, "#F2FAFE", "#CFE9FA")
                edge, color = "#3C7FB1", "#0B3D66"
            else:
                vgrad(cv, x, y, x + w, y + h, "#FAFAFA", "#ECECEC")
                edge, color = "#C9C9C9", "#666666"
            cv.create_rectangle(x, y, x + w, y + h, outline=edge, width=2 if nxt else 1, tags=T)
            cv.create_text(x + w // 2, y + h // 2, text=label, font=font, fill=color, tags=T)
            x += w + gap
        return y + h

    def link(self, sid, x, y, text, cb, anchor="e"):
        """A blue Windows 7 style text link."""
        hov = self.hover == sid
        f = ("Segoe UI", -12, "underline") if hov else ("Segoe UI", -12)
        t = self.cv.create_text(x, y, text=text, font=f, fill="#0066CC" if not hov else "#3399FF",
                                anchor=anchor, tags="panel")
        bx = self.cv.bbox(t)
        self.spot(sid, bx[0] - 2, bx[1] - 2, bx[2] + 2, bx[3] + 2, cb)

    def win7_bar(self, x1, y1, x2, y2, frac, red=False):
        """A Windows 7 progress bar (glossy green, red when time is almost up)."""
        cv, T = self.cv, "panel"
        vgrad(cv, x1, y1, x2, y2, "#F3F3F3", "#DADADA")
        cv.create_rectangle(x1, y1, x2, y2, outline="#BCBCBC", tags=T)
        fx = x1 + 1 + int((x2 - x1 - 2) * max(0.0, min(1.0, frac)))
        mid = (y1 + y2) // 2
        cv.create_rectangle(x1 + 1, y1 + 1, fx, mid, outline="",
                            fill="#F28B82" if red else "#6CE16F", tags=(T, "gbar_top"))
        cv.create_rectangle(x1 + 1, mid, fx, y2 - 1, outline="",
                            fill="#D93025" if red else "#06B025", tags=(T, "gbar_bot"))
        self.gbar_box = (x1, y1, x2, y2)

    def draw_game(self, pl, pr, pt, page_bot):
        cv, T = self.cv, "panel"
        g = self.game
        mid = (pl + pr) // 2
        name = self.diff[0]
        if g is None:                                   # intro screen
            cv.create_text(pl, pt, text="Combo Challenge", font=("Segoe UI", -16),
                           fill="#1E3287", anchor="nw", tags=T)
            cv.create_text(pl, pt + 24, text="How fast can you crash everything?",
                           font=("Segoe UI", -12), fill="#5A5A5A", anchor="nw", tags=T)
            rules = [("List", "You get a list of errors, like  Mac Panic → Blue Screen."),
                     ("Click", "Click them in order on the error board."),
                     ("Flash", "Each right pick flashes on your screen for a second."),
                     ("Combo", "Picks in a row without a mistake multiply your points."),
                     ("Careful", "A wrong click costs 3 seconds and breaks your combo."),
                     ("Bonus", "Finish the list for a time bonus. Then it gets longer!")]
            y = pt + 58
            for tag, line in rules:
                vgrad(cv, pl, y, pl + 62, y + 20, "#F2FAFE", "#D7ECFA")
                cv.create_rectangle(pl, y, pl + 62, y + 20, outline="#9ACFEF", tags=T)
                cv.create_text(pl + 31, y + 10, text=tag, font=("Segoe UI", -11, "bold"),
                               fill="#1E3287", tags=T)
                cv.create_text(pl + 72, y + 10, text=line, font=("Segoe UI", -12),
                               fill="#333333", anchor="w", tags=T)
                y += 28
            y += 12
            cv.create_line(pl, y, pr, y, fill="#E3E3E3", tags=T)
            y += 18
            cv.create_text(pl, y + 11, text="Difficulty:", font=("Segoe UI", -12),
                           fill="#000000", anchor="w", tags=T)
            self.combo("gdiff", pl + 90, y, pl + 210, y + 22, name, self.next_diff)
            _, base, per = self.diff
            cv.create_text(pl + 222, y + 11, text="%g s + %g s per error" % (base, per),
                           font=("Segoe UI", -11), fill="#8C8C8C", anchor="w", tags=T)
            y += 34
            cv.create_text(pl, y + 11, text="Best score:", font=("Segoe UI", -12),
                           fill="#000000", anchor="w", tags=T)
            cv.create_text(pl + 90, y + 11, text="%d" % self.best.get(name, 0),
                           font=("Segoe UI", -14, "bold"), fill="#1E3287", anchor="w", tags=T)
            y += 46
            self.w7button("gstart", mid - 80, y, mid + 80, y + 32, "Start Game", self.start_game)
            return
        if g["over"]:                                   # game over screen
            title = "You gave up!" if g["gave_up"] else "Time's up!"
            cv.create_text(mid, pt + 22, text=title, font=("Segoe UI", -22),
                           fill="#C62828", tags=T)
            cv.create_text(mid, pt + 62, text="%d" % g["score"], font=("Segoe UI", -34),
                           fill="#1E3287", tags=T)
            cv.create_text(mid, pt + 90, text="points  ·  %s" % name,
                           font=("Segoe UI", -12), fill="#5A5A5A", tags=T)
            if g["new_best"]:
                cv.create_text(mid, pt + 118, text="★  New best score!  ★",
                               font=("Segoe UI", -15, "bold"), fill="#E08A00", tags=T)
            else:
                cv.create_text(mid, pt + 118, text="Best score: %d" % self.best.get(name, 0),
                               font=("Segoe UI", -13), fill="#5A5A5A", tags=T)
            # stats box
            total = g["correct"] + g["mistakes"]
            acc = (100 * g["correct"] // total) if total else 0
            stats = [("Round reached", "%d" % g["round"]),
                     ("Correct picks", "%d" % g["correct"]),
                     ("Mistakes", "%d" % g["mistakes"]),
                     ("Accuracy", "%d%%" % acc),
                     ("Best combo", "%d in a row" % g["best_combo"])]
            bx1, bx2, by = mid - 140, mid + 140, pt + 142
            cv.create_rectangle(bx1, by, bx2, by + 22 * len(stats) + 14, fill="#F7F9FC",
                                outline="#D5DFEA", tags=T)
            for i, (k, v) in enumerate(stats):
                yy = by + 18 + i * 22
                cv.create_text(bx1 + 16, yy, text=k, font=("Segoe UI", -12),
                               fill="#5A5A5A", anchor="w", tags=T)
                cv.create_text(bx2 - 16, yy, text=v, font=("Segoe UI", -12, "bold"),
                               fill="#000000", anchor="e", tags=T)
            yb = by + 22 * len(stats) + 34
            self.w7button("gagain", mid - 150, yb, mid - 10, yb + 30, "Play Again",
                          self.start_game)
            self.w7button("gback", mid + 10, yb, mid + 150, yb + 30, "Back",
                          lambda: (setattr(self, "game", None), self.draw_panel()))
            return

        # ----- in a round -----
        cv.create_text(pl, pt, text="Round %d" % g["round"], font=("Segoe UI", -16),
                       fill="#1E3287", anchor="nw", tags=T)
        cv.create_text(pl + 84, pt + 3, text="Score: %d" % g["score"], font=("Segoe UI", -13),
                       fill="#333333", anchor="nw", tags=T)
        if self.multiplier() > 1:
            cv.create_text(pl + 190, pt + 3, text="Combo x%d" % self.multiplier(),
                           font=("Segoe UI", -13, "bold"), fill="#E08A00", anchor="nw", tags=T)
        cv.create_text(pr, pt - 1, text=self.fmt_time(g["time"]), font=("Consolas", -20),
                       fill="#C62828" if g["time"] < 5 else "#1E3287", anchor="ne",
                       tags=(T, "gtimer"))
        frac = g["time"] / g["total"] if g["total"] else 0
        self.win7_bar(pl, pt + 26, pr, pt + 38, frac, red=frac < 0.3)

        if g["phase"] == "intro":                       # "Round 2 ... get ready"
            cv.create_text(mid, pt + 120, text="Round %d" % g["round"],
                           font=("Segoe UI", -30), fill="#1E3287", tags=T)
            cv.create_text(mid, pt + 158, text="%d errors  ·  %.0f seconds" %
                           (len(g["chain"]), g["total"]), font=("Segoe UI", -14),
                           fill="#5A5A5A", tags=T)
            if g["msg"]:
                cv.create_text(mid, pt + 70, text=g["msg"], font=("Segoe UI", -13),
                               fill=g["msg_color"], tags=T)
            cv.create_text(mid, pt + 200, text="Get ready...", font=("Segoe UI", -14, "italic"),
                           fill="#8C8C8C", tags=T)
            return

        cv.create_text(pl, pt + 52, text="Trigger these errors, in order:",
                       font=("Segoe UI", -12), fill="#5A5A5A", anchor="w", tags=T)
        self.link("ggiveup", pr, pt + 52, "Give up", self.give_up)
        y = self.chip_flow(g["chain"], pl, pr, pt + 64)
        if g["msg"]:
            cv.create_text(pl, y + 12, text=g["msg"], font=("Segoe UI", -12),
                           fill=g["msg_color"], anchor="w", tags=T)
        # the error board, grouped by kind
        y = max(y + 26, pt + 150)
        cols, bh, gap = 3, 23, 3
        bw = (pr - pl - gap * (cols - 1)) // cols
        for group, keys in BOARD_GROUPS:
            cv.create_text(pl, y + 7, text=group, font=("Segoe UI", -11, "bold"),
                           fill="#1E3287", anchor="w", tags=T)
            cv.create_line(pl + 52, y + 7, pr, y + 7, fill="#D5DFEA", tags=T)
            y += 15
            for i, key in enumerate(keys):
                r, c = divmod(i, cols)
                x1 = pl + c * (bw + gap)
                y1 = y + r * (bh + gap)
                if g["bad_key"] == key:             # the button you just got wrong
                    vgrad(cv, x1 + 1, y1 + 1, x1 + bw, y1 + bh, "#FDECEA", "#F6C1BC")
                    cv.create_rectangle(x1, y1, x1 + bw, y1 + bh, outline="#C62828", tags=T)
                    cv.create_text(x1 + bw // 2, y1 + bh // 2, text=GAME_NAME[key],
                                   font=("Segoe UI", -12), fill="#8E1C1C", tags=T)
                    self.spot("g_" + key, x1, y1, x1 + bw + 1, y1 + bh + 1,
                              lambda k=key: self.game_pick(k))
                else:
                    self.w7button("g_" + key, x1, y1, x1 + bw, y1 + bh, GAME_NAME[key],
                                  lambda k=key: self.game_pick(k))
            y += ((len(keys) + cols - 1) // cols) * (bh + gap) + 4

    # ----- maximized layout (like a Windows 7 Control Panel window) ---------
    TAB_INFO = {
        "sandbox": ("PC Errors", "Crash screens from Windows, Mac and Linux.", EVENTS),
        "phone": ("Phone Errors", "Your monitor turns into a crashed phone.", PHONE_EVENTS),
        "console": ("Console Errors", "PlayStation, Xbox and Switch error screens.",
                    CONSOLE_EVENTS),
        "game": ("Game Mode", "Combo Challenge: how fast can you crash everything?", None),
    }

    def run_random(self):
        events = self.TAB_INFO[self.tab][2] or (EVENTS + PHONE_EVENTS + CONSOLE_EVENTS)
        keys = [e["key"] for e in events if e["ready"]]
        if keys and not self.busy and not (self.game and not self.game["over"]):
            self.start_event(random.choice(keys))

    def draw_max_layout(self, cx, cy, cx2, cy2):
        cv, T = self.cv, "panel"
        title, subtitle, _ = self.TAB_INFO[self.tab]

        # address bar strip
        ay2 = cy + 36
        vgrad(cv, cx, cy, cx2, ay2, "#DCE8F7", "#C7D9F0")
        cv.create_line(cx, ay2, cx2, ay2, fill="#A0B6D2", tags=T)
        ax1, ax2 = cx + 12, cx2 - 12
        cv.create_rectangle(ax1, cy + 7, ax2, ay2 - 7, fill="#FFFFFF", outline="#8DA2BE", tags=T)
        cv.create_rectangle(ax1 + 6, cy + 11, ax1 + 20, ay2 - 11, fill="#2B7BD3",
                            outline="#0E3F75", tags=T)
        f = tkfont.Font(family="Segoe UI", size=-12)
        x = ax1 + 30
        for i, part in enumerate(["Crash Simulator", title]):
            if i:
                cv.create_text(x, (cy + ay2) // 2, text="\u25b8", font=("Segoe UI", -11),
                               fill="#6A6A6A", anchor="w", tags=T)
                x += 16
            cv.create_text(x, (cy + ay2) // 2, text=part, font=f, fill="#000000",
                           anchor="w", tags=T)
            x += f.measure(part) + 8

        # command bar
        by2 = ay2 + 30
        vgrad(cv, cx, ay2 + 1, cx2, by2, "#F5F9FD", "#DCE6F4")
        cv.create_line(cx, by2, cx2, by2, fill="#A9BCD6", tags=T)
        playing = self.game and not self.game["over"]
        if not playing:
            label = "Run a random error"
            hov = self.hover == "cmd_random"
            tw = f.measure(label) + 26
            bx1, byy = cx + 12, ay2 + 4
            if hov:
                vgrad(cv, bx1, byy, bx1 + tw, by2 - 4, "#FCFDFE", "#D9E9F9")
                cv.create_rectangle(bx1, byy, bx1 + tw, by2 - 4, outline="#8DB2E3", tags=T)
            cv.create_polygon(bx1 + 8, byy + 7, bx1 + 8, by2 - 11, bx1 + 15, (byy + by2 - 4) // 2,
                              fill="#2E8B2E", outline="", tags=T)
            cv.create_text(bx1 + 20, (byy + by2 - 4) // 2, text=label, font=f, fill="#1E3287",
                           anchor="w", tags=T)
            self.spot("cmd_random", bx1, byy, bx1 + tw, by2 - 4, self.run_random)

        # status bar at the bottom
        sy1 = cy2 - 22
        vgrad(cv, cx + 1, sy1, cx2, cy2, "#F4F7FC", "#DFE7F2")
        cv.create_line(cx + 1, sy1, cx2, sy1, fill="#C3CCD9", tags=T)
        cv.create_text(cx + 10, cy2 - 11, text="Ctrl+Shift+Q stops an effect",
                       font=("Segoe UI", -11), fill="#333333", anchor="w", tags=T)
        cv.create_text(cx2 - 10, cy2 - 11, text="Double-click the title bar to restore",
                       font=("Segoe UI", -11), fill="#6A6A6A", anchor="e", tags=T)

        # side pane
        sw = 240
        vgrad(cv, cx, by2 + 1, cx + sw, sy1, "#EEF4FC", "#D6E3F4")
        cv.create_line(cx + sw, by2 + 1, cx + sw, sy1, fill="#B7C9E2", tags=T)
        y = by2 + 22
        cv.create_text(cx + 20, y, text="Crash Simulator", font=("Segoe UI", -13, "bold"),
                       fill="#1E3287", anchor="w", tags=T)
        y += 28
        counts = {"sandbox": len(EVENTS), "phone": len(PHONE_EVENTS),
                  "console": len(CONSOLE_EVENTS)}
        for tid in ("sandbox", "phone", "console", "game"):
            name = self.TAB_INFO[tid][0]
            if tid in counts:
                name += "  (%d)" % counts[tid]
            sel = self.tab == tid
            hov = self.hover == "side_" + tid
            if sel:
                vgrad(cv, cx + 10, y - 12, cx + sw - 10, y + 12, "#FFFFFF", "#E5F0FB")
                cv.create_rectangle(cx + 10, y - 12, cx + sw - 10, y + 12, outline="#A9C6EA",
                                    tags=T)
            cv.create_text(cx + 24, y, text=name,
                           font=("Segoe UI", -13, "bold") if sel else
                           ("Segoe UI", -13, "underline") if hov else ("Segoe UI", -13),
                           fill="#000000" if sel else ("#3399FF" if hov else "#0066CC"),
                           anchor="w", tags=T)
            self.spot("side_" + tid, cx + 10, y - 12, cx + sw - 10, y + 12,
                      lambda t=tid: self.set_tab(t))
            y += 30
        # current settings, like the "See also" area of Control Panel
        y += 14
        cv.create_line(cx + 20, y, cx + sw - 20, y, fill="#B7C9E2", tags=T)
        y += 18
        cv.create_text(cx + 20, y, text="Current settings", font=("Segoe UI", -12, "bold"),
                       fill="#1E3287", anchor="w", tags=T)
        y += 24
        best = self.best.get(self.diff[0], 0) if isinstance(self.best, dict) else self.best
        info = [("Start after", DELAYS[self.delay_i][1]),
                ("Style", STYLES[self.style_i].split(" (")[0]),
                ("Phone display", PHONE_DISPLAYS[self.phone_disp_i]),
                ("Game difficulty", self.diff[0]),
                ("Best score", str(best))]
        for k, v in info:
            cv.create_text(cx + 20, y, text=k, font=("Segoe UI", -12), fill="#4A4A4A",
                           anchor="w", tags=T)
            cv.create_text(cx + sw - 20, y, text=v, font=("Segoe UI", -12), fill="#000000",
                           anchor="e", tags=T)
            y += 22
        cv.create_text(cx + 20, sy1 - 20, text="Nothing on your PC is ever changed.",
                       font=("Segoe UI", -11), fill="#5A5A5A", anchor="w", tags=T)

        # main area (white, like Control Panel)
        mx1 = cx + sw + 1
        cv.create_rectangle(mx1, by2 + 1, cx2, sy1 - 1, fill="#FFFFFF", outline="", tags=T)
        left = mx1 + 40
        cv.create_text(left, by2 + 36, text=title, font=("Segoe UI", -24), fill="#1E3287",
                       anchor="w", tags=T)
        cv.create_text(left, by2 + 66, text=subtitle, font=("Segoe UI", -13), fill="#5A5A5A",
                       anchor="w", tags=T)
        cv.create_line(left, by2 + 86, min(cx2 - 40, left + 760), by2 + 86, fill="#E3E3E3",
                       tags=T)
        pl, pr, pt = left, min(cx2 - 40, left + 640), by2 + 104
        if self.tab == "sandbox":
            self.draw_sandbox(pl, pr, pt)
        elif self.tab == "phone":
            self.draw_phones(pl, pr, pt)
        elif self.tab == "console":
            self.draw_consoles(pl, pr, pt)
        else:
            self.draw_game(pl, pr, pt, sy1 - 10)

    # ----- window buttons ---------------------------------------------------
    def toggle_max(self):
        if self.maximized:
            self.maximized = False
            self.px, self.py = self.saved_pos
        else:
            self.saved_pos = (self.px, self.py)
            self.maximized = True
        self.hover = None
        self.draw_panel()

    def on_double(self, e):
        if self.busy:
            return
        w = self.W if self.maximized else PW
        on_title = self.px <= e.x < self.px + w and self.py <= e.y < self.py + 30
        if on_title and not self.spot_at(e.x, e.y):
            self.drag = None
            self.toggle_max()

    def minimize(self):
        """Minimize to the Windows taskbar, like a real window."""
        self.hover = None
        self.draw_panel()
        try:
            self.root.iconify()
        except Exception:
            pass

    def on_restore(self, e=None):
        """Coming back from the taskbar: make sure we're full screen and on top again."""
        if e is not None and e.widget is not self.root:
            return

        def again():
            try:
                self.root.attributes("-fullscreen", True)
                self.root.attributes("-topmost", True)
                if IS_WIN:
                    self.root.attributes("-transparentcolor", KEY)
            except Exception:
                pass
            self.force_focus()
        self.root.after(60, again)

    def set_tab(self, t):
        self.tab = t
        self.draw_panel()

    def next_delay(self):
        self.delay_i = (self.delay_i + 1) % len(DELAYS)
        self.draw_panel()

    def next_style(self):
        self.style_i = (self.style_i + 1) % len(STYLES)
        self.draw_panel()

    def next_code(self):
        self.code_i = (self.code_i + 1) % (len(STOP_CODES) + 1)
        self.draw_panel()

    def pick_code(self):
        return random.choice(STOP_CODES) if self.code_i == 0 else STOP_CODES[self.code_i - 1]

    # ----- effects -----------------------------------------------------------
    def start_event(self, key):
        if self.busy:
            return
        self.busy = True
        self.hover = None
        self.cv.itemconfigure("panel", state="hidden")
        fn = {"bsod": self.fx_bsod, "black": self.fx_black, "green": self.fx_green,
              "mac": self.fx_mac, "linux": self.fx_linux,
              "noboot": self.fx_noboot,
              "corrupt": self.fx_corrupt,
              "nocmd": self.fx_nocmd, "iphone": self.fx_iphone,
              "download": self.fx_download, "bootloop": self.fx_bootloop,
              "ce34878": self.fx_ce34878, "notoff": self.fx_notoff,
              "safemode": self.fx_safemode, "su30746": self.fx_su30746,
              "bluelight": self.fx_bluelight, "xboxerr": self.fx_xbox,
              "switcherr": self.fx_switch}[key]
        self.later(DELAYS[self.delay_i][0] * 1000 + 200, fn)

    def end_effect(self):
        self.cancel_jobs()
        self.cv.delete("fx")
        self.cv.config(cursor="")
        self._img = None
        self._frames = []
        self.any_key = None
        self.key_handler = None
        self.percent_item = None
        self._pil = None
        self._dim = None
        self.mute.restore()        # sound comes back when the panel does
        self.busy = False
        self.draw_panel()
        self.force_focus()

    def on_stop_key(self, e=None):
        if self.busy:
            self.end_effect()
        else:
            self.quit()

    # Shared crash start: freeze the screen, then show the crash screen ------
    def fx_crash(self, draw):
        self.force_focus()
        code = self.pick_code()
        self.freeze()
        self.later(self.FREEZE_MS, lambda: draw(code))

    def run_progress(self):
        """The % counter: sits at 0 for a bit, jumps unevenly to 100, then restarts."""
        t = random.randint(2200, 3500)
        pct = 0
        while pct < 100:
            pct = min(100, pct + random.choice([1, 2, 4, 7, 10, 13, 17, 21, 25]))
            self.later(t, lambda p=pct: self.set_pct(p))
            t += random.randint(500, 2300)
        self.later(t + 1800, self.fx_restart)

    # Blue Screen of Death ----------------------------------------------------
    def fx_bsod(self):
        self.fx_crash(self.draw_old_bsod if self.style_i == 1 else self.draw_bsod)

    # Old Blue Screen of Death (Windows XP / 7) -------------------------------
    def draw_old_bsod(self, code):
        cv = self.cv
        cv.delete("fx")
        cv.config(cursor="none")
        self.force_focus()
        W, H = self.W, self.H
        size = max(10, int(H / 31))
        cv.create_rectangle(0, 0, W, H, fill=OLD_BLUE, outline=OLD_BLUE, tags="fx")

        num = STOP_HEX.get(code, 0x7E)
        params = ",".join("0x%08X" % p for p in (
            random.choice([0, 0xFFFFFFFFC0000005, 0x80000003]) & 0xFFFFFFFF,
            random.randint(0, 0xFFFFFFFF),
            random.choice([0, 1, 2, 8]),
            random.randint(0x80000000, 0x8FFFFFFF)))
        lines = ["A problem has been detected and Windows has been shut down to prevent damage",
                 "to your computer.", ""]
        if code in WHAT_FAILED:
            lines += ["The problem seems to be caused by the following file: "
                      + WHAT_FAILED[code].upper(), ""]
        lines += [code, "",
                  "If this is the first time you've seen this Stop error screen,",
                  "restart your computer. If this screen appears again, follow",
                  "these steps:", "",
                  "Check to make sure any new hardware or software is properly installed.",
                  "If this is a new installation, ask your hardware or software manufacturer",
                  "for any Windows updates you might need.", "",
                  "If problems continue, disable or remove any newly installed hardware",
                  "or software. Disable BIOS memory options such as caching or shadowing.",
                  "If you need to use Safe Mode to remove or disable components, restart",
                  "your computer, press F8 to select Advanced Startup Options, and then",
                  "select Safe Mode.", "",
                  "Technical information:", "",
                  "*** STOP: 0x%08X (%s)" % (num, params), "", ""]
        if code in WHAT_FAILED:
            base = random.randint(0x88000000, 0x8FFF0000) & 0xFFFF0000
            lines[-1:] = ["***  %s - Address %08X base at %08X, DateStamp %08x"
                            % (WHAT_FAILED[code].upper(), base + random.randint(0x1000, 0xFFFF),
                               base, random.randint(0x40000000, 0x4FFFFFFF)), ""]
        self.old_lines = lines
        family = "Lucida Console" if IS_WIN else "Courier"
        # shrink the font until everything (plus the dump lines added later) fits on screen
        sample = "\n".join(lines + ["Contact your system administrator or technical support "
                                    "group for further"] * 7)
        x0, y0 = int(W * 0.012), int(H * 0.012)
        probe = cv.create_text(x0, y0, text=sample, font=(family, -size), anchor="nw", tags="fx")
        while size > 8:
            bx = cv.bbox(probe)
            if bx[3] <= H - y0 and bx[2] <= W - x0:
                break
            size -= 1
            cv.itemconfigure(probe, font=(family, -size))
        cv.delete(probe)
        self.old_item = cv.create_text(x0, y0, text="\n".join(lines),
                                       font=(family, -size), fill="#FFFFFF",
                                       anchor="nw", tags="fx")

        # the memory dump lines appear at the bottom, one after another
        t = 1500
        self.later(t, lambda: self.old_add("Collecting data for crash dump ..."))
        t += random.randint(900, 1600)
        self.later(t, lambda: self.old_add("Initializing disk for crash dump ..."))
        t += random.randint(900, 1600)
        self.later(t, lambda: self.old_add("Beginning dump of physical memory."))
        t += random.randint(600, 1000)
        self.later(t, lambda: self.old_add("Dumping physical memory to disk:  0"))
        pct = 0
        while pct < 100:
            pct = min(100, pct + random.choice([5, 5, 10, 10, 15, 20]))
            t += random.randint(250, 900)
            self.later(t, lambda p=pct: self.old_set_last("Dumping physical memory to disk:  %d" % p))
        t += 700
        self.later(t, lambda: self.old_add("Physical memory dump complete."))
        t += 300
        self.later(t, lambda: self.old_add("Contact your system administrator or technical "
                                           "support group for further"))
        self.later(t + 1, lambda: self.old_add("assistance."))
        self.later(t + 3500, self.fx_restart)

    def old_add(self, line):
        self.old_lines.append(line)
        self.cv.itemconfigure(self.old_item, text="\n".join(self.old_lines))

    def old_set_last(self, line):
        self.old_lines[-1] = line
        self.cv.itemconfigure(self.old_item, text="\n".join(self.old_lines))

    # Black Screen of Death (Windows 11, 2025) --------------------------------
    def fx_black(self):
        self.fx_crash(self.draw_blackscreen)

    # Mac Kernel Panic -------------------------------------------------------
    MAC_OLD_TEXT = [
        "You need to restart your computer. Hold down the Power button for several seconds "
        "or press the Restart button.",
        "Veuillez redémarrer votre ordinateur. Maintenez la touche de démarrage enfoncée "
        "pendant plusieurs secondes ou bien appuyez sur le bouton de réinitialisation.",
        "Sie müssen Ihren Computer neu starten. Halten Sie dazu die Einschalttaste einige "
        "Sekunden gedrückt oder drücken Sie die Neustart-Taste.",
        "コンピュータを再起動する必要があります。パワーボタンを数秒間押し続けるか、"
        "リセットボタンを押してください。",
    ]
    MAC_NEW_TEXT = [
        "Your computer restarted because of a problem. Press a key or wait a few seconds "
        "to continue starting up.",
        "Votre ordinateur a redémarré en raison d'un problème. Pour poursuivre le "
        "redémarrage, appuyez sur une touche ou patientez quelques secondes.",
        "Ihr Computer wurde aufgrund eines Problems neu gestartet. Drücken Sie zum "
        "Fortfahren eine Taste oder warten Sie einige Sekunden.",
        "問題が起きたためコンピュータを再起動しました。このまま起動する場合は、"
        "いずれかのキーを押すか、数秒間そのままお待ちください。",
        "因出现问题而重新启动了电脑。请按一下按键，或等几秒钟以继续启动。",
    ]

    def fx_mac(self):
        self.force_focus()
        if self.style_i == 1:
            self.mac_old()
        else:
            self.mac_new()

    # new style: the Mac instantly reboots, then explains why
    def mac_new(self):
        self.freeze()
        self.later(self.FREEZE_MS, self.mac_new_black)

    def mac_new_black(self):
        cv = self.cv
        cv.delete("fx")
        self._img = None
        cv.create_rectangle(0, 0, self.W, self.H, fill="#000000", outline="#000000", tags="fx")
        cv.config(cursor="none")
        self.later(2800, self.mac_new_msg)

    def mac_new_msg(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        width = min(int(W * 0.6), int(860 * s))
        y = 0
        items = []
        for para in self.MAC_NEW_TEXT:
            t = cv.create_text(W // 2, y, text=para, font=("Segoe UI", -int(19 * s)),
                               fill="#D6D6D6", width=width, justify="center", anchor="n",
                               tags="fx")
            items.append(t)
            y = cv.bbox(t)[3] + int(22 * s)
        top = (H - y) // 2       # center the whole block
        for t in items:
            cv.move(t, 0, top)
        self.any_key = self.fx_restart          # any key continues "starting up"
        self.later(12000, self.fx_restart)

    # old style: gray curtain slides down over the frozen screen, then the box
    def mac_old(self):
        cv = self.cv
        W, H = self.W, self.H
        cv.config(cursor="none")
        self.mute.mute()
        pil = self.grab_pil()
        steps = 16
        start = self.FREEZE_MS
        self._frames = []
        if pil is not None:
            try:
                from PIL import Image, ImageTk
                dark = Image.blend(pil, Image.new("RGB", pil.size, (0, 0, 0)), 0.6)
                self._frames.append(ImageTk.PhotoImage(dark))
                cv.create_image(0, 0, image=self._frames[0], anchor="nw", tags="fx")
                top = cv.create_image(0, 0, image=None, anchor="nw", tags="fx")
                self._img = ImageTk.PhotoImage(pil)
                cv.itemconfigure(top, image=self._img)

                def step(k):
                    h = int(H * k / steps)
                    if h >= H:
                        cv.delete(top)
                    else:
                        frame = ImageTk.PhotoImage(pil.crop((0, h, W, H)))
                        self._frames[1:] = [frame]
                        cv.itemconfigure(top, image=frame)
                        cv.coords(top, 0, h)
                for k in range(1, steps + 1):
                    self.later(start + k * 70, lambda k=k: step(k))
            except Exception:
                pil = None
        if pil is None:
            # no Pillow: freeze with the built-in screenshot, then a dotted dark curtain
            img = self.grab_screen()
            if img is not None:
                self._img = img
                cv.create_image(0, 0, image=img, anchor="nw", tags="fx")
            cur = cv.create_rectangle(0, 0, W, 0, fill="#000000", outline="",
                                      stipple="gray50", tags="fx")
            for k in range(1, steps + 1):
                self.later(start + k * 70,
                           lambda k=k: cv.coords(cur, 0, 0, W, int(H * k / steps)))
        self.later(start + steps * 70 + 250, self.mac_old_box)

    def mac_old_box(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        bw = int(min(W * 0.42, 640 * s))
        pad = int(34 * s)
        x1 = (W - bw) // 2
        # lay out contents first, then size the box around them
        icon_r = int(34 * s)
        y = icon_r * 2 + int(30 * s)
        items = []
        for para in self.MAC_OLD_TEXT:
            t = cv.create_text(W // 2, y, text=para, font=("Segoe UI", -int(16 * s)),
                               fill="#FFFFFF", width=bw - pad * 2, justify="center",
                               anchor="n", tags="fx")
            items.append(t)
            y = cv.bbox(t)[3] + int(16 * s)
        box_h = y + pad
        y1 = (H - box_h) // 2 - int(20 * s)
        box = self.round_rect(x1, y1, x1 + bw, y1 + box_h, int(22 * s),
                              fill="#141414", outline="#3A3A3A", tags="fx")
        for t in items:
            cv.move(t, 0, y1 + pad - int(6 * s))
            cv.tag_raise(t)
        self.power_icon(W // 2, y1 + pad + icon_r - int(6 * s), icon_r, max(3, int(7 * s)))
        # an old Mac just sits here until you hold the power button
        self.later(14000, self.fx_restart)

    # Linux Kernel Panic -----------------------------------------------------
    LINUX_BOOT = [
        "Linux version 6.8.0-45-generic (buildd@lcy02-amd64-075) (x86_64-linux-gnu-gcc-13 "
        "(Ubuntu 13.2.0-23ubuntu4) 13.2.0) #45-Ubuntu SMP PREEMPT_DYNAMIC",
        "Command line: BOOT_IMAGE=/boot/vmlinuz-6.8.0-45-generic root=UUID=4f2c9a1e-77d0-4b8e-"
        "9c3a-2d61f0e8b5a7 ro quiet splash",
        "KERNEL supported cpus:",
        "  Intel GenuineIntel",
        "  AMD AuthenticAMD",
        "BIOS-provided physical RAM map:",
        "BIOS-e820: [mem 0x0000000000000000-0x000000000009efff] usable",
        "BIOS-e820: [mem 0x0000000000100000-0x0000000009afffff] usable",
        "NX (Execute Disable) protection: active",
        "DMI: To Be Filled By O.E.M. To Be Filled By O.E.M./B550M Steel Legend, BIOS P2.10",
        "tsc: Detected 3593.250 MHz processor",
        "ACPI: Early table checksum verification disabled",
        "Zone ranges:",
        "  DMA      [mem 0x0000000000001000-0x0000000000ffffff]",
        "  DMA32    [mem 0x0000000001000000-0x00000000ffffffff]",
        "  Normal   [mem 0x0000000100000000-0x000000083f37ffff]",
        "smpboot: Allowing 16 CPUs, 0 hotplug CPUs",
        "Memory: 32651244K/33476348K available (20480K kernel code, 4469K rwdata)",
        "rcu: Preemptible hierarchical RCU implementation.",
        "NR_IRQS: 524544, nr_irqs: 1096, preallocated irqs: 16",
        "Console: colour dummy device 80x25",
        "printk: legacy console [tty0] enabled",
        "Calibrating delay loop (skipped), value calculated using timer frequency.. 7186.50 BogoMIPS",
        "x86/cpu: User Mode Instruction Prevention (UMIP) activated",
        "smp: Bringing up secondary CPUs ...",
        "smp: Brought up 1 node, 16 CPUs",
        "devtmpfs: initialized",
        "PCI: Using configuration type 1 for base access",
        "ACPI: Added _OSI(Module Device)",
        "ACPI: Interpreter enabled",
        "pci 0000:00:01.1: PCI bridge to [bus 01]",
        "usbcore: registered new interface driver usbfs",
        "NET: Registered PF_INET protocol family",
        "Trying to unpack rootfs image as initramfs...",
        "Freeing initrd memory: 71344K",
        "nvme nvme0: pci function 0000:01:00.0",
        "ahci 0000:02:00.1: AHCI 0001.0301 32 slots 6 ports 6 Gbps 0x3f impl SATA mode",
        "xhci_hcd 0000:03:00.0: xHCI Host Controller",
        "usb usb1: New USB device found, idVendor=1d6b, idProduct=0002, bcdDevice= 6.08",
        "input: Power Button as /devices/LNXSYSTM:00/LNXPWRBN:00/input/input0",
        "nvme nvme0: missing or invalid SUBNQN field.",
        "nvme nvme0: Shutdown timeout set to 10 seconds",
        "nvme nvme0: I/O queue 3 timeout, reset controller",
        "md: Waiting for all devices to be available before autodetect",
        "Waiting for root device UUID=4f2c9a1e-77d0-4b8e-9c3a-2d61f0e8b5a7...",
    ]
    LINUX_PANICS = [
        ("VFS: Unable to mount root fs on unknown-block(0,0)",
         ["dump_stack_lvl+0x48/0x70", "dump_stack+0x10/0x20", "panic+0x1a3/0x3b0",
          "mount_root_generic+0x1d0/0x300", "mount_root+0x10f/0x150",
          "prepare_namespace+0x6e/0x2b0", "kernel_init_freeable+0x271/0x2c0",
          "? __pfx_kernel_init+0x10/0x10", "kernel_init+0x1b/0x1f0",
          "ret_from_fork+0x44/0x70", "? __pfx_kernel_init+0x10/0x10",
          "ret_from_fork_asm+0x1b/0x30"]),
        ("Attempted to kill init! exitcode=0x0000000b",
         ["dump_stack_lvl+0x48/0x70", "dump_stack+0x10/0x20", "panic+0x1a3/0x3b0",
          "do_exit+0x9b1/0xb20", "do_group_exit+0x35/0x90", "get_signal+0x9a1/0x9e0",
          "arch_do_signal_or_restart+0x39/0x120", "irqentry_exit_to_user_mode+0x1a7/0x260",
          "irqentry_exit+0x43/0x50", "exc_page_fault+0x94/0x1b0",
          "asm_exc_page_fault+0x27/0x30"]),
        ("Fatal exception in interrupt",
         ["dump_stack_lvl+0x48/0x70", "dump_stack+0x10/0x20", "panic+0x1a3/0x3b0",
          "oops_end+0xcd/0xe0", "die_addr+0x3d/0x70", "exc_general_protection+0x1d5/0x450",
          "asm_exc_general_protection+0x27/0x30", "nvme_irq+0x1c2/0x2e0 [nvme]",
          "__handle_irq_event_percpu+0x4c/0x1b0", "handle_irq_event+0x39/0x80",
          "handle_edge_irq+0x8c/0x250", "common_interrupt+0x9f/0xc0"]),
    ]
    TUX = [
        r"     .--.        _ ",
        r"    |o_o |      | |",
        r"    |:_/ |      | |",
        r"   //   \ \     |_|",
        r"  (|     | )     _ ",
        r" /'\_   _/`\    (_)",
        r" \___)=(___/       ",
    ]

    def mono_font(self):
        return "Consolas" if IS_WIN else "DejaVu Sans Mono"

    def fx_linux(self):
        self.force_focus()
        self.freeze()
        reason, trace = random.choice(self.LINUX_PANICS)
        if self.style_i == 1:
            self.later(self.FREEZE_MS, lambda: self.linux_old(reason, trace))
        else:
            self.later(self.FREEZE_MS, lambda: self.linux_new(reason))

    # old style: classic text console, messages scroll, then the panic dump
    def linux_old(self, reason, trace):
        cv = self.cv
        cv.delete("fx")
        self._img = None
        W, H = self.W, self.H
        cv.create_rectangle(0, 0, W, H, fill="#000000", outline="#000000", tags="fx")
        cv.config(cursor="none")
        size = max(10, int(H / 50))
        font = (self.mono_font(), -size)
        probe = cv.create_text(0, 0, text="X\nX", font=font, anchor="nw")
        line_h = (cv.bbox(probe)[3] - cv.bbox(probe)[1]) / 2.0
        cv.delete(probe)
        self.lx_rows = max(10, int((H - 8) / line_h) - 1)
        self.lx_lines = []
        self.lx_item = cv.create_text(8, 4, text="", font=font, fill="#AAAAAA", anchor="nw",
                                      tags="fx")
        clock = [random.uniform(0.0, 0.002)]

        def stamp(step):
            clock[0] += step
            return "[%12.6f] " % clock[0]

        t = 0
        for msg in self.LINUX_BOOT:
            line = stamp(random.uniform(0.002, 0.09)) + msg
            t += random.randint(15, 70)
            self.later(t, lambda l=line: self.lx_add(l))
        t += 1800                         # stuck waiting for the drive...
        cpu = random.randint(0, 15)
        block = ["Kernel panic - not syncing: " + reason,
                 "CPU: %d PID: 1 Comm: swapper/0 Not tainted 6.8.0-45-generic #45-Ubuntu" % cpu,
                 "Hardware name: To Be Filled By O.E.M. B550M Steel Legend/B550M Steel Legend, "
                 "BIOS P2.10 02/15/2024",
                 "Call Trace:", " <TASK>"]
        block += [" " + fn for fn in trace]
        block += [" </TASK>",
                  "Kernel Offset: 0x%x from 0xffffffff81000000 (relocation range: "
                  "0xffffffff80000000-0xffffffffbfffffff)" % (random.randint(0x100, 0x3ff) << 20)]
        for msg in block:
            line = stamp(random.uniform(0.000001, 0.00004)) + msg
            t += 12
            self.later(t, lambda l=line: self.lx_add(l))
        end = stamp(0.016) + "---[ end Kernel panic - not syncing: " + reason + " ]---"
        t += 60
        self.later(t, lambda: self.lx_add(end))
        # a panicked Linux box just sits there forever
        self.later(t + 12000, self.fx_restart)

    def lx_add(self, line):
        self.lx_lines.append(line)
        self.cv.itemconfigure(self.lx_item, text="\n".join(self.lx_lines[-self.lx_rows:]))

    # new style: the modern Linux panic screen (penguin + centered message)
    def linux_new(self, reason):
        cv = self.cv
        cv.delete("fx")
        self._img = None
        W, H = self.W, self.H
        cv.create_rectangle(0, 0, W, H, fill="#000000", outline="#000000", tags="fx")
        cv.config(cursor="none")
        font = (self.mono_font(), -max(12, int(H / 42)))
        cv.create_text(0, 0, text="\n".join(self.TUX), font=font, fill="#FFFFFF",
                       anchor="nw", tags="fx")
        msg = "\n".join(["KERNEL PANIC!", "", "Please reboot your computer.", "", reason])
        cv.create_text(W // 2, H // 2, text=msg, font=font, fill="#FFFFFF",
                       justify="center", anchor="center", tags="fx")
        self.later(13000, self.fx_restart)

    # No Bootable Device -----------------------------------------------------
    POST_LINES = [
        "BIOS Date: 02/15/24 18:22:43 Ver: 2.10",
        "CPU : AMD Ryzen 5 5600X 6-Core Processor",
        " Speed : 3.70 GHz",
        "",
        "Press DEL to run Setup",
        "Press F8 for BBS POPUP",
        "DDR4 3200MHz Dual-Channel Interleaved",
        "Initializing USB Controllers .. Done.",
        "MEMTEST",
        "",
        "USB Device(s): 1 Keyboard, 1 Mouse, 1 Hub",
        "Auto-detecting AHCI Port 0...",
        "Auto-detecting AHCI Port 1...",
        "Auto-detecting NVMe Drive...",
        "",
    ]

    def fx_noboot(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, self.noboot_black)

    def noboot_black(self):
        cv = self.cv
        cv.delete("fx")
        self._img = None
        cv.create_rectangle(0, 0, self.W, self.H, fill="#000000", outline="#000000", tags="fx")
        cv.config(cursor="none")
        if self.style_i == 1:
            self.later(1800, self.noboot_old)
        else:
            self.later(2200, self.noboot_new)

    def nb_setup(self, color):
        """Text console for the boot screens."""
        size = max(12, int(self.H / 40))
        self.nb_font = (self.mono_font(), -size)
        self.nb_lines = []
        self.nb_color = color
        self.nb_item = self.cv.create_text(int(size * 0.8), int(size * 0.8), text="",
                                           font=self.nb_font, fill=color, anchor="nw",
                                           tags="fx")
        self.nb_cursor_on = True

    def nb_show(self, cursor=True):
        text = "\n".join(self.nb_lines)
        if cursor:
            text += "\n" + ("_" if self.nb_cursor_on else " ")
        self.cv.itemconfigure(self.nb_item, text=text)

    def nb_blink(self):
        self.nb_cursor_on = not self.nb_cursor_on
        self.nb_show()
        self.later(500, self.nb_blink)

    def nb_wait_key(self, message):
        """Show the message; pressing a key just shows it again (nothing to boot!)."""
        def again():
            self.nb_lines += [""] + message
            self.nb_lines = self.nb_lines[-30:]
            self.nb_show()
            self.any_key = again
        self.nb_lines += message
        self.nb_show()
        self.any_key = again
        self.later(500, self.nb_blink)
        self.later(15000, self.fx_restart)

    # old style: classic BIOS startup screen
    def noboot_old(self):
        self.nb_setup("#AAAAAA")
        t = 0
        for line in self.POST_LINES:
            if line == "MEMTEST":
                self.later(t, lambda: self.nb_lines.append("Memory Test :      0M"))
                for mb in range(2048, 32768 + 1, 2048):
                    t += 55
                    self.later(t, lambda mb=mb: self.nb_set_last("Memory Test : %6dM" % mb))
                t += 90
                self.later(t, lambda: self.nb_set_last("Memory Test :  32768M OK"))
                continue
            t += random.randint(80, 250)
            if line.startswith("Auto-detecting"):
                t += random.randint(250, 450)
                self.later(t, lambda l=line: self.nb_add(l))
                t += random.randint(500, 800)
                self.later(t, lambda l=line: self.nb_set_last(l + " Not detected"))
            else:
                self.later(t, lambda l=line: self.nb_add(l))
        t += 700
        self.later(t, lambda: self.nb_wait_key(
            ["Reboot and Select proper Boot device",
             "or Insert Boot Media in selected Boot device and press a key"]))

    def nb_add(self, line):
        self.nb_lines.append(line)
        self.nb_show(cursor=False)

    def nb_set_last(self, line):
        if self.nb_lines:
            self.nb_lines[-1] = line
        self.nb_show(cursor=False)

    # new style: modern laptop firmware message
    def noboot_new(self):
        self.nb_setup("#FFFFFF")
        self.nb_wait_key(["No Bootable Device -- insert boot disk and press any key"])

    # Phone errors -----------------------------------------------------------
    def phone_area(self, kind="android", bg="#000000"):
        """Black screen, plus a drawn phone in the middle when 'Phone-shaped' is picked.
        Returns the phone screen box (x1, y1, x2, y2) and a scale (pixels per phone dp)."""
        cv = self.cv
        W, H = self.W, self.H
        cv.delete("fx")
        self._img = None
        cv.create_rectangle(0, 0, W, H, fill="#000000", outline="#000000", tags="fx")
        cv.config(cursor="none")
        if self.phone_disp_i == 1:                    # full screen
            cv.create_rectangle(0, 0, W, H, fill=bg, outline=bg, tags="fx")
            return 0, 0, W, H, H / 915.0
        ph = int(H * 0.92)
        pw = int(ph * 0.47)
        bx1, by1 = (W - pw) // 2, (H - ph) // 2
        r = int(pw * 0.13)
        # side buttons (power + volume), then the body
        cv.create_rectangle(bx1 + pw - 2, by1 + ph * 0.22, bx1 + pw + 5, by1 + ph * 0.30,
                            fill="#2A2A2D", outline="", tags="fx")
        cv.create_rectangle(bx1 + pw - 2, by1 + ph * 0.34, bx1 + pw + 5, by1 + ph * 0.46,
                            fill="#2A2A2D", outline="", tags="fx")
        self.round_rect(bx1, by1, bx1 + pw, by1 + ph, r, fill="#1A1A1C", outline="#3B3B40",
                        width=2, tags="fx")
        b = max(6, int(pw * 0.035))
        x1, y1, x2, y2 = bx1 + b, by1 + b, bx1 + pw - b, by1 + ph - b
        self.round_rect(x1, y1, x2, y2, r - b, fill=bg, outline="", tags="fx")
        cx = (x1 + x2) // 2
        if kind == "iphone":                           # pill-shaped cutout
            pw2, ph2 = int(pw * 0.30), max(8, int(pw * 0.085))
            py1 = y1 + int(pw * 0.03)
            self.round_rect(cx - pw2 // 2, py1, cx + pw2 // 2, py1 + ph2, ph2 // 2,
                            fill="#050506", outline="", tags="fx")
        else:                                          # punch-hole camera
            cam = max(4, int(pw * 0.022))
            cv.create_oval(cx - cam, y1 + cam * 2, cx + cam, y1 + cam * 4, fill="#0B0B0D",
                           outline="#222226", tags="fx")
        return x1, y1, x2, y2, (x2 - x1) / 412.0

    def phone_off(self, then=None, wait=1800):
        """Phone screen goes dark (and the panel comes back after)."""
        self.any_key = None
        self.key_handler = None
        self.cv.delete("fx")
        self.cv.create_rectangle(0, 0, self.W, self.H, fill="#000000", outline="#000000",
                                 tags="fx")
        self.later(wait, then or self.end_effect)

    # Android: "Your device is corrupt" ---------------------------------------
    def fx_corrupt(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, lambda: self.phone_off(self.corrupt_screen, 1400))

    def corrupt_screen(self):
        cv = self.cv
        x1, y1, x2, y2, u = self.phone_area()
        pad = int(32 * u) if self.phone_disp_i == 0 else int(self.W * 0.1)
        wrap = int(min(x2 - x1, 900 * u + pad * 2) - pad * 2)
        left = x1 + pad
        # red warning icon
        ir = int(26 * u)
        icy = y1 + int(150 * u)
        cv.create_oval(left, icy - ir, left + ir * 2, icy + ir, fill="#EA4335", outline="",
                       tags="fx")
        cv.create_text(left + ir, icy, text="!", font=("Segoe UI", -int(34 * u), "bold"),
                       fill="#000000", tags="fx")
        y = icy + ir + int(36 * u)
        t = cv.create_text(left, y, text="Your device is corrupt", anchor="nw", width=wrap,
                           font=("Segoe UI", -int(34 * u)), fill="#FFFFFF", tags="fx")
        y = cv.bbox(t)[3] + int(22 * u)
        t = cv.create_text(left, y, text="It can't be trusted and may not work properly.",
                           anchor="nw", width=wrap, font=("Segoe UI", -int(18 * u)),
                           fill="#C8C8C8", tags="fx")
        y = cv.bbox(t)[3] + int(28 * u)
        t = cv.create_text(left, y, text="Visit this link on another device:", anchor="nw",
                           width=wrap, font=("Segoe UI", -int(18 * u)), fill="#C8C8C8", tags="fx")
        y = cv.bbox(t)[3] + int(6 * u)
        cv.create_text(left, y, text="g.co/ABH", anchor="nw",
                       font=("Segoe UI", -int(20 * u), "bold"), fill="#8AB4F8", tags="fx")
        # bottom hint
        by = y2 - int(90 * u)
        self.power_icon(left + int(12 * u), by, int(11 * u), max(2, int(3 * u)), "#C8C8C8")
        cv.create_text(left + int(36 * u), by, text="Press power button to continue.",
                       anchor="w", font=("Segoe UI", -int(16 * u)), fill="#C8C8C8", tags="fx")
        # any key = the power button: the phone "continues" booting (goes dark)
        self.any_key = lambda: self.phone_off(wait=2200)
        # nobody pressed it? the real phone powers itself off after 30 seconds
        self.later(30000, lambda: self.phone_off(wait=1500))

    # PS4: CE-34878-0 (a game crashed) ----------------------------------------
    def fx_ce34878(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, self.ce_dim)

    def ce_dim(self):
        self.dim_frozen(0.7)
        self.later(500, self.ce_dialog)

    def ce_dialog(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0

        def S(v):
            return int(round(v * s))

        bw, bh = S(860), S(400)
        x1, y1 = (W - bw) // 2, (H - bh) // 2
        cv.create_rectangle(x1, y1, x1 + bw, y1 + bh, fill="#24272E", outline="#3A3F4A",
                            width=max(1, S(2)), tags="fx")
        pad = S(48)
        t = cv.create_text(x1 + pad, y1 + pad, text="An error has occurred in the following "
                           "application.", anchor="nw", fill="#FFFFFF",
                           font=("Segoe UI", -S(28)), width=bw - pad * 2, tags="fx")
        y = cv.bbox(t)[3] + S(28)
        t = cv.create_text(x1 + pad, y, text=random.choice(FAKE_GAMES), anchor="nw",
                           fill="#FFFFFF", font=("Segoe UI", -S(26)), tags="fx")
        y = cv.bbox(t)[3] + S(26)
        cv.create_text(x1 + pad, y, text="(CE-34878-0)", anchor="nw", fill="#B9BEC9",
                       font=("Segoe UI", -S(24)), tags="fx")
        # the OK button (already selected, with a glowing edge)
        okw, okh = S(300), S(56)
        ox, oy = x1 + (bw - okw) // 2, y1 + bh - pad - okh
        cv.create_rectangle(ox - S(4), oy - S(4), ox + okw + S(4), oy + okh + S(4),
                            fill="", outline="#5FB4FF", width=max(1, S(3)), tags="fx")
        cv.create_rectangle(ox, oy, ox + okw, oy + okh, fill="#F2F4F7", outline="", tags="fx")
        cv.create_text(ox + okw // 2, oy + okh // 2, text="OK", fill="#1A1C22",
                       font=("Segoe UI", -S(24)), tags="fx")
        cv.create_text(x1 + bw, y1 + bh + S(20), text="Enter  OK", anchor="ne",
                       fill="#C9CED8", font=("Segoe UI", -S(18)), tags="fx")

        def ok(k):
            if k in ("Return", "KP_Enter", "space", "x", "X"):
                self.key_handler = None
                self.cancel_jobs()
                self.fx_restart()       # the game closes; screen goes dark, then back
        self.key_handler = ok
        self.later(20000, self.fx_restart)

    # PS4: not turned off properly ------------------------------------------
    def console_black(self):
        cv = self.cv
        cv.delete("fx")
        self._img = None
        cv.create_rectangle(0, 0, self.W, self.H, fill="#000000", outline="#000000", tags="fx")
        cv.config(cursor="none")

    def progress_bar(self, cx, y, width, height, pct, label=True):
        cv, s = self.cv, self.H / 1080.0
        x1 = cx - width // 2
        cv.delete("pbar")
        cv.create_rectangle(x1, y, x1 + width, y + height, fill="#2E3440", outline="",
                            tags=("fx", "pbar"))
        cv.create_rectangle(x1, y, x1 + int(width * pct / 100.0), y + height, fill="#E8ECF2",
                            outline="", tags=("fx", "pbar"))
        if label:
            cv.create_text(x1 + width, y + height + int(14 * s), text="%d%%" % pct, anchor="ne",
                           fill="#C9CED8", font=("Segoe UI", -int(20 * s)), tags=("fx", "pbar"))

    def fx_notoff(self):
        self.force_focus()
        self.freeze()
        # the power cuts out...
        self.later(self.FREEZE_MS, self.console_black)
        # ...comes back on, and the PS4 starts up again
        self.later(self.FREEZE_MS + 3200, self.notoff_screen)

    def notoff_screen(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        self.console_black()
        cv.create_text(W // 2, H // 2 - int(70 * s),
                       text="The PS4 was not turned off properly.\nChecking system storage...",
                       fill="#FFFFFF", justify="center", font=("Segoe UI", -int(30 * s)),
                       tags="fx")
        bar_w, bar_h, bar_y = int(760 * s), max(4, int(8 * s)), H // 2 + int(30 * s)
        self.progress_bar(W // 2, bar_y, bar_w, bar_h, 0)
        t = 600
        pct = 0
        while pct < 100:
            pct = min(100, pct + random.choice([1, 2, 3, 3, 5, 8]))
            t += random.randint(120, 600)
            self.later(t, lambda p=pct: self.progress_bar(W // 2, bar_y, bar_w, bar_h, p))
        self.later(t + 1500, self.fx_restart)

    # PS4: Safe Mode ----------------------------------------------------------
    SAFE_ITEMS = [
        "Restart PS4",
        "Change Resolution",
        "Update System Software",
        "Restore Default Settings",
        "Rebuild Database",
        "Initialize PS4",
        "Initialize PS4 (Reinstall System Software)",
        "Set HDCP Mode",
    ]

    def fx_safemode(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, self.console_black)
        self.later(self.FREEZE_MS + 2500, self.safe_connect)

    def safe_frame(self):
        """Black screen with the 'Safe Mode' title bar."""
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        self.console_black()
        cv.create_text(int(120 * s), int(70 * s), text="Safe Mode", anchor="nw",
                       fill="#FFFFFF", font=("Segoe UI", -int(40 * s)), tags="fx")
        cv.create_line(int(120 * s), int(140 * s), W - int(120 * s), int(140 * s),
                       fill="#3A4050", width=max(1, int(2 * s)), tags="fx")
        return s

    def safe_connect(self):
        s = self.safe_frame()
        self.cv.create_text(self.W // 2, self.H // 2,
                            text="Connect the DUALSHOCK 4 using the USB cable and then press "
                                 "the PS button.", width=int(1100 * s), justify="center",
                            fill="#FFFFFF", font=("Segoe UI", -int(30 * s)), tags="fx")
        self.cv.create_text(self.W // 2, self.H - int(110 * s),
                            text="(press any key on your keyboard)", fill="#7E8696",
                            font=("Segoe UI", -int(18 * s)), tags="fx")
        self.safe_sel = 0
        self.safe_choice = None
        self.any_key = self.safe_menu
        self.later(30000, self.fx_restart)

    def safe_menu(self):
        self.cancel_jobs()
        self.key_handler = self.safe_key
        self.safe_mode = "menu"
        self.safe_draw()
        self.later(120000, self.fx_restart)

    def safe_draw(self):
        cv = self.cv
        W, H = self.W, self.H
        s = self.safe_frame()
        left, row_h = int(160 * s), int(66 * s)
        y = int(200 * s)
        if self.safe_mode == "menu":
            items = ["%d. %s" % (i + 1, it) for i, it in enumerate(self.SAFE_ITEMS)]
        else:   # a yes/no question
            t = cv.create_text(left, y, text=self.safe_question, anchor="nw", fill="#FFFFFF",
                               width=W - left * 2, font=("Segoe UI", -int(28 * s)), tags="fx")
            y = cv.bbox(t)[3] + int(50 * s)
            items = self.safe_answers
        for i, item in enumerate(items):
            if i == self.safe_sel:
                cv.create_rectangle(left - int(24 * s), y, W - left, y + row_h - int(8 * s),
                                    fill="#1C2740", outline="#5FB4FF", width=max(1, int(3 * s)),
                                    tags="fx")
            cv.create_text(left, y + (row_h - int(8 * s)) // 2, text=item, anchor="w",
                           fill="#FFFFFF", font=("Segoe UI", -int(28 * s)), tags="fx")
            y += row_h
        cv.create_text(W - int(120 * s), H - int(70 * s), text="\u2191\u2193 Select     Enter  OK",
                       anchor="e", fill="#C9CED8", font=("Segoe UI", -int(20 * s)), tags="fx")

    def safe_key(self, key):
        if self.safe_mode == "busy":
            return
        count = len(self.SAFE_ITEMS) if self.safe_mode == "menu" else len(self.safe_answers)
        if key in ("Up", "w", "W"):
            self.safe_sel = (self.safe_sel - 1) % count
        elif key in ("Down", "s", "S"):
            self.safe_sel = (self.safe_sel + 1) % count
        elif key in ("Return", "KP_Enter", "space"):
            self.safe_pick()
            return
        elif key in ("Escape", "BackSpace") and self.safe_mode == "ask":
            self.safe_back()
            return
        else:
            return
        self.safe_draw()

    def safe_back(self):
        self.safe_mode = "menu"
        self.safe_sel = 0
        self.safe_draw()

    def safe_ask(self, question, answers, on_yes):
        self.safe_mode = "ask"
        self.safe_question = question
        self.safe_answers = answers
        self.safe_yes = on_yes
        self.safe_sel = len(answers) - 1          # the PS4 puts the cursor on the safe choice
        self.safe_draw()

    def safe_work(self, text, seconds, then, done_text=None):
        """A message with a progress bar, like the PS4 doing something."""
        self.safe_mode = "busy"
        W, H = self.W, self.H
        s = self.safe_frame()
        self.cv.create_text(W // 2, H // 2 - int(60 * s), text=text, fill="#FFFFFF",
                            justify="center", font=("Segoe UI", -int(30 * s)), tags="fx")
        bar_w, bar_h, bar_y = int(760 * s), max(4, int(8 * s)), H // 2 + int(20 * s)
        self.progress_bar(W // 2, bar_y, bar_w, bar_h, 0)
        steps = 20
        for k in range(1, steps + 1):
            self.later(int(seconds * 1000 * k / steps),
                       lambda k=k: self.progress_bar(W // 2, bar_y, bar_w, bar_h,
                                                     int(100 * k / steps)))
        end = int(seconds * 1000) + 600
        if done_text:
            self.later(end, lambda: self.safe_message(done_text, then))
        else:
            self.later(end, then)

    def safe_message(self, text, then, wait=2600):
        self.safe_mode = "busy"
        s = self.safe_frame()
        self.cv.create_text(self.W // 2, self.H // 2, text=text, fill="#FFFFFF",
                            justify="center", width=int(1200 * s),
                            font=("Segoe UI", -int(30 * s)), tags="fx")
        self.later(wait, then)

    def safe_restart(self):
        self.key_handler = None
        self.later(10, self.fx_restart)

    def safe_pick(self):
        if self.safe_mode == "ask":
            if self.safe_sel == 0:
                self.safe_yes()
            else:
                self.safe_back()
            return
        item = self.SAFE_ITEMS[self.safe_sel]
        if item == "Restart PS4":
            self.safe_restart()
        elif item == "Change Resolution":
            self.safe_message("The PS4 will restart, and the resolution will be changed "
                              "to 480p.", self.safe_restart)
        elif item == "Update System Software":
            self.safe_work("Checking for an update...", 4, self.safe_back,
                           "The latest version of the system software is already installed.")
        elif item == "Restore Default Settings":
            self.safe_ask("Your PS4 will be restored to its default settings. "
                          "Saved data, applications, and screenshots will not be deleted.",
                          ["Restore", "Cancel"],
                          lambda: self.safe_work("Restoring default settings...", 5,
                                                 self.safe_restart))
        elif item == "Rebuild Database":
            self.safe_ask("Rebuilding the database might take a long time.\n"
                          "Rebuild the database?", ["OK", "Cancel"],
                          lambda: self.safe_work("Rebuilding database...\nDo not turn off "
                                                 "the PS4.", 8, self.safe_restart))
        elif item == "Initialize PS4":
            self.safe_ask("All data and settings will be deleted, and the PS4 will be "
                          "restored to its factory state. This cannot be undone.\n\n"
                          "Initialize the PS4?", ["Initialize", "Cancel"],
                          lambda: self.safe_work("Initializing...\nDo not turn off the PS4.",
                                                 9, self.safe_restart,
                                                 "Initialization is complete. The PS4 will "
                                                 "restart."))
        elif item.startswith("Initialize PS4 ("):
            self.safe_message("Connect a USB storage device that contains the update file "
                              "for reinstallation.\n\n(SU-41350-3)", self.safe_back, 3500)
        elif item == "Set HDCP Mode":
            self.safe_message("HDCP mode is set to HDCP 2.2 only.\nThe PS4 will restart.",
                              self.safe_restart)

    # PS4: SU-30746-0 ---------------------------------------------------------
    def fx_su30746(self):
        self.force_focus()
        self.freeze()
        self.su_tries = 0
        self.later(self.FREEZE_MS, self.console_black)
        self.later(self.FREEZE_MS + 2500, self.su_screen)

    def su_screen(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        self.console_black()
        left = int(260 * s)
        y = int(H * 0.30)
        t = cv.create_text(left, y, text="Cannot start the PS4.", anchor="nw", fill="#FFFFFF",
                           font=("Segoe UI", -int(40 * s)), tags="fx")
        y = cv.bbox(t)[3] + int(36 * s)
        t = cv.create_text(left, y, text="An error has occurred in the system software.",
                           anchor="nw", fill="#E1E5EC", width=W - left * 2,
                           font=("Segoe UI", -int(28 * s)), tags="fx")
        y = cv.bbox(t)[3] + int(14 * s)
        cv.create_text(left, y, text="(SU-30746-0)", anchor="nw", fill="#B9BEC9",
                       font=("Segoe UI", -int(26 * s)), tags="fx")
        # the "Restart PS4" button, already selected
        bw, bh = int(360 * s), int(60 * s)
        bx, by = left, int(H * 0.62)
        cv.create_rectangle(bx - int(4 * s), by - int(4 * s), bx + bw + int(4 * s),
                            by + bh + int(4 * s), fill="", outline="#5FB4FF",
                            width=max(1, int(3 * s)), tags="fx")
        cv.create_rectangle(bx, by, bx + bw, by + bh, fill="#F2F4F7", outline="", tags="fx")
        cv.create_text(bx + bw // 2, by + bh // 2, text="Restart PS4", fill="#1A1C22",
                       font=("Segoe UI", -int(24 * s)), tags="fx")
        cv.create_text(W - int(120 * s), H - int(70 * s), text="Enter  OK", anchor="e",
                       fill="#C9CED8", font=("Segoe UI", -int(20 * s)), tags="fx")

        def restart(k):
            if k in ("Return", "KP_Enter", "space"):
                self.key_handler = None
                self.cancel_jobs()
                self.su_tries += 1
                self.console_black()
                if self.su_tries >= 3:          # it gives up after a few tries
                    self.later(2500, self.end_effect)
                else:                           # restarts... into the same error
                    self.later(3500, self.su_screen)
        self.key_handler = restart
        self.later(25000, self.fx_restart)

    # PS4: Blue Light of Death ------------------------------------------------
    def fx_bluelight(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, self.console_black)
        self.later(self.FREEZE_MS + 1800, self.bluelight_start)

    def bluelight_start(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        # the console's light, glowing through at the bottom of the screen
        lw, lh = int(520 * s), max(4, int(10 * s))
        glow = [cv.create_rectangle(W // 2 - lw // 2 - i * int(10 * s), H - int(40 * s) - i * 3,
                                    W // 2 + lw // 2 + i * int(10 * s),
                                    H - int(40 * s) + lh + i * 3, fill="#000000", outline="",
                                    tags="fx") for i in range(4, -1, -1)]
        # the monitor's own "No Signal" box, drifting around like a screensaver
        bw, bh = int(300 * s), int(120 * s)
        box = cv.create_rectangle(0, 0, bw, bh, fill="#1E1E22", outline="#55555C",
                                  width=max(1, int(2 * s)), tags=("fx", "osd"))
        cv.create_text(bw // 2, int(40 * s), text="HDMI 1", fill="#9A9AA2",
                       font=("Segoe UI", -int(20 * s)), tags=("fx", "osd"))
        cv.create_text(bw // 2, int(78 * s), text="No Signal", fill="#FFFFFF",
                       font=("Segoe UI", -int(30 * s)), tags=("fx", "osd"))
        cv.itemconfigure("osd", state="hidden")
        x, y = random.randint(0, W - bw), random.randint(0, H // 2)
        cv.move("osd", x, y)
        state = {"x": x, "y": y, "dx": max(1, int(2 * s)), "dy": max(1, int(2 * s)), "t": 0}

        def tick():
            state["t"] += 1
            t = state["t"]
            # the light pulses slowly, the way a stuck PS4 does
            level = (math.sin(t * 0.06) + 1) / 2
            for i, g in enumerate(glow):
                fade = level * (0.25 + 0.75 * (i + 1) / len(glow))
                cv.itemconfigure(g, fill=mix("#000000", "#2F8BFF", fade))
            # the No Signal box shows up after a couple of seconds, then drifts
            if t == 40:
                cv.itemconfigure("osd", state="normal")
            if t > 40:
                nx, ny = state["x"] + state["dx"], state["y"] + state["dy"]
                if nx < 0 or nx > W - bw:
                    state["dx"] *= -1
                if ny < 0 or ny > H - bh - int(80 * s):
                    state["dy"] *= -1
                cv.move("osd", state["dx"], state["dy"])
                state["x"] += state["dx"]
                state["y"] += state["dy"]
            self.later(30, tick)
        tick()
        self.any_key = self.fx_restart
        self.later(22000, self.fx_restart)

    # Xbox: "Something went wrong" ---------------------------------------------
    XBOX_GREEN = "#107C10"

    def fx_xbox(self):
        self.force_focus()
        self.freeze()
        code = random.choice(["E101", "E102", "E105", "E106", "E203", "E204", "E207", "E305"])
        self.xbox_code = "%s  %08X  %08X" % (code, random.randint(0, 0xFFFFFFFF),
                                             random.choice([0x80070002, 0x8007045D, 0x80070570,
                                                            0x80004005, 0x8007001F]))
        self.later(self.FREEZE_MS, self.console_black)
        self.later(self.FREEZE_MS + 2500, self.xbox_screen)

    def xbox_screen(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        cv.delete("fx")
        self._img = None
        cv.create_rectangle(0, 0, W, H, fill=self.XBOX_GREEN, outline=self.XBOX_GREEN, tags="fx")
        cv.config(cursor="none")
        left = int(W * 0.14)
        wrap = int(W * 0.62)
        y = int(H * 0.22)
        t = cv.create_text(left, y, text="Something went wrong", anchor="nw", fill="#FFFFFF",
                           font=("Segoe UI Light", -int(64 * s)), tags="fx")
        y = cv.bbox(t)[3] + int(30 * s)
        t = cv.create_text(left, y, text="Your Xbox needs to restart. If this keeps happening, "
                           "go to xbox.com/errorhelp and enter this code:", anchor="nw",
                           width=wrap, fill="#FFFFFF", font=("Segoe UI", -int(28 * s)), tags="fx")
        y = cv.bbox(t)[3] + int(22 * s)
        t = cv.create_text(left, y, text=self.xbox_code, anchor="nw", fill="#FFFFFF",
                           font=("Segoe UI Semibold", -int(30 * s)), tags="fx")
        self.xbox_btn_y = cv.bbox(t)[3] + int(70 * s)
        self.xbox_sel = 0
        self.xbox_draw_buttons()

        def key(k):
            if k in ("Left", "Right", "Up", "Down", "Tab"):
                self.xbox_sel = 1 - self.xbox_sel
                self.xbox_draw_buttons()
            elif k in ("Return", "KP_Enter", "space"):
                self.key_handler = None
                self.cancel_jobs()
                if self.xbox_sel == 0:          # Restart this Xbox
                    self.console_black()
                    self.later(3000, self.end_effect)
                else:                           # Troubleshoot
                    self.xbox_troubleshoot()
        self.key_handler = key
        self.later(30000, self.fx_restart)

    def xbox_draw_buttons(self):
        cv = self.cv
        s = self.H / 1080.0
        cv.delete("xbtn")
        left = int(self.W * 0.14)
        bw, bh, gap = int(330 * s), int(64 * s), int(24 * s)
        for i, label in enumerate(["Restart this Xbox", "Troubleshoot"]):
            x = left + i * (bw + gap)
            y = self.xbox_btn_y
            sel = i == self.xbox_sel
            cv.create_rectangle(x, y, x + bw, y + bh, fill="#FFFFFF" if sel else "#0B5A0B",
                                outline="#FFFFFF", width=max(1, int(3 * s)) if sel else 1,
                                tags=("fx", "xbtn"))
            cv.create_text(x + int(20 * s), y + bh // 2, text=label, anchor="w",
                           fill=self.XBOX_GREEN if sel else "#FFFFFF",
                           font=("Segoe UI", -int(24 * s)), tags=("fx", "xbtn"))
        cv.create_text(self.W - int(120 * s), self.H - int(70 * s),
                       text="\u2190\u2192 Select     Enter  OK", anchor="e", fill="#CFEFCF",
                       font=("Segoe UI", -int(20 * s)), tags=("fx", "xbtn"))

    def xbox_troubleshoot(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        cv.delete("fx")
        cv.create_rectangle(0, 0, W, H, fill=self.XBOX_GREEN, outline=self.XBOX_GREEN, tags="fx")
        cv.create_text(int(W * 0.14), int(H * 0.30), text="Troubleshooting...", anchor="nw",
                       fill="#FFFFFF", font=("Segoe UI Light", -int(56 * s)), tags="fx")
        cv.create_text(int(W * 0.14), int(H * 0.30) + int(100 * s),
                       text="This might take a few minutes. Don't turn off your Xbox.",
                       anchor="nw", fill="#FFFFFF", font=("Segoe UI", -int(26 * s)), tags="fx")
        # little dots that move along, like the Xbox's busy animation
        dots = [cv.create_oval(0, 0, 0, 0, fill="#FFFFFF", outline="", tags="fx")
                for _ in range(5)]
        y = int(H * 0.30) + int(180 * s)
        r = max(3, int(5 * s))

        def frame(f):
            for i, d in enumerate(dots):
                x = int(W * 0.14) + ((f * 9 - i * 22) % int(500 * s))
                cv.coords(d, x - r, y - r, x + r, y + r)
        for f in range(110):
            self.later(f * 40, lambda f=f: frame(f))
        # ...and it ends up right back at the same error
        self.later(110 * 40 + 300, self.xbox_screen)

    # Switch: Error 2162-0002 -------------------------------------------------
    def fx_switch(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, lambda: (self.dim_frozen(0.6),
                                            self.later(400, self.switch_dialog)))

    def switch_dialog(self):
        cv = self.cv
        W, H = self.W, self.H
        s = H / 1080.0
        bw, bh = int(760 * s), int(330 * s)
        x1, y1 = (W - bw) // 2, (H - bh) // 2
        self.round_rect(x1, y1, x1 + bw, y1 + bh, int(18 * s), fill="#2D2D2D", outline="",
                        tags="fx")
        cv.create_text(W // 2, y1 + int(100 * s),
                       text="The software was closed because an error occurred.",
                       fill="#FFFFFF", width=bw - int(80 * s), justify="center",
                       font=("Segoe UI", -int(28 * s)), tags="fx")
        cv.create_text(W // 2, y1 + int(165 * s), text="Error Code: 2162-0002",
                       fill="#BDBDBD", font=("Segoe UI", -int(24 * s)), tags="fx")
        # the button row at the bottom, with OK selected
        line_y = y1 + bh - int(90 * s)
        cv.create_line(x1, line_y, x1 + bw, line_y, fill="#4A4A4A",
                       width=max(1, int(2 * s)), tags="fx")
        pad = int(14 * s)
        cv.create_rectangle(x1 + pad, line_y + pad, x1 + bw - pad, y1 + bh - pad, fill="",
                            outline="#00C3E3", width=max(2, int(4 * s)), tags="fx")
        cv.create_text(W // 2, (line_y + y1 + bh) // 2, text="OK", fill="#00C3E3",
                       font=("Segoe UI", -int(28 * s)), tags="fx")

        def ok(k):
            if k in ("Return", "KP_Enter", "space", "a", "A"):
                self.key_handler = None
                self.cancel_jobs()
                self.fx_restart()
        self.key_handler = ok
        self.later(20000, self.fx_restart)

    # Download Mode -----------------------------------------------------------
    DL_BLUE = "#1565C0"

    def fx_download(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, lambda: self.phone_off(self.download_warning, 1400))

    def download_warning(self):
        cv = self.cv
        x1, y1, x2, y2, u = self.phone_area(bg=self.DL_BLUE)
        pad = int(28 * u) if self.phone_disp_i == 0 else int(self.W * 0.1)
        wrap = int(min(x2 - x1, 900 * u + pad * 2) - pad * 2)
        left = x1 + pad
        y = y1 + int(170 * u)
        t = cv.create_text(left, y, text="Warning", anchor="nw", fill="#FFFFFF",
                           font=("Segoe UI", -int(30 * u), "bold"), tags="fx")
        y = cv.bbox(t)[3] + int(24 * u)
        body = ("A custom OS can cause critical problems in phone and installed applications.\n\n"
                "If you want to download a custom OS, press the volume up key. Otherwise, press "
                "the volume down key to cancel.")
        t = cv.create_text(left, y, text=body, anchor="nw", width=wrap, fill="#FFFFFF",
                           font=("Segoe UI", -int(18 * u)), tags="fx")
        y = cv.bbox(t)[3] + int(40 * u)
        t = cv.create_text(left, y, text="Volume up :  Continue", anchor="nw", fill="#FFFFFF",
                           font=("Segoe UI", -int(18 * u), "bold"), tags="fx")
        y = cv.bbox(t)[3] + int(10 * u)
        cv.create_text(left, y, text="Volume down :  Cancel (restart phone)", anchor="nw",
                       fill="#FFFFFF", font=("Segoe UI", -int(18 * u), "bold"), tags="fx")
        y2b = y2 - int(70 * u)
        cv.create_text((x1 + x2) // 2, y2b, text="(on your keyboard:  ↑ continue   ↓ cancel)",
                       fill="#9EC5F5", font=("Segoe UI", -int(13 * u)), tags="fx")

        def key(k):
            if k == "Up":
                self.key_handler = None
                self.cancel_jobs()
                self.download_screen()
            elif k == "Down":
                self.phone_off(wait=2000)
        self.key_handler = key
        self.later(15000, lambda: (setattr(self, "key_handler", None), self.download_screen()))

    def download_screen(self):
        cv = self.cv
        x1, y1, x2, y2, u = self.phone_area(bg=self.DL_BLUE)
        pad = int(18 * u) if self.phone_disp_i == 0 else int(self.W * 0.04)
        left = x1 + pad
        info = [("ODIN MODE (AUTO DOWNLOAD)", "#FFFFFF"),
                ("PRODUCT NAME: SM-G991U", "#FFFFFF"),
                ("CURRENT BINARY: Samsung Official", "#FFFFFF"),
                ("KG STATE: Checking", "#FFFFFF"),
                ("FRP LOCK: ON", "#FFFFFF"),
                ("OEM LOCK: ON (L)", "#FFFFFF"),
                ("Secure Download : Enabled", "#FFFFFF"),
                ("WARRANTY VOID: 0 (0x0000)", "#FFFFFF"),
                ("AP SWREV: B:6 K:5 S:5", "#FFFFFF"),
                ("DID: 0D2B6C1E8F4A73", "#FFE066"),
                ("Sub DID: 3F1A9C2E", "#FFE066")]
        y = y1 + int(60 * u)
        font = (self.mono_font(), -max(10, int(12 * u)))
        for text, color in info:
            t = cv.create_text(left, y, text=text, anchor="nw", fill=color, font=font, tags="fx")
            y = cv.bbox(t)[3] + int(2 * u)
        # a download arrow going into a tray
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2 + int(30 * u)
        lw = max(3, int(8 * u))
        cv.create_line(cx, cy - int(70 * u), cx, cy + int(10 * u), fill="#FFFFFF", width=lw,
                       capstyle="round", tags="fx")
        cv.create_line(cx - int(32 * u), cy - int(22 * u), cx, cy + int(10 * u),
                       cx + int(32 * u), cy - int(22 * u), fill="#FFFFFF", width=lw,
                       capstyle="round", joinstyle="round", tags="fx")
        cv.create_line(cx - int(55 * u), cy + int(20 * u), cx - int(55 * u), cy + int(42 * u),
                       cx + int(55 * u), cy + int(42 * u), cx + int(55 * u), cy + int(20 * u),
                       fill="#FFFFFF", width=lw, capstyle="round", joinstyle="round", tags="fx")
        cv.create_text(cx, cy + int(95 * u), text="Downloading...", fill="#FFFFFF",
                       font=("Segoe UI", -int(24 * u)), tags="fx")
        cv.create_text(cx, cy + int(130 * u), text="Do not turn off target !!", fill="#FFFFFF",
                       font=("Segoe UI", -int(18 * u)), tags="fx")
        # it waits forever for a computer that never sends anything
        self.later(25000, lambda: self.phone_off(wait=1500))

    # Boot Loop ----------------------------------------------------------------
    def fx_bootloop(self):
        self.force_focus()
        self.freeze()
        self.bl_round = 0
        self.later(self.FREEZE_MS, lambda: self.phone_off(self.bootloop_warning, 1400))

    def bootloop_warning(self):
        cv = self.cv
        x1, y1, x2, y2, u = self.phone_area()
        pad = int(32 * u) if self.phone_disp_i == 0 else int(self.W * 0.1)
        wrap = int(min(x2 - x1, 900 * u + pad * 2) - pad * 2)
        left = x1 + pad
        ir = int(26 * u)
        icy = y1 + int(150 * u)
        cv.create_oval(left, icy - ir, left + ir * 2, icy + ir, fill="#F29900", outline="",
                       tags="fx")
        cv.create_text(left + ir, icy, text="!", font=("Segoe UI", -int(34 * u), "bold"),
                       fill="#000000", tags="fx")
        y = icy + ir + int(36 * u)
        body = ("The bootloader is unlocked and software integrity cannot be guaranteed. "
                "Any data stored on the device might be available to attackers. Do not store "
                "any sensitive data on the device.")
        t = cv.create_text(left, y, text=body, anchor="nw", width=wrap, fill="#FFFFFF",
                           font=("Segoe UI", -int(20 * u)), tags="fx")
        y = cv.bbox(t)[3] + int(28 * u)
        t = cv.create_text(left, y, text="Visit this link on another device:", anchor="nw",
                           width=wrap, font=("Segoe UI", -int(18 * u)), fill="#C8C8C8", tags="fx")
        y = cv.bbox(t)[3] + int(6 * u)
        t = cv.create_text(left, y, text="g.co/ABH", anchor="nw",
                           font=("Segoe UI", -int(20 * u), "bold"), fill="#8AB4F8", tags="fx")
        y = cv.bbox(t)[3] + int(22 * u)
        cv.create_text(left, y, text="ID: d14a028c", anchor="nw",
                       font=("Segoe UI", -int(16 * u)), fill="#C8C8C8", tags="fx")
        by = y2 - int(90 * u)
        self.power_icon(left + int(12 * u), by, int(11 * u), max(2, int(3 * u)), "#C8C8C8")
        cv.create_text(left + int(36 * u), by, text="Press power button to pause.",
                       anchor="w", font=("Segoe UI", -int(16 * u)), fill="#C8C8C8", tags="fx")
        # each loop gets a little faster, like it's giving up
        self.later(max(1800, 4000 - self.bl_round * 700), self.bootloop_anim)

    def bootloop_anim(self):
        cv = self.cv
        x1, y1, x2, y2, u = self.phone_area()
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        n, r, dot = 10, int(34 * u), max(3, int(6 * u))
        dots = []
        for i in range(n):
            a = 2 * math.pi * i / n
            x, y = cx + r * math.sin(a), cy - r * math.cos(a)
            dots.append(cv.create_oval(x - dot, y - dot, x + dot, y + dot, fill="#333333",
                                       outline="", tags="fx"))
        frames = random.randint(28, 45) - self.bl_round * 4
        for f in range(frames):
            def spin(f=f):
                for i, d in enumerate(dots):
                    age = (f - i) % n
                    shade = max(0x33, 0xFF - age * 0x22)
                    cv.itemconfigure(d, fill="#%02x%02x%02x" % (shade, shade, shade))
            self.later(f * 90, spin)
        # ...and then it crashes: the screen freezes, buzzes, and goes black
        self.later(frames * 90 + 400, self.bootloop_crash)

    def bootloop_crash(self):
        for i in range(6):                      # buzz (the whole picture shakes)
            dx = 6 if i % 2 == 0 else -6
            self.later(i * 45, lambda dx=dx: self.cv.move("fx", dx, 0))
        self.bl_round += 1
        if self.bl_round >= 4:                  # after a few loops, it just dies
            self.later(400, lambda: self.phone_off(wait=2500))
        else:
            self.later(400, lambda: self.phone_off(self.bootloop_warning, 1300))

    # Android: "No command" + the recovery menu ------------------------------
    RECOVERY_ITEMS = [
        "Reboot system now",
        "Reboot to bootloader",
        "Enter fastboot",
        "Apply update from ADB",
        "Apply update from SD card",
        "Wipe data/factory reset",
        "Wipe cache partition",
        "Mount /system",
        "View recovery logs",
        "Run graphics test",
        "Run locale test",
        "Power off",
    ]

    def fx_nocmd(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, lambda: self.phone_off(self.nocmd_screen, 1400))

    def warning_triangle(self, cx, cy, size, color="#E53935"):
        cv = self.cv
        h = size * 0.87
        cv.create_polygon(cx, cy - h / 2, cx + size / 2, cy + h / 2, cx - size / 2, cy + h / 2,
                          fill=color, outline=color, joinstyle="round", width=max(2, size // 12),
                          tags="fx")
        cv.create_text(cx, cy + h * 0.1, text="!", fill="#FFFFFF",
                       font=("Segoe UI", -int(size * 0.55), "bold"), tags="fx")

    def nocmd_screen(self):
        cv = self.cv
        x1, y1, x2, y2, u = self.phone_area()
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        self.warning_triangle(cx, cy - int(30 * u), int(80 * u))
        cv.create_text(cx, cy + int(50 * u), text="No command.", fill="#FFFFFF",
                       font=("Segoe UI", -int(22 * u)), tags="fx")
        self.phone_box = (x1, y1, x2, y2, u)
        # on a real phone you hold Power + Volume Up here; any key works in this one
        self.any_key = self.recovery_open
        self.later(25000, lambda: self.phone_off(wait=1500))

    def recovery_open(self):
        self.cancel_jobs()
        self.rec_sel = 0
        self.rec_log = []
        self.rec_mode = "menu"
        self.key_handler = self.recovery_key
        self.recovery_draw()
        self.later(90000, lambda: self.phone_off(wait=1500))

    def recovery_draw(self):
        cv = self.cv
        cv.delete("fx")
        x1, y1, x2, y2, u = self.phone_area()
        font = (self.mono_font(), -max(11, int(14 * u)))
        big = (self.mono_font(), -max(12, int(17 * u)))
        pad = int(14 * u) if self.phone_disp_i == 0 else int(self.W * 0.06)
        left = x1 + pad
        y = y1 + int(60 * u)
        header = ["Android Recovery", "google/sargo/sargo", "12/SP2A.220505.008/8782922",
                  "user/release-keys", "Use volume up/down and power."]
        for i, line in enumerate(header):
            t = cv.create_text(left, y, text=line, anchor="nw", font=big if i == 0 else font,
                               fill="#F0A33C" if i == 0 else "#C8C8C8", tags="fx")
            y = cv.bbox(t)[3] + int(4 * u)
        y += int(14 * u)
        if self.rec_mode == "menu":
            items = self.RECOVERY_ITEMS
        elif self.rec_mode == "confirm":
            t = cv.create_text(left, y, text="Wipe all user data?\n  THIS CAN NOT BE UNDONE!",
                               anchor="nw", font=font, fill="#FFFFFF", tags="fx")
            y = cv.bbox(t)[3] + int(14 * u)
            items = ["Cancel", "Factory data reset"]
        else:
            items = []
        row_h = int(30 * u)
        for i, item in enumerate(items):
            if i == self.rec_sel:
                cv.create_rectangle(x1, y, x2, y + row_h, fill="#6FB8E8", outline="", tags="fx")
            cv.create_text(left, y + row_h // 2, text=item, anchor="w", font=font,
                           fill="#000000" if i == self.rec_sel else "#FFFFFF", tags="fx")
            y += row_h
        # log lines at the bottom
        ly = y2 - int(30 * u)
        for line in reversed(self.rec_log[-8:]):
            t = cv.create_text(left, ly, text=line, anchor="sw", font=font, fill="#FFD27A",
                               tags="fx")
            ly = cv.bbox(t)[1] - int(2 * u)

    def recovery_key(self, key):
        if self.rec_mode == "busy":
            return
        items = self.RECOVERY_ITEMS if self.rec_mode == "menu" else ["Cancel", "Factory data reset"]
        if key in ("Up", "w", "W"):
            self.rec_sel = (self.rec_sel - 1) % len(items)
        elif key in ("Down", "s", "S"):
            self.rec_sel = (self.rec_sel + 1) % len(items)
        elif key in ("Return", "KP_Enter", "space"):
            self.recovery_pick(items[self.rec_sel])
            return
        else:
            return
        self.recovery_draw()

    def recovery_steps(self, lines, after):
        """Print fake log lines one by one, then do 'after'."""
        self.rec_mode = "busy"
        t = 0
        for line in lines:
            t += random.randint(500, 1100)
            self.later(t, lambda l=line: (self.rec_log.append(l), self.recovery_draw()))
        self.later(t + 900, after)

    def recovery_back(self):
        self.rec_mode = "menu"
        self.rec_sel = 0
        self.recovery_draw()

    def recovery_pick(self, item):
        if self.rec_mode == "confirm":
            if item == "Cancel":
                self.recovery_back()
            else:
                self.recovery_steps(["-- Wiping data...", "Formatting /data...",
                                     "Formatting /cache...", "Formatting /metadata...",
                                     "Data wipe complete."], self.recovery_back)
                self.recovery_draw()
            return
        if item.startswith("Reboot") or item == "Enter fastboot":
            self.rec_log.append("Rebooting...")
            self.rec_mode = "busy"
            self.recovery_draw()
            self.later(1200, lambda: self.phone_off(wait=2000))
        elif item == "Power off":
            self.rec_log.append("Shutting down...")
            self.rec_mode = "busy"
            self.recovery_draw()
            self.later(1200, lambda: self.phone_off(wait=1500))
        elif item == "Wipe data/factory reset":
            self.rec_mode = "confirm"
            self.rec_sel = 0
            self.recovery_draw()
        elif item == "Wipe cache partition":
            self.recovery_steps(["-- Wiping cache...", "Formatting /cache...",
                                 "Cache wipe complete."], self.recovery_back)
            self.recovery_draw()
        elif item.startswith("Apply update"):
            self.recovery_steps(["-- Install from " + ("ADB" if "ADB" in item else "SD card")
                                 + " ...", "E: No package found.", "Installation aborted."],
                                self.recovery_back)
            self.recovery_draw()
        else:
            self.recovery_steps(["-- " + item + " ...", "E: Not supported on this device."],
                                self.recovery_back)
            self.recovery_draw()

    # iPhone: recovery mode ---------------------------------------------------
    def fx_iphone(self):
        self.force_focus()
        self.freeze()
        self.later(self.FREEZE_MS, lambda: self.phone_off(self.iphone_screen, 1400))

    def iphone_screen(self):
        cv = self.cv
        x1, y1, x2, y2, u = self.phone_area("iphone")
        cx = (x1 + x2) // 2
        lw = max(2, int(4 * u))
        white = "#FFFFFF"
        # a laptop outline
        sw, sh = int(150 * u), int(96 * u)
        ty = (y1 + y2) // 2 - int(150 * u)
        self.round_rect(cx - sw // 2, ty, cx + sw // 2, ty + sh, int(9 * u), fill="",
                        outline=white, width=lw, tags="fx")
        by = ty + sh + int(6 * u)
        bw = int(186 * u)
        self.round_rect(cx - bw // 2, by, cx + bw // 2, by + int(10 * u), int(5 * u),
                        fill="", outline=white, width=lw, tags="fx")
        # a cable coming up from the bottom toward the computer
        plug_top = by + int(110 * u)
        cv.create_line(cx, plug_top + int(34 * u), cx, y2 - int(150 * u), fill=white,
                       width=lw, tags="fx")
        self.round_rect(cx - int(13 * u), plug_top, cx + int(13 * u), plug_top + int(36 * u),
                        int(6 * u), fill="", outline=white, width=lw, tags="fx")
        cv.create_rectangle(cx - int(6 * u), plug_top - int(16 * u), cx + int(6 * u), plug_top,
                            fill="", outline=white, width=lw, tags="fx")
        cv.create_text(cx, y2 - int(80 * u), text="support.apple.com/iphone/restore",
                       fill=white, font=("Segoe UI", -int(17 * u)), tags="fx")
        # a real iPhone sits here until it's plugged in and restored
        self.later(25000, lambda: self.phone_off(wait=1500))

    # Green Screen of Death (Windows Insider builds) --------------------------
    def fx_green(self):
        if self.style_i == 1:   # old: the classic Insider screen with the :( face
            self.fx_crash(lambda code: self.draw_bsod(code, bg=GSOD_GREEN,
                                                      who="Your Windows Insider Build"))
        else:                   # new: 2025 layout, in green
            self.fx_crash(lambda code: self.draw_blackscreen(code, bg=GSOD_GREEN))

    def draw_blackscreen(self, code, bg="#000000"):
        cv = self.cv
        cv.delete("fx")
        cv.config(cursor="none")
        self.force_focus()
        W, H = self.W, self.H
        s = H / 1080.0

        def S(v):
            return int(round(v * s))

        x0 = int(W * 0.135)
        white = "#FFFFFF"
        cv.create_rectangle(0, 0, W, H, fill=bg, outline=bg, tags="fx")
        main = cv.create_text(x0, int(H * 0.36),
                              text="Your device ran into a problem and needs to restart.",
                              font=("Segoe UI", -S(36)), fill=white, anchor="nw",
                              width=int(W * 0.75), tags="fx")
        y = cv.bbox(main)[3] + S(30)
        self.percent_item = cv.create_text(x0, y, text="0% complete", font=("Segoe UI", -S(36)),
                                           fill=white, anchor="nw", tags="fx")

        # small details near the bottom
        small = ("Segoe UI", -S(17))
        lines = ["For more information about this issue and possible fixes, visit "
                 "https://www.windows.com/stopcode",
                 "",
                 "Stop code: " + code]
        if code in WHAT_FAILED:
            lines.append("What failed: " + WHAT_FAILED[code])
        cv.create_text(x0, int(H * 0.80), text="\n".join(lines), font=small, fill=white,
                       anchor="sw", width=int(W * 0.75), tags="fx")
        self.run_progress()

    def draw_bsod(self, code, bg=BSOD_BLUE, who="Your PC"):
        cv = self.cv
        cv.delete("fx")
        cv.config(cursor="none")
        self.force_focus()
        W, H = self.W, self.H
        s = H / 1080.0

        def S(v):
            return int(round(v * s))

        x0 = int(W * 0.135)
        white = "#FFFFFF"
        cv.create_rectangle(0, 0, W, H, fill=bg, outline=bg, tags="fx")
        face = cv.create_text(x0 - S(8), int(H * 0.19), text=":(", font=("Segoe UI Light", -S(170)),
                              fill=white, anchor="nw", tags="fx")
        y = cv.bbox(face)[3] + S(10)
        main = cv.create_text(x0, y, text=who + " ran into a problem and needs to restart. We're "
                                          "just collecting some error info, and then we'll restart "
                                          "for you.",
                              font=("Segoe UI", -S(34)), fill=white, anchor="nw",
                              width=S(960), tags="fx")
        y = cv.bbox(main)[3] + S(34)
        self.percent_item = cv.create_text(x0, y, text="0% complete", font=("Segoe UI", -S(34)),
                                           fill=white, anchor="nw", tags="fx")
        y = cv.bbox(self.percent_item)[3] + S(46)

        q = S(118)
        self.draw_qr(x0, y, q, bg)
        tx = x0 + q + S(22)
        small = ("Segoe UI", -S(17))
        t1 = cv.create_text(tx, y - S(3), text="For more information about this issue and possible "
                                               "fixes, visit https://www.windows.com/stopcode",
                            font=small, fill=white, anchor="nw", width=S(820), tags="fx")
        ty = cv.bbox(t1)[3] + S(22)
        t2 = cv.create_text(tx, ty, text="If you call a support person, give them this info:",
                            font=small, fill=white, anchor="nw", tags="fx")
        ty = cv.bbox(t2)[3] + S(2)
        t3 = cv.create_text(tx, ty, text="Stop code: " + code, font=small, fill=white,
                            anchor="nw", tags="fx")
        if code in WHAT_FAILED:
            ty = cv.bbox(t3)[3] + S(2)
            cv.create_text(tx, ty, text="What failed: " + WHAT_FAILED[code], font=small,
                           fill=white, anchor="nw", tags="fx")
        self.run_progress()

    def set_pct(self, p):
        if self.percent_item:
            self.cv.itemconfigure(self.percent_item, text="%d%% complete" % p)

    def draw_qr(self, x, y, size, color=BSOD_BLUE):
        cv = self.cv
        n = 25
        m = size / n
        cv.create_rectangle(x, y, x + size, y + size, fill="#FFFFFF", outline="#FFFFFF", tags="fx")
        rnd = random.Random(1803)
        grid = [[rnd.random() < 0.48 for _ in range(n)] for _ in range(n)]

        def finder(r0, c0):
            for r in range(-1, 8):
                for c in range(-1, 8):
                    rr, cc = r0 + r, c0 + c
                    if 0 <= rr < n and 0 <= cc < n:
                        grid[rr][cc] = (0 <= r <= 6 and 0 <= c <= 6 and
                                        (r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4)))

        finder(0, 0)
        finder(0, n - 7)
        finder(n - 7, 0)
        for i in range(8, n - 8):
            grid[6][i] = grid[i][6] = (i % 2 == 0)
        for r in range(-2, 3):
            for c in range(-2, 3):
                grid[18 + r][18 + c] = max(abs(r), abs(c)) != 1
        for r in range(n):
            for c in range(n):
                if grid[r][c]:
                    cv.create_rectangle(x + round(c * m), y + round(r * m),
                                        x + round((c + 1) * m), y + round((r + 1) * m),
                                        fill=color, outline="", tags="fx")

    def fx_restart(self):
        self.any_key = None
        self.key_handler = None
        cv = self.cv
        cv.delete("fx")
        cv.create_rectangle(0, 0, self.W, self.H, fill="#000000", outline="#000000", tags="fx")
        cv.config(cursor="none")
        self.later(2600, self.end_effect)

    # ----- run ---------------------------------------------------------------
    def quit(self):
        self.cancel_jobs()
        self.mute.restore()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if not IS_WIN:
        print("Crash Simulator is made for Windows. On other systems the see-through "
              "background won't work.")
    CrashSimulator().run()
