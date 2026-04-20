@echo off
echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing setuptools and wheel...
pip install setuptools wheel

echo Installing requirements...
pip install -r requirements.txt

echo Installing the package in development mode...
pip install -e .

echo Installation complete!
echo Please activate the virtual environment using: .venv\Scripts\activate.bat

echo Starting the server...
python run.py 