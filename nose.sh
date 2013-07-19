if [ "$1" == "selenium" ]
then
	echo "Running selenium tests"
	xvfb-run nosetests ckanext-kata/ckanext/kata/testselenium
else
	echo "Running normal tests"
	nosetests --ckan --with-pylons=ckanext-kata/test-core.ini ckanext-kata/ckanext/kata/tests --logging-filter=kata
fi
