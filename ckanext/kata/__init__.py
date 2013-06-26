"""
Kata extension for CKAN. 

Provides modified Add Dataset (package) page and other modifications. This extension contains also jQuery files, 
custom css (eg. kata.css) and several templates are overwritten from basic CKAN to provide the Kata/TTA looks. 
"""

try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
