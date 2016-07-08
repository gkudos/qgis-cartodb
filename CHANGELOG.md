<a name="0.2.5"></a>
### 0.2.5 (2016-07-08)

#### Fixes

* Fix #44 problems with domain changes.

### 0.2.4 (2016-03-14)

#### Refactoring

* Change 'Add CartoDB Layer' button to layer toolbar on QGIS >= 2.12. (Left side on QGIS).
* Change 'Add SQL CartoDB Layer' button to layer toolbar on QGIS >= 2.12. (Left side on QGIS).

#### Fixes

* Fix #40 error when the layer name contains non-ascii characters

<a name="0.2.3"></a>
### 0.2.3 (2015-10-04)

#### Fixes

* Fix #33 Error updating recently uploaded data

<a name="0.2.2"></a>
### 0.2.2 (2015-09-02)

#### Enhancements

* Change privacy for maps (public checkbox).
* Change some texts.

<a name="0.2.1"></a>
### 0.2.1 (2015-08-19)

#### Enhancements

* Create maps without select layers.
* Add status to upload items.
* Change icons.

#### Fixes

* Fix order layer in maps.
* Fix #30 When you push a new layer to CartoDB, it doesn't register the layer with your current project as being a CartoDB layer.

<a name="0.2.0"></a>
### 0.2.0 (2015-08-10)

#### Enhancements

* Add functionality to Create Map buttons.

#### Fixes

* Fix #25 Error creating map from CartoDB.
* Fix #5 Filter data by attribute or extent.
* Fix problems with SQL layers in maps.
* Fix #31 Style Categorized: The generation of CartoCSS fails if there is data with special characters.
* Remove unnecessary files in the plugin package.

<a name="0.1.9"></a>
### 0.1.9 (2015-07-22)

#### Enhancements

* Default symbology for not supported symbols.
* Add messages for not supported symbols.
* Add uploaded message.
* Change icons.

#### Fixes

* Fix #29 Error updating layer single user account.
* Fix #27 Error getting columns in SQL dialog.


<a name="0.1.8"></a>
### 0.1.8 (2015-07-11)

#### Enhancements

* Remove connection controls in SQL Editor.
* Add composite mode in create maps.
* Add dash style to lines in create maps.
* Add join style to lines in create maps.

<a name="0.1.7"></a>
### 0.1.7 (2015-07-10)

#### Fixes

* Fix #19 Do not allow to edit read-only layers.
* Show owner in shared layers, issue #18.
* Fix #26 Encoding error creating map.


<a name="0.1.6"></a>
### 0.1.6 (2015-06-20)

#### Enhancements

* Remove scroll in user table list.
* Ascending order in user table list.
* Download datasets in spatialite format.

#### Fixes

* Fix #23 Error conecting multiuser account.

<a name="0.1.5"></a>
### 0.1.5 (2015-06-16)

#### New Features

* Upload layers to CartoDB (More formats).
* Create basic visualization. Support:
  * Borders.
  * Fill.
  * Label.

<a name="0.1.4"></a>
### 0.1.4 (2015-06-05)

#### New Features

* Upload layers to CartoDB.

#### Translate

* Add spanish translation.

#### Fixes

* Fix avatar size.
* Fix #21 Insert data without complete fields.
* Enable buttons only if there is at least one created connection.

<a name="0.1.3"></a>
### 0.1.3 (2015-05-24)

#### New Features

* Filter tables by current extent.
* Add more info for table list.
* Use threads for download data.

#### Fixes.

* Fix error at multiusers accounts #15, again.

<a name="0.1.2"></a>
### 0.1.2 (2015-05-07)

#### New Features

* Filter tables by name. Fix #4
* Indicate READ_ONLY tables for multiuser accounts.
* Add unit test to project.
* Add user information at main dialog.
* Load Tables from viz API.
* Paginate tables on scroll.

#### Fixes.

* Fix error at multiusers accounts #15

<a name="0.1.1"></a>
### 0.1.1 (2014-11-27)

* Fix error when repeat layer name at spatialite database.
#### New Features

* Load cartodb layers from SQL Queries.

#### Fixes.

* New connection dialog is now a modal window.

<a name="0.1.0"></a>
### 0.1.0 (2014-09-23)

#### Features

* Add, edit and delete features.
* Add, edit and delete data.
* Manage connection.
