# Makefile for CartoDB Plugin plugin
UI_FILES = ui/UI_CartoDBPlugin.py ui/NewConnection.py

RESOURCE_FILES = resources.py

default: compile

compile: $(UI_FILES) $(RESOURCE_FILES)

%.py : %.qrc
	pyrcc4 -o $@  $<

%.py : %.ui
	pyuic4 -o $@ $<

install:
	mkdir /home/$(USER)/.qgis2/python/plugins/QgisCartoDB/
	cp -r ./* /home/$(USER)/.qgis2/python/plugins/QgisCartoDB/

clean:
	rm -R /home/$(USER)/.qgis2/python/plugins/QgisCartoDB/
