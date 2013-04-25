"""
A simple auth handler for Google App Engine supporting 
OAuth 1.0a, 2.0 and OpenID.
"""

__version__ = '0.1.4'
__license__ = "MIT"
__author__ = "Alex Vagin (http://alex.cloudware.it)"

__all__ = []

from handler import *
__all__ += handler.__all__
