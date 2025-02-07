#!/usr/bin/python3
"""
Module for working with DNVGL Application Version Manager
"""
import logging
import os
from xml.dom import minidom
from collections import OrderedDict

# configure logger
logger = logging.getLogger(__name__)


def exe_path(appname, version=None, appverxml=None):
    """
    Return absolute path to DNV GL application executable

    Parameters
    ----------
    appname : str
        Application name
    version : str, optional
        Application version, by default the application marked as default in
        Application Version Manager is used.
    appverxml : str, optional
        XML file listing application-versions. By default the file in APPDATA is applied.

    Returns
    -------
    str
        Absolute path to application executable

    Notes
    -----
    Based on parsing the 'ApplicationVersions.xml' in the AppData directory
    on your local machine.

    """
    # all registered applications
    try:
        appdata = registered_applications(appverxml=appverxml)
    except FileNotFoundError:
        logger.error(f"Failed to load application version data", exc_info=True)
        raise

    # get app data
    app = appdata.get(appname.lower())
    if app is None:
        logger.warning(f"Application '{appname}' is not registered in Application Version Manager.", exc_info=True)
        return None

    if version is not None:
        # requested specific version
        try:
            appversion = app.get(version.lower())
        except KeyError:
            logger.warning(f"Version '{version}' of application '{appname}' is not registered in Application "
                           f"Version Manager.")
            return None
        else:
            if appname.lower() == 'simo':
                path = f"{appversion.get('installdir')}simo\\bin\\rsimo.exe"
            elif appname.lower() == 'riflex':
                path = f"{appversion.get('installdir')}Riflex\\bin\\riflex.bat"
            else:
                path = appversion.get('exepath')
            versionnumber = appversion.get('versionnumber')

    else:
        # use default version
        path, versionnumber = None, None
        for _, appversion in app.items():
            if appversion.get('default'):
                if appname.lower() == 'simo':
                    path = f"{appversion.get('installdir')}simo\\bin\\rsimo.exe"
                elif appname.lower() == 'riflex':
                    path = f"{appversion.get('installdir')}Riflex\\bin\\riflex.bat"
                else:
                    path = appversion.get('exepath')
                versionnumber = appversion.get('versionnumber')

        if path is None:
            logger.warning(f"There is no default version registered for application '{appname}' in Application "
                           f"Version Manager.")
            return None

    # verify that the executable path exists
    if not os.path.exists(path):
        logger.warning(f"The executable path '{path}' for application/version {appname}/{versionnumber} does not exist.")
        return None
    else:
        return f'"{path}"'



def installation_path(appname, version=None, appverxml=None):
    """
    Return installation path to DNV GL application

    Parameters
    ----------
    appname : str
        Application name
    version : str, optional
        Application version, by default the application marked as default in
        Application Version Manager is used.
    appverxml : str, optional
        XML file listing application-versions. By default the file in APPDATA is applied.

    Returns
    -------
    str
        Absolute path to installation directory

    Notes
    -----
    Based on parsing the 'ApplicationVersions.xml' in the AppData directory
    on your local machine.

    """
    # all registered applications
    try:
        appdata = registered_applications(appverxml=appverxml)
    except FileNotFoundError:
        logger.error(f"Failed to load application version data", exc_info=True)
        raise

    # get app data
    app = appdata.get(appname.lower())
    if app is None:
        logger.warning(f"Application '{appname}' is not registered in Application Version Manager.", exc_info=True)
        return None


    if version is not None:
        # requested specific version
        appversion = app.get(version.lower())
        if appversion is None:
            logger.warning(f"Version '{version}' of application '{appname}' is not registered in Application "
                           f"Version Manager.")
            return None
        else:
            path = appversion.get('installdir')
            versionnumber = appversion.get('versionnumber')

    else:
        # use default version
        path, versionnumber = None, None
        for _, appversion in app.items():
            if appversion.get('default'):
                path = appversion.get('installdir')
                versionnumber = appversion.get('versionnumber')

        if path is None:
            logger.warning(f"There is no default version registered for application '{appname}' in Application "
                           f"Version Manager.")
            return None

    # verify that the executable path exists
    if not os.path.exists(path):
        logger.warning(f"The path '{path}' for application/version {appname}/{versionnumber} does not exist.")
        return None
    else:
        return f'"{path}"'


def registered_applications(appverxml=None):
    """
    Get all applications registered in Application Version Manager

    Parameters
    ----------
    appverxml : str, optional
        XML file listing application-versions. By default the file in APPDATA is applied.

    Returns
    -------
    OrderedDict
        Registered applications and versions
    """
    # Try to locate the ApplicationVersions.xml in appdata, if it is not specified
    if appverxml is None:
        try:
            appverxml = os.path.join(os.getenv('appdata'), 'DNVGL', 'ApplicationVersionManager',
                                     'ApplicationVersions.xml')
        except TypeError:
            logger.error("No environmental variable called 'APPDATA'. Unable to find 'ApplicationVersions.xml'.")
            raise FileNotFoundError("No environmental variable called 'APPDATA'. Unable to find "
                                    "'ApplicationVersions.xml'.")

    # Verify the existence of the xml file
    if os.path.exists(appverxml):
        logger.debug(f"Using the xml file '{appverxml}'.")
    else:
        logger.error(f"The xml file '{appverxml}' does not exist.")
        raise FileNotFoundError(f"The xml file '{appverxml}' does not exist.")

    # parse document tree with application information
    try:
        apps = minidom.parse(appverxml).getElementsByTagName('Application')
    except (FileNotFoundError, AttributeError) as err:
        logger.error(f"Failed to parse the 'ApplicationVersion.xml'. The file does not exist.", exc_info=True)
        raise FileNotFoundError("Failed to parse the 'ApplicationVersion.xml'. The file does not exist.") from err

    # find specified application and version
    data = OrderedDict()
    for app in apps:
        appname = app.getAttribute('Name').lower()                  # lowercase for increased robustness
        versions = app.getElementsByTagName('Version')
        appdata = OrderedDict()
        for version in versions:
            vnumber = version.getAttribute('VersionNumber').lower() # lowercase for increased robustness
            exepath = version.getAttribute('ExeFilePath')
            installdir = version.getAttribute('InstallDir')
            platform = version.getAttribute('Platform')
            producttype = version.getAttribute('ProductType')
            category  = version.getAttribute('Category')
            isdefault = True if version.getAttribute('IsDefault').lower() == 'true' else False
            appdata[vnumber] = OrderedDict(
                versionnumber=vnumber,
                exepath=exepath,
                default=isdefault,
                installdir=installdir,
                platform=platform,
                producttype=producttype,
                category=category
            )
            logger.debug(f"Application '{appname}' - version '{vnumber}'- is default {isdefault}")

        # add application data dict
        data[appname] = appdata

    return data

