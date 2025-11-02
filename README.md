# ingenium-lib

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

Libraries and scripts to interact with and support Ingenium operations. This repository provides a Python package (`ing-lib`) for programmatic interaction with Ingenium, focusing on systems test proceedures for complex engineering projects.

## Structure

The repository is organized as follows:

-   `ing-lib/`: The main Python package.
    -   `__init__.py`: Package initializer.
    -   `venue.py`: A client library for the Ingenium venue management API. It provides functions to create, query, and update venues and venue groups.
    -   `project_config.py`: The core library for managing Ingenium Project Configurations.
    -   `common.py`: Contains shared utility functions and constants used across the library.
    -   `logs.py`: Manages logging configuration.
    -   `apps/`: A collection of command-line applications for managing Project Configurations:
        -   `ProjConfigBackup.py`: Backs up a project configuration.
        -   `ProjConfigRestore.py`: Restores a project configuration from a backup.
        -   `ProjConfigClear.py`: Clears a project configuration.
        -   `ProjConfigCreateUpdateCS.py`: Creates or updates a project configuration using a custom script.
        -   `ProjConfigLoadAMPCSDict.py`: Loads a project configuration from an AMPCS dictionary.
    -   `utils/`: Contains utility scripts for data management.
        -   `ProjConfigV3toV4Convert.py`: Converts project configurations from v3 to v4 format.
    -   `tests/`: Contains pytest tests for the library.
-   `setup.py`: The setup script for the `ing-lib` package.
-   `requirements.txt`: A list of package dependencies.

## Installation

To install the `ing-lib` package, you can run the following command from the `ingenium-lib` directory:

```bash
pip install .
```

This will install the package and its dependencies (e.g., `rich`). The package requires Python 3.13 or higher.
