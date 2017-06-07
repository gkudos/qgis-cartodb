from setuptools import setup
import sys

setup(name='qgis-cartodb',
      author='Javi Santana',
      author_email='info@gkudos.com',
      description='CARTO QGIS Plugin',
      version='0.8.1',
      url='https://github.com/Vizzuality/cartodb',
      packages=['cartodb'],
      test_suite='test.cartodbapi')
