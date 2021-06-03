#!/bin/bash

# Clean build folder
rm -rf build
rm -rf dist

# Generate binary
pyinstaller --onefile main.py

# Stop services
sudo systemctl stop telegram-bot@1895979877:AAEXbQIIe17tvw355wjIyXdPg9TFyOW9W38.service

# Copy to /usr/bin
sudo cp dist/main /usr/bin/telegram-bot
