case "$1" in
	selenium )
		echo "Running selenium tests";
		xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium;
		;;
	unit )
		echo "Running unit tests";
		nosetests --ckan --with-pylons=ckanext-kata/test-core.ini ckanext-kata/ckanext/kata/tests --logging-filter=kata;
		;;
	* )
		echo "Accepted parameters are 'selenium' and 'normal' to run only Selenium or unit tests.";
		echo "Running all tests\n";

		nosetests --ckan --with-pylons=ckanext-kata/test-core.ini ckanext-kata/ckanext/kata/tests --logging-filter=kata;
		xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium;
		
		# xvfb-run nosetests --ckan --with-pylons=ckanext-kata/test-core.ini ckanext-kata/ckanext/kata/ --logging-filter=kata;
		;;
esac
