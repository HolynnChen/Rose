__all__=['ftpmanager']
from . import ftpmanager
from rose import gb
import importlib
importlib.reload(ftpmanager)
gb.addClass(ftpmanager.ftpmanager)