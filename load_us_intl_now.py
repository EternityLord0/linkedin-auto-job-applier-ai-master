# load_us_intl_now.py
import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32

KLF_ACTIVATE = 0x00000001
KLF_REORDER = 0x00000008
KLF_SETFORPROCESS = 0x00000100
HWND_BROADCAST = 0xFFFF
WM_INPUTLANGCHANGEREQUEST = 0x0050

# Carregar o layout Estados Unidos (Internacional)
# Identificador de Layout US-International: "00020409"
hkl = user32.LoadKeyboardLayoutW("00020409", KLF_ACTIVATE | KLF_REORDER)
print(f"LoadKeyboardLayout 00020409 retornou HKL: {hex(hkl)}")

if hkl:
    # Transmitir a mudanca de idioma para todas as janelas abertas
    user32.PostMessageW(HWND_BROADCAST, WM_INPUTLANGCHANGEREQUEST, 0, hkl)
    user32.ActivateKeyboardLayout(hkl, KLF_REORDER)
    print("Sucesso! Layout Estados Unidos (Internacional) ativado em todas as janelas.")
else:
    print(f"Falha ao carregar layout. Erro: {ctypes.GetLastError()}")

# Listar layouts ativos apos o carregamento
num_layouts = user32.GetKeyboardLayoutList(0, None)
layouts = (ctypes.c_ulong * num_layouts)()
user32.GetKeyboardLayoutList(num_layouts, layouts)

print("\nLayouts ativos agora:")
for i, l in enumerate(layouts):
    print(f"  [{i}] {hex(l)}")
