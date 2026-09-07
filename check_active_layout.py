# check_active_layout.py
import ctypes
import time

user32 = ctypes.windll.user32

hwnd = user32.GetForegroundWindow()
thread_id = user32.GetWindowThreadProcessId(hwnd, None)
klid = user32.GetKeyboardLayout(thread_id)

# Os 16 bits inferiores sao a lingua, os 16 superiores sao a variante do layout
lang_id = klid & 0xFFFF
layout_id = (klid >> 16) & 0xFFFF

print(f"Foreground HWND: {hwnd} | Thread: {thread_id}")
print(f"Keyboard Layout HEX: {hex(klid)} | LangID: {hex(lang_id)} | LayoutVariant: {hex(layout_id)}")

# Lista de layouts instalados
num_layouts = user32.GetKeyboardLayoutList(0, None)
layouts = (ctypes.c_ulong * num_layouts)()
user32.GetKeyboardLayoutList(num_layouts, layouts)

print("\nTodos os layouts disponiveis no sistema atualmente:")
for i, l in enumerate(layouts):
    print(f"  [{i}] {hex(l)} (Lang: {hex(l & 0xFFFF)}, Variant: {hex((l >> 16) & 0xFFFF)})")
