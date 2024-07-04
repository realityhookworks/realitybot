import psutil
import pyautogui
import win32gui
import win32process
import time

def find_window_by_exe(exe_name):
    def enum_windows_callback(hwnd, pid_windows):
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            pid_windows[pid] = hwnd

    pid_windows = {}
    win32gui.EnumWindows(enum_windows_callback, pid_windows)

    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == exe_name:
            pid = proc.info['pid']
            if pid in pid_windows:
                return pid_windows[pid]
    return None

def focus_window(hwnd):
    if hwnd:
        win32gui.SetForegroundWindow(hwnd)
        return True
    print(f"No window found for the executable.")
    return False

def type_text(text):
    pyautogui.typewrite(text, interval=0.1)

def press_tab():
    pyautogui.press('tab')

def main():
    exe_name = "steam.exe"
    hwnd = find_window_by_exe(exe_name)
    if focus_window(hwnd):
        time.sleep(1)  # wait for the window to be focused
        type_text("First text")
        press_tab()
        type_text("Second text")

if __name__ == "__main__":
    main()
