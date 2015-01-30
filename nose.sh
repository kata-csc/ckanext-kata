#!/bin/sh
case "$1" in
	selenium )
		echo "Running normal tests and selenium tests";
		nosetests --ckan --with-pylons=ckanext-kata/test-core.ini ckanext-kata/ckanext/kata/tests --logging-clear-handlers --logging-filter=ckanext
		xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium;
		;;
	* )
		echo "Accepted parameter is 'selenium' to run Selenium tests after normal tests.";
		echo "Running normal tests";

		nosetests --ckan --with-pylons=ckanext-kata/test-core.ini ckanext-kata/ckanext/kata/tests --logging-clear-handlers --logging-filter=ckanext
		;;
esac
