# fix_bcrypt.py
import pip
import subprocess
import sys

print("Fixing bcrypt and passlib compatibility...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "bcrypt==3.2.0"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "passlib==1.7.4"])
print("Fixed! Please restart the application.")