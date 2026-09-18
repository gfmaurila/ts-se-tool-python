# Architecture

Camadas alvo: `core` (SII, profiles, saves, cloning, backup), `application` (use cases), `infrastructure` (filesystem/decoder/runtime resources) e `desktop` (PySide6).

A GUI não acessa arquivos SII diretamente. Escrita passa por use case transacional. O decoder é uma porta substituível. Recursos empacotados devem ser acessados por helper que funcione em desenvolvimento e no PyInstaller one-file (`sys._MEIPASS`).
