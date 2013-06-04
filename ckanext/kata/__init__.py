"""
Kata extension for CKAN. 

Provides our modified Add Dataset (package) page and contains many other modifications described here. This extension 
contains also jQuery files, custom css (eg. kata.css) and several templates are overwritten from basic CKAN to provide 
the Kata/TTA looks. Note, that some css and template modifications were done in early stage in CSC. Note that during 
the software development there has been a great deal of regression problems in the extension and it might be 
worthwhile remembering this when debugging some random odd bug. 
"""

try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
