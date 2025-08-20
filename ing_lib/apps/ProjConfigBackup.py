"""
This script backs up the project configuration content from an Ingenium server to a local file

Authors:
    * Chris Swan (christopher.a.swan@jpl.nasa.gov)
"""

##################################################### Imports ######################################################
import logging
from logs import init_console_logger
init_console_logger(logging.INFO)

#from common import *
import common
from project_config import get_dictionary_versions,get_dictionary,get_custom_scripts,get_vnv_vis,get_dictionary_element
import argparse
import getpass
import urllib3
import json


##################################################### Functions ######################################################

logger = logging.getLogger(__name__)

def get_input(args=[]):
    """
    This function gathers inputs for the Project Configuration Backup Script

    Parameters
    --------
    args
        list of input arguments. Used when this is called from another Python module.

    Returns
    -------
        inputs: object
            Argparse input object
    """

    parser = argparse.ArgumentParser(
        description='This script backs up Ingenium project configuration information.',
        prog='Ingenium Backup Project Config',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('server', type=str,
                        help='Full Path to Ingenium Server (e.g. https://ingenium-sample_project.jpl.nasa.gov')
    parser.add_argument('api_version', type=str,
                        help='Version of the API in use by the server', choices=['v3','v4'])
    parser.add_argument('file_output', type=str,
                        help='Full path and file name of the backup project configuration file.')
    parser.add_argument('--debug', action='store_true', help='Enables debug logging.')
    parser.add_argument('--username', type=str,
                        help='Optional input to use a different username to login to Ingenium server.')
    parser.add_argument('--ignore_ssl_error', action='store_true', help='Ignore SSL verification error')
    parser.add_argument('--ssl_ca_bundle', type=str,
                        help='Path to the SSL CA bundle. If provided, this will override ignore_ssl_error.')
    parser.add_argument('--rsa', action='store_true',
                        help='Uses RSA Two Factor Authentication (username/passcode) to authenticate.')
    parser.add_argument('--filter_retired', action='store_true', default=True,
                        help='Filters dictionaries based on status and ignores RETIRED dictionaries.')

    if len(args) > 0:
        inputs = parser.parse_args(args)
    else:
        inputs = parser.parse_args()

    # Setup debug logging (if desired)
    if inputs.debug:
        for handler in logger.root.handlers:
            handler.setLevel(logging.DEBUG)
            logger.debug("Logging set to Debug.")
    return inputs


def get_source_dictionaries(server, api_version, filter_retired):
    """
    Queries all dictionaries from a source server

    Note that querying the dictionary from an older (v3) project configuration service will take some time (hours).

    Parameters
    ----------
    server: str
        Ingenium Server (e.g. https://ingenium.project_name.jpl.nasa.gov) without a trailing slash

    api_version: str
        Either v3 or v4 (slight differences between the project configuration api)

    filter_retired: bool
        Whether to only backup the released/published dictionaries and ignore the retired dictionaries

    Returns
    -------
    dictionary_content: dict
        Python dictionary of all dictionary content
    """

    # Setting up a dictionary to hold all the information

    dictionary_content = {'versions': {'flight': {}, 'sse': {}},
                          'flight': {},
                          'sse': {},
                          'vis': [],
                          'custom_scripts': []}

    for dict_type in ['flight', 'sse']:

        versions = get_dictionary_versions(server, dict_type, api_version=api_version)

        for version in versions:

            # If the list of dictionaries is long you may want to skip the Retired ones. (it takes a long time to dump all of them)
            if filter_retired:
                if version.get('state') == 'RETIRED':
                    continue
            dictionary_content['versions'][dict_type][version.get('dictionary_version')] = {
                'dictionary_description': version.get('dictionary_description'),
                'dictionary_version': version.get('dictionary_version'),
                'state': version.get('state')}
            dictionary_content[dict_type][version.get('dictionary_version')] = {'cmds': [], 'channels': [], 'evrs': [],
                                                                               'mil1553': []}

            for sub_dict in ['cmds', 'evrs', 'channels', 'mil1553']:

                # First grab the master list of dictionary elements
                # This is only required in v3 of the PC API
                if api_version == 'v3':
                    # Query the dictionary content in the specific dictionary version (note that the try except is because if there are no elements a 400 error is thrown)
                    try:
                        elements = get_dictionary(server,
                                                                                                                         version.get(
                                                                                                                             'dictionary_version'),
                                                                                                                         dict_type,
                                                                                                                         sub_dict, api_version=api_version)
                    except:
                        logger.warning(f"Could not read {version.get('dictionary_version')} - type:{sub_dict}. Skipping", exc_info=True)
                        continue

                    # Now extract all the individual elements
                    for element in elements:
                        if sub_dict == 'cmds':
                            element_name = element.get('command_stem')
                        if sub_dict == 'evrs':
                            element_name = element.get('evr_name')
                        if sub_dict == 'channels':
                                element_name = element.get('eha_name')
                        if sub_dict == 'mil1553':
                            element_name = element.get('mil1553_name')

                        element_details =  get_dictionary_element(server,version.get('dictionary_version'),dict_type,sub_dict,element_name, api_version=api_version)
                        # Need to refresh the token because this takes awhile
                        common.refresh_auth(server)
                        dictionary_content[dict_type][version.get('dictionary_version')][sub_dict].append(element_details)

                else:
                    for sub_dict in ['cmds', 'evrs', 'channels', 'mil1553']:

                        # Query the dictionary content in the specific dictionary version (note that the try except is because if there are no elements a 400 error is thrown)
                        try:
                            dictionary_content[dict_type][version.get('dictionary_version')][sub_dict] = get_dictionary(
                                server,
                                version.get(
                                    'dictionary_version'),
                                dict_type,
                                sub_dict, api_version=api_version)
                        except:
                            logger.warning(
                                f"Could not read {version.get('dictionary_version')} - type:{sub_dict}. Skipping",
                                exc_info=True)

    dictionary_content['vis'] = get_vnv_vis(server,api_version=api_version)

    dictionary_content['custom_scripts'] = get_custom_scripts(server,api_version=api_version)

    return dictionary_content


##################################################### Main ###########################################################


def main(args=[]):
    """
    This is the main function of the Ingenium Migrate Execution script

    Parameters
    ----------
    args
        Array of input arguments. Used when this function is called from another Python module.

    Returns
    -------
        None
    """
    # Gets initial input
    inputs = get_input(args)

    # if ssl_ca_bundle is specified, it will take precedence over ignore_ssl_error
    if inputs.ssl_ca_bundle is not None:
        common.ssl_verify = inputs.ssl_ca_bundle
    else:
        common.ssl_verify = not inputs.ignore_ssl_error
        if not common.ssl_verify:
            # To suppress SSL warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    logger.debug(f"Ingenium.ssl_verify:{common.ssl_verify}")

    if inputs.username:
        username = inputs.username
    else:
        username = getpass.getuser()

    logger.info(f"Backing up project configuration from {inputs.server} to {inputs.file_output}.")

    if inputs.rsa:
        pw_prompt = f"Enter RSA Passcode for {username}:"
    else:
        pw_prompt = f"Enter LDAP Password for {username}:"

    # Login to source_execution
    login = common.authenticate(inputs.server, username=username, password=getpass.getpass(pw_prompt), force=True,
                                  rsa=inputs.rsa)

    if not login:
        msg = f"Failure to Login to: {inputs.server} - Can not proceed. Exiting."
        logger.error(msg)
        raise common.IngeniumLibError(msg)

    source_dict = get_source_dictionaries(inputs.server, inputs.api_version, inputs.filter_retired)

    with open(inputs.file_output, "w") as file:
        json.dump(source_dict, file)

if __name__ == '__main__':
    try:
        main()
    except common.IngeniumLibError:
        logger.error("Ingenium Project Configuration backup script has encountered and error and needs to exit. Please check the log messages for the source of the error.")

