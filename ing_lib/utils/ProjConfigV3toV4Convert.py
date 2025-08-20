#!/usr/bin/env python3
"""
ProjConfigV3toV4Convert.py

Utility script to convert verification item (VI) JSON data from API v3 format to v4 format.

The main differences are:
1. v4 adds 'vas' and 'vacs' arrays to the VerificationItem schema
2. v4 extracts va_name and vac_name from v3's vas array into separate arrays
3. v4 fixes state field values, converting "NOT PUBLISHED" to "NOT_PUBLISHED"
4. v4 validates custom script names against the pattern ^[a-zA-Z0-9_-]{1,64}$
5. v4 strips '.py' extensions from custom script names
6. v4 converts command argument types (enum->ENUM, var_string->STRING, unsigned->UINT, signed->INT,
float->FLOAT, int->INT, uint->UINT, rol->ROL, string->STRING, fixed_string->STRING, unknown->ENUM/UINT)
7. v4 converts mil1553 transmit_receive values (T->TRANSMIT, R->RECEIVE)
"""

import argparse
import json
import sys
import os
import re
from typing import Dict, List, Any, Union

# Regular expression pattern for valid custom script names
CUSTOM_SCRIPT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')

# Mapping for v3 to v4 argument type conversions
ARGUMENT_TYPE_MAPPING = {
    'enum': 'ENUM',
    'var_string': 'STRING', 
    'unsigned': 'UINT',
    'signed': 'INT',
    'float': 'FLOAT',
    'int': 'INT',
    'uint': 'UINT',
    'rol': 'ROL',
    'integer': 'INT',
    'string': 'STRING',
    'fixed_string': 'STRING'
}


def validate_custom_script_name(script_name: str) -> bool:
    """
    Validate a custom script name against the required pattern.
    
    Parameters
    ----------
    script_name : str
        The script name to validate
        
    Returns
    -------
    bool
        True if the script name is valid, False otherwise
    """
    if not script_name or not isinstance(script_name, str):
        return False
    return bool(CUSTOM_SCRIPT_NAME_PATTERN.match(script_name))



