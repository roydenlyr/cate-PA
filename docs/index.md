# AES PA system
---

## Setting Up

What you need:
- Raspberry Pi Model 3B
- 32GB microSD card
- Raspberry Pi Power Supply
- Monitor Screen
- HDMI Cable
- Keyboard and Mouse (USB-A)

### Raspberry Pi Imager
Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) if you have not done so.

### Flashing OS into Raspberry Pi Board
1. Insert the microSD card into your computer and launch **rpi-imager.exe**.
2. Under **Device**, select the correct Raspberry Pi Model (**Raspberry Pi 3**).
3. Under **OS**, select **Raspberry Pi OS (64-bit)**.
4. Under **Storage**, select the microSD card.


#### Customisation
1. Under **Hostname**, name the Pi in accordance to this format: cate-PA-{*Station Name Abbreviation*}
    >Example: For Fire Station 1, hostname will be **cate-PA-FS1**
2. Under **Localisation**, ensure settings are as follows:
   1. Capital City: **Singapore**
   2. Time Zone: **Asia/Singapore**
   3. Keyboard Layout: **us**
3.  Under **User**, username and password should align with CATE's standard.
4.  Under **Wi-Fi**, enter the SSID and credentials for the network you are currently in.
    > NOTE: Ensure you have stable internet connection.
5. Under **Remote Access**, select **enable SSH** and choose **use password authentication** as the *Authentication Mechanism*.
6. Under **Raspberry Pi Connect**, do not enable this feature.

Upon completing all of the steps above, select **Write** to start flashing the OS into the microSD card. This process will take a while (~10 min).

### Power On
---

Insert the microSD card into the Raspberry Pi and connect the power supply. There are 2 LED indicators on the Raspberry Pi (beside power supply port).
> Solid Green: Raspberry Pi is booting up
> Slow Flashing Green: Raspberry Pi is running

1. Connect the monitor, keyboard and mouse to the Raspberry Pi.
2. Once the Desktop is shown on the monitor, check for Wi-Fi connection (top right corner)
> NOTE: Connect to Wi-Fi if not connected

### Script Downloading
---
Before proceeding to the next steps, ensure Wi-Fi is connected.

Open terminal (top left corner) and run this command:
```
git clone https://github.com/roydenlyr/cate-PA.git
cd cate-PA
chmod +x setup.sh
./setup.sh
```
``setup.sh`` is a shell script that will install all relevant resources required for the system to run. This process will take a while (~5 min).

Once the script has completed, you will be asked to set up a password for the network folder. Run this command:
```
sudo smbpasswd -a cate
```

> Note: the command *sudo* gives user elevated privilege. Terminal may prompt you for the password. This is the password you have configured under [CUSTOMISATION (point 3)](#customisation)

You will be prompted to enter a password. **Password should conform to CATE standard**.
> NOTE: When entering the password into terminal, password will not be shown. Press ENTER once you have keyed in the password. You will be required to enter the password again.

### Station Configuration
---
To configure the Raspberry Pi, you will have to make changes to the configuration file ``config.py``

1. From Desktop, open **Files** (top right corner).
2. Open **cate-PA &rarr; src &rarr; ``config.py``**

There are 7 variables within ``config.py``. You should only change these 3 variables:
- STATION_ID
- NUMBER_OF_STATIONS
- STATIONS

``STATION_ID`` refers to the station where the current Raspberry Pi will operate. It should follow the same abbreviation given in [hostname](#customisation).
> Example: Given hostname cate-PA-FS1, STATION_ID = FS1. Do not include 'cate-PA'

``NUMBER_OF_STATIONS`` refers to the total number of Raspberry Pi being deployed, including the one you are setting up right now. Update this value accordingly.

``STATIONS`` provides a list of IP address of all stations in the format:
```
'{STATION_ID}': ('{IP ADDRESS}', TCP_PORT),
```
Add all existing stations accordingly.
> REMINDER: Always add the last **comma** from the command shown above.

> WARNING: Ensure there are no typo errors in the configuration file.

Once completed, press ``CTRL + S`` to save the file and close the window.

### Reboot
The Raspberry Pi configuration and set up is now complete. Reboot the system for all changes to take effect. To reboot:
```
sudo reboot
```