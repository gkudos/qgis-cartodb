# Makefile for CartoDB Plugin plugin

#Add iso code for any locales you want to support here (space separated)
LOCALES = es

PLUGINNAME = QgisCartoDB

EXTRAS = icon.png metadata.txt

UI_FILES = ui/UI_CartoDBPlugin.py ui/NewConnection.py

RESOURCE_FILES = resources.py

RESOURCE_SRC=$(shell grep '^ *<file' resources.qrc | sed 's@</file>@@g;s/.*>//g' | tr '\n' ' ')

QGISDIR=.qgis2

PLUGIN_UPLOAD = ./plugin_upload.py

default: compile

compile: $(UI_FILES) $(RESOURCE_FILES)

%.py : %.qrc $(RESOURCES_SRC)
	pyrcc4 -o $@  $<

%.py : %.ui
	pyuic4 -o $@ $<

install: transcompile compile
	@echo
	@echo "-------------------------------------------"
	@echo "Installing plugin to your .qgis2 directory."
	@echo "-------------------------------------------"
	rm -f $(PLUGINNAME).zip
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -r ./* $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	rm -R $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/scripts
	@echo " "

uninstall:
	@echo
	@echo "-----------------------------------------------"
	@echo "Uninstalling plugin from your .qgis2 directory."
	@echo "-----------------------------------------------"
	rm -f -R $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	@echo " "

transcompile:
	@echo
	@echo "----------------------------------------"
	@echo "Compiled translation files to .qm files."
	@echo "----------------------------------------"
	@chmod +x scripts/compile-strings.sh
	@scripts/compile-strings.sh $(LOCALES)

transclean:
	@echo
	@echo "------------------------------------"
	@echo "Removing compiled translation files."
	@echo "------------------------------------"
	rm -f i18n/*.qm


dclean:
	@echo
	@echo "-----------------------------------"
	@echo "Removing any compiled python files."
	@echo "-----------------------------------"
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname "*.pyc" -delete
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname ".zip" -delete
	rm -f $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/db/database.sqlite


zip: install dclean
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	# The zip target deploys the plugin and creates a zip file with the deployed
	# content. You can then upload the zip file on http://plugins.qgis.org
	rm -f $(PLUGINNAME).zip
	cd $(HOME)/$(QGISDIR)/python/plugins; zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)

upload: zip
	@echo
	@echo "-------------------------------------"
	@echo "Uploading plugin to QGIS Plugin repo."
	@echo "-------------------------------------"
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

clean:
	@echo
	@echo "------------------------------------"
	@echo "Removing uic and rcc generated files"
	@echo "------------------------------------"
	rm -f $(UI_FILES) $(RESOURCE_FILES)