def fix_custom_script_names(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively find custom script names, strip '.py' extensions, and validate them in nested data structures.
    Issues warnings for invalid names but does not prevent conversion.
    
    Parameters
    ----------
    data : Union[Dict, List, Any]
        Data structure that may contain custom scripts
        
    Returns
    -------
    Union[Dict, List, Any]
        Data structure with custom script names processed and validated
    """
    if isinstance(data, dict):
        # Make a copy to avoid modifying the original
        result = {}
        for key, value in data.items():
            if key == 'custom_scripts' and isinstance(value, list):
                # Found custom scripts array - process each script name
                result[key] = []
                for item in value:
                    if isinstance(item, dict) and 'script_name' in item:
                        script_name = item['script_name']
                        # Strip .py extension if present
                        if script_name.endswith('.py'):
                            original_name = script_name
                            script_name = script_name[:-3]  # Remove last 3 characters (.py)
                            print(f"INFO: Stripped '.py' from script name: '{original_name}' -> '{script_name}'")
                            # Update the script name in the item
                            item = item.copy()
                            item['script_name'] = script_name
                        
                        # Validate the processed script name
                        if not validate_custom_script_name(script_name):
                            print(f"WARNING: Invalid custom script name '{script_name}'. "
                                  f"Must match pattern ^[a-zA-Z0-9_-]{{1,64}}$")
                        result[key].append(item)
                    else:
                        result[key].append(item)
            else:
                # Recursively process other values
                result[key] = fix_custom_script_names(value)
        return result
    elif isinstance(data, list):
        # Process each item in the list
        result = []
        for item in data:
            # Check if this is a custom script
            if isinstance(item, dict) and 'script_name' in item:
                script_name = item['script_name']
                # Strip .py extension if present
                if script_name.endswith('.py'):
                    original_name = script_name
                    script_name = script_name[:-3]  # Remove last 3 characters (.py)
                    print(f"INFO: Stripped '.py' from script name: '{original_name}' -> '{script_name}'")
                    # Update the script name in the item
                    item = item.copy()
                    item['script_name'] = script_name
                
                # Validate the processed script name
                if not validate_custom_script_name(script_name):
                    print(f"WARNING: Invalid custom script name '{script_name}'. "
                          f"Must match pattern ^[a-zA-Z0-9_-]{{1,64}}$")
                result.append(item)
            else:
                result.append(fix_custom_script_names(item))
        return result
    else:
        # Return primitive values as-is
        return data


def convert_argument_type(v3_type: str, argument: Dict[str, Any] = None) -> str:
    """
    Convert a v3 argument type to v4 format.
    
    Parameters
    ----------
    v3_type : str
        The argument type from v3 format
    argument : Dict[str, Any], optional
        The full argument object (needed for "unknown" type conversion)
        
    Returns
    -------
    str
        The argument type in v4 format
    """
    if not v3_type or not isinstance(v3_type, str):
        return v3_type
    
    # Convert to lowercase for case-insensitive matching
    v3_type_lower = v3_type.lower()
    
    # Special handling for "unknown" type
    if v3_type_lower == "unknown":
        if argument and isinstance(argument, dict):
            # Check if enumerations are defined
            enumerations = argument.get('enumerations', [])
            if enumerations and len(enumerations) > 0:
                return "ENUM"
            else:
                return "UINT"
        else:
            # If we don't have the argument object, default to UINT
            print(f"WARNING: 'unknown' argument type found but no argument object provided, defaulting to UINT")
            return "UINT"
    
    if v3_type_lower in ARGUMENT_TYPE_MAPPING:
        converted_type = ARGUMENT_TYPE_MAPPING[v3_type_lower]
        return converted_type
    else:
        print(f"WARNING: Unknown argument type '{v3_type}', leaving unchanged")
        return v3_type


def fix_mil1553_transmit_receive(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively find and convert transmit_receive values in mil1553 data from T/R to TRANSMIT/RECEIVE format.
    
    Parameters
    ----------
    data : Union[Dict, List, Any]
        Data structure that may contain mil1553 transmit_receive values
        
    Returns
    -------
    Union[Dict, List, Any]
        Data structure with transmit_receive values converted to v4 format
    """
    if isinstance(data, dict):
        # Make a copy to avoid modifying the original
        result = {}
        for key, value in data.items():
            if key == 'transmit_receive' and isinstance(value, str):
                # Convert T/R values to TRANSMIT/RECEIVE
                if value == 'T':
                    result[key] = 'TRANSMIT'
                elif value == 'R':
                    result[key] = 'RECEIVE'
                else:
                    result[key] = value
            else:
                # Recursively process other values
                result[key] = fix_mil1553_transmit_receive(value)
        return result
    elif isinstance(data, list):
        # Process each item in the list
        result = []
        for item in data:
            result.append(fix_mil1553_transmit_receive(item))
        return result
    else:
        # Return primitive values as-is
        return data


def fix_argument_types(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively find and convert argument types in command arguments from v3 to v4 format.
    
    Parameters
    ----------
    data : Union[Dict, List, Any]
        Data structure that may contain command arguments
        
    Returns
    -------
    Union[Dict, List, Any]
        Data structure with argument types converted to v4 format
    """
    if isinstance(data, dict):
        # Make a copy to avoid modifying the original
        result = {}
        for key, value in data.items():
            if key == 'arguments' and isinstance(value, list):
                # Found arguments array - process each argument's type
                result[key] = []
                for arg in value:
                    if isinstance(arg, dict) and 'argument_type' in arg:
                        # Convert the argument type
                        arg = arg.copy()
                        arg['argument_type'] = convert_argument_type(arg['argument_type'], arg)
                    result[key].append(arg)
            else:
                # Recursively process other values
                result[key] = fix_argument_types(value)
        return result
    elif isinstance(data, list):
        # Process each item in the list
        result = []
        for item in data:
            # Check if this is an argument with argument_type
            if isinstance(item, dict) and 'argument_type' in item:
                item = item.copy()
                item['argument_type'] = convert_argument_type(item['argument_type'], item)
            result.append(fix_argument_types(item))
        return result
    else:
        # Return primitive values as-is
        return data


def convert_verification_item(vi_v3: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a single verification item from v3 to v4 format.
    
    Parameters
    ----------
    vi_v3 : Dict[str, Any]
        Verification item in v3 format
        
    Returns
    -------
    Dict[str, Any]
        The verification item in v4 format
    """
    vi_v4 = vi_v3.copy()
    
    # Fix state field if present
    if 'state' in vi_v4 and vi_v4['state'] == "NOT PUBLISHED":
        vi_v4['state'] = "NOT_PUBLISHED"
    
    # Initialize new arrays for v4
    va_names = []
    vac_names = []
    
    # Extract va_name and vac_name from the existing vas array if it exists
    if 'vas' in vi_v3 and isinstance(vi_v3['vas'], list):
        for va in vi_v3['vas']:
            if isinstance(va, dict):
                # Extract va_name if available
                if 'va_name' in va and va['va_name'] and va['va_name'] not in va_names:
                    va_names.append(va['va_name'])
                    
                # Also include va_id if available (as an alternative in case va_name is missing)
                elif 'va_id' in va and va['va_id'] and va['va_id'] not in va_names:
                    va_names.append(va['va_id'])
                
                # Extract vac_name if available    
                if 'vac_name' in va and va['vac_name'] and va['vac_name'] not in vac_names:
                    vac_names.append(va['vac_name'])
                
                # Also include vac_id if available (as an alternative in case vac_name is missing)
                elif 'vac_id' in va and va['vac_id'] and va['vac_id'] not in vac_names:
                    vac_names.append(va['vac_id'])
    
    # Set the new v4 format fields
    vi_v4['vas'] = va_names
    vi_v4['vacs'] = vac_names
    
    return vi_v4


def convert_verification_items(vi_list_v3: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert a list of verification items from v3 to v4 format.
    
    Parameters
    ----------
    vi_list_v3 : List[Dict[str, Any]]
        List of verification items in v3 format
        
    Returns
    -------
    List[Dict[str, Any]]
        List of verification items in v4 format
    """
    return [convert_verification_item(vi) for vi in vi_list_v3]


def convert_verification_items_recursive(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively find and convert verification items in nested data structures.
    
    Parameters
    ----------
    data : Union[Dict, List, Any]
        Data structure that may contain verification items
        
    Returns
    -------
    Union[Dict, List, Any]
        Data structure with verification items converted to v4 format
    """
    if isinstance(data, dict):
        # Make a copy to avoid modifying the original
        result = {}
        for key, value in data.items():
            if key == 'vis' and isinstance(value, list):
                # Found verification items array - convert each item
                result[key] = []
                for item in value:
                    if isinstance(item, dict) and 'vi_id' in item:
                        result[key].append(convert_verification_item(item))
                    else:
                        result[key].append(item)
            else:
                # Recursively process other values
                result[key] = convert_verification_items_recursive(value)
        return result
    elif isinstance(data, list):
        # Process each item in the list
        result = []
        for item in data:
            # Check if this is a verification item
            if isinstance(item, dict) and 'vi_id' in item:
                result.append(convert_verification_item(item))
            else:
                result.append(convert_verification_items_recursive(item))
        return result
    else:
        # Return primitive values as-is
        return data


def fix_state_field(obj: Dict[str, Any]) -> None:
    """
    Recursively fix state fields in a nested dictionary.
    
    Parameters
    ----------
    obj : Dict[str, Any]
        Dictionary to fix state fields in
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "state" and value == "NOT PUBLISHED":
                obj[key] = "NOT_PUBLISHED"
            elif isinstance(value, (dict, list)):
                fix_state_field(value)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                fix_state_field(item)


def fix_plural(data):
    """

    Parameters
    ----------
    data

    Returns
    -------

    """

    for dict_type in ['flight', 'sse']:
        for version_id, version in data[dict_type].items():
            if version.get('cmd'):
                version['cmds'] = version.pop('cmd')
            if version.get('channel'):
                version['channels'] = version.pop('channel')
            if version.get('evr'):
                version['evrs'] = version.pop('evr')
            if version.get('1553'):
                version['mil1553'] = version.pop('1553')


def fix_eha_to_channel(data):
    """

    Parameters
    ----------
    obj

    Returns
    -------

    """

    for dict_type in ['flight', 'sse']:
        for version_id, version in data[dict_type].items():
            for channel in version['channels']:
                channel['channel_name'] = channel.pop('eha_name')
                channel['description'] = channel.pop('eha_description')
                if 'eha_bit_size' in channel:
                    channel['bit_size'] = channel.pop('eha_bit_size')
                if 'eha_type' in channel:
                    channel['type'] = channel.pop('eha_type')


def convert_json_file(input_file: str, output_file: str = None) -> None:
    """
    Convert a JSON file containing verification items from v3 to v4 format.
    Also strips '.py' extensions from custom script names, validates them against the pattern ^[a-zA-Z0-9_-]{1,64}$,
    and converts command argument types from v3 to v4 format.
    
    Parameters
    ----------
    input_file : str
        Path to the input JSON file (v3 format)
    output_file : str, optional
        Path to the output JSON file (v4 format).
        If None, will output to [input_file]_v4.json
    
    Raises
    ------
    SystemExit
        If the input file is not found or contains invalid JSON
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: '{input_file}' is not a valid JSON file.")
        sys.exit(1)
    
    # Fix state fields throughout the entire structure
    fix_state_field(data)

    fix_plural(data)

    # Fix EHA/Channel names
    fix_eha_to_channel(data)

    # Strip .py extensions from custom script names and validate them
    data = fix_custom_script_names(data)

    # Convert argument types from v3 to v4 format
    data = fix_argument_types(data)

    # Convert mil1553 transmit_receive values from T/R to TRANSMIT/RECEIVE
    data = fix_mil1553_transmit_receive(data)

    # Apply recursive conversion to handle verification items wherever they are nested
    converted_data = convert_verification_items_recursive(data)
    
    # Determine output file
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_v4{ext}"
    
    with open(output_file, 'w') as f:
        json.dump(converted_data, f, indent=2)
    
    print(f"Successfully converted {input_file} to {output_file}.")


def main():
    parser = argparse.ArgumentParser(
        description='Convert verification item JSON from API v3 format to v4 format.'
    )
    parser.add_argument(
        'input_file',
        help='Input JSON file containing verification items in v3 format.'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path for the v4 format JSON. If not specified, will use [input_file]_v4.json.'
    )
    args = parser.parse_args()
    
    convert_json_file(args.input_file, args.output)


if __name__ == "__main__":
    main()
