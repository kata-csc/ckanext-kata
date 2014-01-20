case "$1" in
	selenium )
		echo "Running normal tests and selenium tests";
		nosetests --ckan --with-pylons=ckanext-kata/test-core.ini ckanext-kata/ckanext/kata/tests --logging-filter=ckanext.kata --logging-level=CRITICAL;
		xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium;
		;;
	* )
		echo "Accepted parameter is 'selenium' to run Selenium tests after normal tests.";
		echo "Running normal tests";

		nosetests --ckan --with-pylons=ckanext-kata/test-core.ini ckanext-kata/ckanext/kata/tests --logging-filter=ckanext.kata --logging-level=CRITICAL;
		;;
esac
