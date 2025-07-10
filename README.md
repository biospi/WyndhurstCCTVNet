# Wyndhurst Farm CCTV Network Utils

This project contains the sources for managing the Wyndhurst cctv network. Including the scripts for:
* downloading videos from the Hanwha cameras
* Transferring videos from the farm PC to the Workstation
* Sending email report for storage and farm overview visualisation
* Video postprocessing (crop)

## Prerequisite
Existing configured Workstation. Follow the guide to install a new workstation.

## How To Install
 
1) Clone the repository.

```bash
git clone https://github.com/biospi/WyndhurstCCTVNet.git
```
2) Change directory
```bash
cd Wyndhurst/
```
3) Create python virtual environment 
```bash
python3 -m venv venv
```
4) Activate the environment
```bash
source venv/bin/activate
```
5) Install dependencies 
```bash
pip install --upgrade pip
make environment
```

## How to use
A config file named 'config.cfg' containing the credentials is required and need to be placed in the source directory root, 
the file should be edited and formatted as below:
```bash
[SSH]
farm_server_user = username
farm_server_password = password
[EMAIL]
receiver_0 = email
receiver_1 = email
sender = email
password = password
[AUTH]
password_hikvision = password
password_hanwha = password
login = user

```
To start the video recording across the farm, and start error and storage reporting:
```bash
python start_recording.py
```


## Collaborators
[![Bristol Veterinary School](http://www.bristol.ac.uk/media-library/protected/images/uob-logo-full-colour-largest-2.png)](http://www.bristol.ac.uk/vetscience/)