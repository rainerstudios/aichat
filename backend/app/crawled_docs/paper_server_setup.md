---
url: 
title: Untitled
source: Paper Server Setup
game_type: Minecraft
category: Game Server
crawled_at: 2025-07-29T22:14:25.490730
---

# Untitled

**Source:** Paper Server Setup  
**Game Type:** Minecraft  
**URL:** 

---

[Skip to content](https://docs.papermc.io/paper/getting-started/#_top)

# Getting started

## Requirements

[Section titled “Requirements”](https://docs.papermc.io/paper/getting-started/#requirements)

| Paper Version | Recommended Java Version |
| --- | --- |
| 1.8 to 1.11 | Java 8 |
| 1.12 to 1.16.4 | Java 11 |
| 1.16.5 | Java 16 |
| 1.17.1-1.18.1+ | Java 21 |

## Downloading Paper

[Section titled “Downloading Paper”](https://docs.papermc.io/paper/getting-started/#downloading-paper)

Paper provides runnable server JARs directly from our
[website’s downloads page](https://papermc.io/downloads).

Click on the build number to download a file.

## Running the server

[Section titled “Running the server”](https://docs.papermc.io/paper/getting-started/#running-the-server)

To run the server you will need to either create a startup script
or run a command in your terminal.

You can generate a startup script using our [Startup Script Generator](https://docs.papermc.io/misc/tools/start-script-gen).
You can also obtain the optimized terminal command to run the server there.

If you’re just looking for a short command:

```

java -Xms4G -Xmx4G -jar paper.jar --nogui
```

Ensure you navigated your terminal to the directory of your server
and that you have replaced `paper.jar` with the name of the JAR you have downloaded.

The amount of RAM can be set by changing the numbers in the `Xmx` and `Xms` arguments.
`--nogui` disables Vanilla’s GUI, so you don’t get double interfaces when using the command line.

To configure your server, see the [Global Configuration](https://docs.papermc.io/paper/reference/global-configuration) and
[Per World Configuration](https://docs.papermc.io/paper/reference/world-configuration) pages.

## Updating the server

[Section titled “Updating the server”](https://docs.papermc.io/paper/getting-started/#updating-the-server)

Updating Paper is simple! See our [Update Tutorial](https://docs.papermc.io/paper/updating) for more information.

## Migrating to Paper

[Section titled “Migrating to Paper”](https://docs.papermc.io/paper/getting-started/#migrating-to-paper)

### From Vanilla

[Section titled “From Vanilla”](https://docs.papermc.io/paper/getting-started/#from-vanilla)

Migrating from Vanilla is easy, but there are some differences, namely in world saves. Paper (and
CraftBukkit and Spigot) separate out each dimension of a world (nether, the end, etc.) into separate
world folders.

Paper will handle this conversion for you automatically. No additional consideration is required.

### From CraftBukkit or Spigot

[Section titled “From CraftBukkit or Spigot”](https://docs.papermc.io/paper/getting-started/#from-craftbukkit-or-spigot)

Paper is a drop in replacement for both CraftBukkit and Spigot, you don’t need to make any changes.

## Next steps

[Section titled “Next steps”](https://docs.papermc.io/paper/getting-started/#next-steps)

Take a look at our [Next Steps](https://docs.papermc.io/paper/next-steps) guide to get your server up and running with the best performance and
features.

Copyright © 2025 PaperMC and contributors. Built with [Starlight](https://starlight.astro.build/).

This website is not an official Minecraft website and is not associated with Mojang Studios or Microsoft. All
product and company names are trademarks or registered trademarks of their respective holders. Use of these names
does not imply any affiliation or endorsement by them.
