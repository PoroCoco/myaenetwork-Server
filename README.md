This is code for the website myaenetwork.ovh that lets users interact with their in-game Minecraft Applied Energistics 2 network from the web. 

The Flask framework is used in combinaison to Jinja to generate the templates for front-end pages. 
It interacts with the OpenComputers computers using TCP Sockets with a custom communication protocol available in the poroNet.py file.
The database is an oracle db that stores the credentials of the accounts. 

# Running your private version
Even though the website is publicly available you may want to run your own and make some tweaks. To do this you'll need to update the config.json and if you don't use a oracle database then you'll also have to change the database module to handle your own.

# Overview of the architecture 

Here's a quick diagram showing the interactions between the differents part of program.

![myaenetwork_diagram](https://github.com/PoroCoco/myaenetwork-Server/assets/48033370/f8d64065-3927-434a-adb9-da6afba10179)
