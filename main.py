import subprocess
import time
import ctypes
import psutil
import os
from pyinjector import inject
import sbie as sandbox

injected_steam_pids = set()
injected_hl2_pids = set()

def inject_dll(pid, dll_path, injected_pids):
    if pid in injected_pids:
        print(f"Skipping injection: {dll_path} already injected into process {pid}")
    else:
        print(f"Injecting {dll_path} into process {pid}")
        inject(pid, dll_path)
        injected_pids.add(pid)

def start_and_inject(sbie, sandbox_name, hl2_exe, dll_path, steam, vac, username, password):
    # terminate everything on that sandbox
    sbie.terminate_sandbox_processes(sandbox_name)
    print(f"Starting REALITYBOT in '{sandbox_name}'...")
    
    steam_proc = sbie.execute([steam, "-noreactlogin", "-login", f"{username}", f"{password}"], sandbox_name)
    print(steam_proc)
    time.sleep(10)  # Wait for steam to start first (increased from 5 seconds)

    steam_pid = None
    for _ in range(5):  # Retry loop to find steam.exe
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'steam.exe' and proc.info['pid'] not in injected_steam_pids:
                steam_pid = proc.info['pid']
                break
        if steam_pid:
            break
        time.sleep(2)

    if steam_pid is None:
        raise RuntimeError("Failed to find uninjected steam.exe process.")
    print(f"Found steam.exe with PID {steam_pid}")
    
    inject_dll(steam_pid, vac, injected_steam_pids)  # inject vac bypass
    time.sleep(30)
    
    hl2_proc = sbie.execute([hl2_exe], sandbox_name)  # Start hl2.exe
    time.sleep(60)  # Wait for process to start (increased from 50 seconds)
    
    hl2_pid = None
    for _ in range(5):  # Retry loop to find hl2.exe
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'hl2.exe' and proc.info['pid'] not in injected_hl2_pids:
                hl2_pid = proc.info['pid']
                break
        if hl2_pid:
            break
        time.sleep(2)
    
    if hl2_pid is None:
        raise RuntimeError("Failed to find uninjected hl2.exe process.")
    print(f"Found hl2.exe with PID {hl2_pid}")
    
    inject_dll(hl2_pid, dll_path, injected_hl2_pids)
    
    return hl2_proc, hl2_pid, username, password

def monitor_processes(processes, sbie, hl2_exe, dll_path, steam, vac):
    while True:
        time.sleep(10)
        for i, (sandbox_name, hl2_proc, hl2_pid, username, password) in enumerate(processes):
            try:
                p = psutil.Process(hl2_pid)
                if p.name() == 'hl2.exe' and p.status() == psutil.STATUS_STOPPED:
                    print(f"HL2.exe in sandbox '{sandbox_name}' stopped unexpectedly. Restarting and injecting DLL...")
                    processes[i] = (sandbox_name, *start_and_inject(sbie, sandbox_name, hl2_exe, dll_path, steam, vac, username, password))
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                print(f"HL2.exe in sandbox '{sandbox_name}' crashed or closed. Restarting and injecting DLL...")
                processes[i] = (sandbox_name, *start_and_inject(sbie, sandbox_name, hl2_exe, dll_path, steam, vac, username, password))

def main():
    sbie = sandbox.Sandboxie()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    vacbypass_dll = os.path.join(script_dir, 'vacbypass.dll')
    steam_path = r"C:\Program Files (x86)\Steam\steam.exe"
    dll_path = os.path.join(script_dir, 'potassium.dll')
    hl2_exe = os.path.join(script_dir, 'bottf2.lnk')
    
    num_sandboxes = int(input("Enter the number of sandbox instances needed: "))
    
    with open(os.path.join(script_dir, 'accounts.txt'), 'r') as f:
        accounts = f.readlines()

    if len(accounts) < num_sandboxes:
        print("Not enough accounts in accounts.txt. Exiting.")
        return
    
    for i in range(num_sandboxes):
        try:
            sandbox_name = f'REALITYBOT_{i}'
            settings = sbie.make_sandbox_setting('default')
            sbie.create_sandbox(sandbox_name, settings=settings)
        except Exception as e:
            print(f"Failed to create sandbox '{sandbox_name}': {e}")
            continue
    
    input("Now go to Sandboxie and give permissions to the Steam folder.")

    processes = []
    for i in range(num_sandboxes):
        username, password = accounts[i].strip().split(':')
        sandbox_name = f'REALITYBOT_{i}'
        try:
            hl2_proc, hl2_pid, username, password = start_and_inject(sbie, sandbox_name, hl2_exe, dll_path, steam_path, vacbypass_dll, username, password)
            processes.append((sandbox_name, hl2_proc, hl2_pid, username, password))
        except RuntimeError as e:
            print(f"Failed to start and inject in '{sandbox_name}': {e}")
            continue

    monitor_processes(processes, sbie, hl2_exe, dll_path, steam_path, vacbypass_dll)

if __name__ == "__main__":
    main()
