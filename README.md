![Logo](images/logo.png?raw=true "QGis CartoDB")
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

Coming soon

### From git repository

#### Downloading code
* Download the code from [Here](https://github.com/gkudos/qgis-cartodb/archive/master.zip)
* Extract from zip file.
* Copy the plugin folder to $HOME/.qgis2/python/plugins/

#### Cloning repo

* Open a terminal
* Execute `cd $HOME/.qgis2/`
* Execute `git clone https://github.com/gkudos/qgis-cartodb.git QgisCartoDB`

#### Enabling plugin

* Open QGIS
* Go to "Plugins"=>"Manage and install plugins"
* Click at "Installed" and enable "CartoDB Plugin"

## Quick Use

After enabled plugin, click at the icon: ![Icon](images/icon.png?raw=true "Icon") or at the web menu item "CartoDB Plugin" => "Add CartoDB Layer"

This open dialog:

![Dialog 1](images/dialog1.png?raw=true "Add CartoDB Layer 1")

#### Creating new connection

Click in "New" buttom.

![Dialog 2](images/dialog2.png?raw=true "New Connection")

Add your CartoDB account. Your api key is in:

    https://[youraccount].cartodb.com/your_apps

Click in "Save" button.

#### Adding CartoDB layer

Select connection and click in "Connect" button.

![Dialog 3](images/dialog3.png?raw=true "Adding layer")

Select any table and click in "OK" button.

Voilá !!!!

![Voilá](images/layer.png?raw=true "Voilá !!!")

## Limitations

* Create new tables.
* Add new attributes.
* Get visualizations or cartoCSS styles.

## Help Wanted

Any idea, any issue, any comment, Open an issue labeling with respective. You want to contribute? Fork this project and get to work. All help is welcomed.

Check [Contributing Guide](CONTRIBUTING.md)

## Licence

This plugin is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
