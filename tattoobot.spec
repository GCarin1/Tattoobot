# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file para o TattooBot Desktop.
#
# Build:
#   pyinstaller tattoobot.spec --clean --noconfirm
#
# Resultado: dist/TattooBot/TattooBot.exe (Windows)
#
# Para gerar um unico .exe use:
#   pyinstaller tattoobot.spec --clean --noconfirm --onefile
# (mais lento pra iniciar, mas um unico arquivo distribuivel)

from pathlib import Path

import customtkinter

# Diretorios
project_root = Path(SPECPATH).resolve()
ctk_path = Path(customtkinter.__file__).parent

block_cipher = None


# Tudo do CustomTkinter precisa ser empacotado (temas, fontes, assets)
ctk_data = [
    (str(ctk_path / "assets"), "customtkinter/assets"),
]


# Arquivos de dados do projeto
project_data = []
settings_file = project_root / "settings.json"
if settings_file.exists():
    project_data.append((str(settings_file), "."))

# Cria data/ empty se nao existir - PyInstaller exige diretorio existente
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)


a = Analysis(
    ['gui_main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=ctk_data + project_data,
    hiddenimports=[
        # Garantir que todos os modulos do projeto vao junto
        'gui',
        'gui.app',
        'gui.theme',
        'gui.async_worker',
        'gui.pages.base',
        'gui.pages.home',
        'gui.pages.settings',
        'gui.pages.engagement',
        'gui.pages.caption',
        'gui.pages.ideas',
        'gui.pages.spy',
        'gui.pages.compare',
        'gui.pages.growth',
        'gui.pages.evaluate',
        'gui.widgets.cards',
        'gui.widgets.console_output',
        'modules.engagement',
        'modules.caption',
        'modules.content_ideas',
        'modules.competitor_spy',
        'modules.profile_comparator',
        'modules.growth_tracker',
        'modules.tattoo_evaluator',
        'modules.ollama_client',
        'modules.scraper',
        'utils.display',
        'utils.storage',
        'config',
        # Dependencias que as vezes nao sao detectadas
        'customtkinter',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Economiza tamanho removendo coisas pesadas que nao usamos
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TattooBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # --windowed: nao abre console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "gui" / "assets" / "icon.ico") if (project_root / "gui" / "assets" / "icon.ico").exists() else None,
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TattooBot',
)
