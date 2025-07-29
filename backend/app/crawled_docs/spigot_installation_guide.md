---
url: 
title: Untitled
source: Spigot Installation Guide
game_type: Minecraft
category: Game Server
crawled_at: 2025-07-29T22:14:31.556661
---

# Untitled

**Source:** Spigot Installation Guide  
**Game Type:** Minecraft  
**URL:** 

---

Your name or email address:Do you already have an account?

- No, create an account now.
- Yes, my password is:
- [Forgot your password?](https://www.spigotmc.org/lost-password/)


Stay logged in

# Installation

Mar 12, 2023

- [Page](https://www.spigotmc.org/wiki/spigot-installation/#wikiContent)
- [History](https://www.spigotmc.org/wiki/spigot-installation/#history)
- [Editors](https://www.spigotmc.org/wiki/spigot-installation/#editors)

Installation


- Spigot Installation



A guide



* * *






Spigot is a fork of CraftBukkit with extra optimizations and more features sprinkled on top. Installing it is simple, as it's a drop-in replacement for your typical CraftBukkit JAR.




If you already have CraftBukkit successfully installed, installing Spigot is usually as simple as replacing your server JAR with the new one.




Also, to avoid malicious or old Spigot that opens a large vulnerability for a Minecraft server, you should **NOT** download any Spigot jar files found on Internet. It may be outdated, or can be a trojan sometimes.





The instructions for running and compiling Spigot/CraftBukkit have been changing over the past few months. Please make sure to check out the [BuildTools wiki page](http://www.spigotmc.org/wiki/buildtools/) for the latest compilation instructions.







## Contents



- [Prerequisites](https://www.spigotmc.org/wiki/spigot-installation/#prerequisites)
- [Installation](https://www.spigotmc.org/wiki/spigot-installation/#installation)
- [Windows](https://www.spigotmc.org/wiki/spigot-installation/#windows)
- [Linux](https://www.spigotmc.org/wiki/spigot-installation/#linux)
- [Screen](https://www.spigotmc.org/wiki/spigot-installation/#screen)
- [Mac OS X](https://www.spigotmc.org/wiki/spigot-installation/#mac-os-x)
- [Multicraft](https://www.spigotmc.org/wiki/spigot-installation/#multicraft)
- [Post-Installation](https://www.spigotmc.org/wiki/spigot-installation/#post-installation)
- [Plugins](https://www.spigotmc.org/wiki/spigot-installation/#plugins)

## Prerequisites( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

1. Java compatible with the minecraft version you wanna run (you can check in the [BuildTools Prerequisites](https://www.spigotmc.org/wiki/buildtools/#prerequisites) to check the java version desired)

2. The server jar compiled by following the [BuildTools wiki](http://spigotmc.org/wiki/buildtools) page. (After running BuildTools you will find the Spigot/CraftBukkit server jar files in the same directory)

3. The Spigot/CraftBukkit server jar file copied to a new directory dedicated to your server. (Not the same folder as BuildTools is in!)

## Installation( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

### Windows( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

1. Paste the following text into a text document. Save it as start.bat in the same directory as spigot.jar:
2. Code (example (Unknown Language)):



@echo off


java -Xms#G -Xmx#G -XX:+UseG1GC -jar spigot.jar nogui


pause


    (where # is your allocated server memory in GB)

3. Double click the batch file.

### Linux( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

1. Create a new startup script (start.sh) in the server directory to launch the JAR:




Code (example (Unknown Language)):



#!/bin/sh




java -Xms#G -Xmx#G -XX:+UseG1GC -jar spigot.jar nogui




    (where # is your allocated server memory in GB)
2. Open your terminal and execute the following in the directory:




Code (makeexecutable (Unknown Language)):



chmod +x start.sh

3. Run your start up script:

4. Code (runcommand (Unknown Language)):



./start.sh


#### Screen( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

If you want to start the server using screen and also support the /restart command, you can use this script (start.sh):

Code (example (Unknown Language)):

#!/bin/sh

screen -d -m -S "name\_of\_screen\_here" java \[your startup flags here\] -jar spigot.jar nogui

Note that the -d -m options are required for /restart to work.

### Mac OS X( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

1. Create a new startup script (start.command) to launch the JAR in the server directory:




Code (example (Unknown Language)):



#!/bin/sh




cd "$( dirname "$0" )"


java -Xms#G -Xmx#G -XX:+UseG1GC -jar spigot.jar nogui




    (where # is your allocated server memory in GB)

2. Open Terminal and type into it: (Don't hit enter!)




Code (Text):



chmod a+x

3. Drag your startup script file into the Terminal window. (Be sure to put a space between chmod a+x and your startup script!)

4. Double click your startup script.

### Multicraft( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

Depending on your Minecraft host's configuration, you will have two ways to enable the use of Spigot through Multicraft.

- If there's already an option for Spigot in the JAR file selection menu, you can simply select it and restart your server upon save. However, this may not be recommended if your host does not keep up to date with the latest Spigot builds.
- If you have access to upload custom server JARs (FTP), download the Spigot JAR and enter in the name of the file via the JAR file input box located on the index of the panel. Some hosts may require you to rename your JAR to a specific name (like _custom.jar_) and then select it from the dropdown menu.
- If your personal server you have root to, place the [spigot.jar.conf](http://www.multicraft.org/download/conf?file=spigot.jar.conf) in your daemon jar directory, then update the jar using the admin panel. The jar should now be the clients jar selection.

## Post-Installation( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

After the Spigot.jar has been run the first time, folders and config files will be created. You will need to edit these config files to have the server work properly in your environment.

You can access further instructions for these files here:

- [server.properties](http://minecraft.gamepedia.com/Server.properties)

- [bukkit.yml](http://wiki.bukkit.org/Bukkit.yml)

- [spigot.yml](https://www.spigotmc.org/wiki/spigot-configuration/)

- [Server Icons](https://www.spigotmc.org/wiki/server-icon/)

If the server is working incorrectly, be sure you have port forwarded and you have followed the steps closely. If you are having issues, you can create a help thread in the [**Spigot forum**](http://www.spigotmc.org/forums/help.40/) or come chat with us in [Discord](https://www.spigotmc.org/link-forums/discord.95/) or **[IRC.](http://www.spigotmc.org/pages/irc/)**

Due to the inefficiency of the Windows and Mac OS X kernels (e.g. high overhead, poor resource allocation, and such), it is not recommended to host on these platforms for a serious/dedicated server.

## Plugins( [top](https://www.spigotmc.org/wiki/spigot-installation/\#wikiPage))

In practically all cases, your Bukkit plugins will likely work on Spigot, unless the author of one of your plugins uses certain internal CraftBukkit/Minecraft code.

Check out our [**Resources section**](http://www.spigotmc.org/resources/) or [**BukkitDev**](http://dev.bukkit.org/bukkit-plugins/) to find a wide variety of plugins, that range from helping with administration to adding completely new gamemodes. If you cannot find anything there you could request a plugin to be made on **[Spigot's Services & Recruitment forum](http://www.spigotmc.org/forums/hiring-developers.55/)** or **[Bukkit's Plugin Requests Forum](http://forums.bukkit.org/forums/plugin-requests.13/)**. Please be sure to follow the guidelines on how to set up a request.

You can add your plugins by dropping the JAR file into your _plugins_ folder in your server directory and restarting the server. If it does not work or if you see errors seek help on the **[Spigot Forum](http://www.spigotmc.org/forums/help.40/)**

- Loading...
- Loading...


(1896516 Views)


Last Modified: Mar 12, 2023 at 2:22 AM



[XenCarta PRO](http://xenforo.com/community/resources/1690/)
© Jason Axelrod from [8WAYRUN.COM](http://8wayrun.com/)

←

→

SunMonTueWedThuFriSat

### Home

Quick Links

- [Recent Posts](https://www.spigotmc.org/find-new/posts)
- [Recent Activity](https://www.spigotmc.org/recent-activity/)

### Forums

Quick Links

- [Search Forums](https://www.spigotmc.org/search/?type=post)
- [Recent Posts](https://www.spigotmc.org/find-new/posts)

### Resources

Quick Links

- [Search Resources](https://www.spigotmc.org/search/?type=resource_update)
- [Most Resources](https://www.spigotmc.org/resources/authors)
- [Latest Reviews](https://www.spigotmc.org/resources/reviews)

### Useful Searches

- [Recent Posts](https://www.spigotmc.org/find-new/posts?recent=1)

### Team

Quick Links

- [Administrator](https://www.spigotmc.org/XenStaff/#Administrator)
- [Moderator](https://www.spigotmc.org/XenStaff/#Moderator)
- [Sponsor](https://www.spigotmc.org/XenStaff/#Sponsor)
- [Developer](https://www.spigotmc.org/XenStaff/#Developer)
- [Wiki Team](https://www.spigotmc.org/XenStaff/#Wiki%20Team)
- [Services Staff](https://www.spigotmc.org/XenStaff/#Services%20Staff)
- [Junior Mod](https://www.spigotmc.org/XenStaff/#Junior%20Mod)
- [Resource Staff](https://www.spigotmc.org/XenStaff/#Resource%20Staff)
- [IRC Staff](https://www.spigotmc.org/XenStaff/#IRC%20Staff)

### Downloads

Quick Links

- [Spigot / BuildTools](https://www.spigotmc.org/link-forums/spigot-buildtools.88/)
- [BungeeCord](https://www.spigotmc.org/link-forums/bungeecord.28/)
- [Jenkins](https://www.spigotmc.org/link-forums/jenkins.29/)

### Members

Quick Links

- [Notable Members](https://www.spigotmc.org/members/)
- [Current Visitors](https://www.spigotmc.org/online/)
- [Recent Activity](https://www.spigotmc.org/recent-activity/)
- [New Profile Posts](https://www.spigotmc.org/find-new/profile-posts)

- [Wiki Index](https://www.spigotmc.org/wiki/)
- [Page List](https://www.spigotmc.org/wiki/special/pages)
