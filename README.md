![Logo](images/logo.jpg?raw=true "QGis CartoDB")
================================================

CartoDB Plugin for QGis.  It allows to view,  create, edit or delete data from  your CartoDB account using your favorite opensource desktop GIS: QGIS.  


## Features

![QGis CartoDB](images/screenshot.png?raw=true "QGis CartoDB")

* Manage CartoDB connections.
* Add CartoDB layers to QGis projects.
* Add features to CartoDB tables.
* Edit data and update CartoDB tables.
* Edit data and update geometries.
* Delete features.

## Supported Versions

Minimum QGIS version:  2.3

## Install

### From QGIS repositories

* Go to "Plugins -> Manage and Install Plugins" 
* Mark "Show also experimental plugins" in "Settings" 
* Search for "CartoDB Plugin" in "Search" 

### From git repository

#### Downloading release code
* Download the code from [here](https://github.com/gkudos/qgis-cartodb/releases/latest)
* Extract from zip file.
* Rename folder to QgisCartoDB
* Copy the plugin folder to $HOME/.qgis2/python/plugins/

#### Cloning repo

* Open a terminal.
* Execute:
    * `git clone https://github.com/gkudos/qgis-cartodb.git`
    * `cd qgis-cartodb`
    * `make install`

#### Enabling plugin

* Open QGIS
* Go to "Plugins"=>"Manage and install plugins"
* Click on "Installed" and enable "CartoDB Plugin"

## Quick Use

After enabled plugin, click on the icon: ![Icon](images/add.png?raw=true "Icon") or on the web menu item "CartoDB Plugin" => "Add CartoDB Layer"

This open dialog:

![Dialog 1](images/dialog1.png?raw=true "Add CartoDB Layer 1")

#### Creating new connection

Click on "New" button.

![Dialog 2](images/dialog2.png?raw=true "New Connection")

Add your CartoDB account. Your api key is in:

    https://[youraccount].cartodb.com/your_apps

Click on "Save" button.

#### Adding CartoDB layer

Select connection and click on "Connect" button.

![Dialog 3](images/dialog3.png?raw=true "Adding layer")

Select any table and click on "OK" button.

Voilá !!!!

![Voilá](images/layer.png?raw=true "Voilá !!!")

## Dependencies

* [CartoDB](https://github.com/Vizzuality/cartodb-python)
* oauth2
* simplejson
* certifi

## Limitations

* Create new tables.
* Add new attributes.
* Get visualizations or CartoCSS styles.

## Help Wanted

Any idea, issue or comment?, Please open an issue with related label. 
Do You want to contribute? Fork this project and get to work. Your time and help is greatly appreciated.

Please check our [Contributing Guide](CONTRIBUTING.md)

## Licence

This plugin is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
