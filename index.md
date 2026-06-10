# AES PA system
---

## Setting Up

What you need:
- Raspberry Pi Model 3B
- 32GB microSD card
- Raspberry Pi Power Supply

### Raspberry Pi Imager
Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) if you have not done so.

### Flashing OS into Raspberry Pi Board
1. Insert the microSD card into your computer and launch **rpi-imager.exe**.
2. Under **Device**, select the correct Raspberry Pi Model (**Raspberry Pi 3**)
3. Under **OS**, select **Raspberry Pi OS (64-bit)**
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

Upon completing all of the steps above, select **Write** to start flashing the OS into the microSD card. This process will take a while.

### Script Set Up
