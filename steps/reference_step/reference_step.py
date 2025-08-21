
'''
This is an example of Ingenium custom script that can be used as a template for a new script.

<Add your description of said script>

Authors:
    * Chris Swan 
    * Hongman Kim 

'''


import time
import copy

# Note that the import order is important here - script utils comes last (otherwise the logging doesn't work)

# Note: ing_venue_utils is supported only for Python 2.7 currently.
# from ingenium_cs.script_utils.ing_venue_utils import get_eha, get_evr, send_fsw_cmd, start_mtak
from ingenium_cs.script_utils.chill_utils import query_evr
from ingenium_cs.script_utils.utils import get_input_output_paths, read_input_file, write_output_file, custom_script_log


if __name__ == '__main__':

    # Locate the custom script input file
    error_msg = 'USAGE: python template.py input_file_path output_file_path'
    input_file_abs_path, output_file_abs_path = get_input_output_paths(error_msg)
    custom_script_log.info('input_file_abs_path: %s' % input_file_abs_path)
    custom_script_log.info('output_file_abs_path: %s' % output_file_abs_path)

    # Read the input file
    custom_script_log.info('Reading custom script inputs')
    input_dict = read_input_file(input_file_abs_path)

    # Initialize the Output Data
    '''
    Users should construct the output data structure as a python dictionary and initialize the status to "PENDING"
    Later the script will update this dictionary as results are produced and it can be easily saved to the outputs.json
    
    Note that this varies per script (as the outputs vary)
    '''

    # Example Code
    # Users should modify this based on their inputs/outputs.

    # Initialize output data
    inputs = copy.deepcopy(input_dict.get('inputs', []))
    entries = copy.deepcopy(input_dict.get('entries', {}))
    outputs = {
        'output_1': 0,
        'output_2': 0
    }
    output_array = []

    output_dict = {
        'custom_script_status': 'PENDING',
        'inputs': inputs,
        'entries': entries,
        'outputs': outputs,
        'output_array': output_array
    }

    # Step through each entry and initialize the outputs
    for i, entry in enumerate(entries):
        entry['verification_status'] = 'PENDING'
        entry['entry_outputs'] = {
            'entry_output_1': '0',
            'entry_output_2': '0'
        }
        entry['entry_output_array'] = []

    # Write initial output
    write_output_file(output_dict, output_file_abs_path)
    custom_script_log.info('Output file was initialized')

    '''
    Add the custom script logic here
    Remember to:
        - Program defensibly (use try/except, think about what happens if actions fail)
        - Update the output_dict as you go and save it when new results are available (this will provide visibility while it is executing)
        - Log the actions - it helps with visibility and troubleshooting
        - Remember that the script will be running as an application user - not you
    '''
    # Populate output values
    for i, entry in enumerate(entries):
        entry['verification_status'] = 'PASS'
        entry['entry_outputs']['entry_output_1'] = '' + str(i)
        entry['entry_outputs']['entry_output_2'] = '' + str(10*i)

        entry_output_array = entry['entry_output_array']
        for j in range(5):
            elem = {
                'entry_output_array_field_1': '' + str(j),
                'entry_output_array_field_2': '' + str(10*j),
            }
            entry_output_array.append(elem)
        
        write_output_file(output_dict, output_file_abs_path)
        custom_script_log.info('Entry was added: %s' % i)
            
        time.sleep(1)

    # set outputs        
    outputs['output_1'] = '101'
    outputs['output_2'] = '102'
    
    # set ouput array
    for i in range(10):
        item = {
            'output_array_field_1': str(i),
            'output_array_field_2': str(10*i),
        }               

        output_array.append(item)        


    '''
    If your script has entries - evaluate them to determine overall status.
    '''
    # Review entries to generate overall status
    custom_script_status = 'PASS'
    for entry in entries:
        if entry['verification_status'] != 'PASS':
            custom_script_status = 'FAIL'
            break

    '''
    Log the successful completion and Push the final status (PASS/FAIL/ERROR) to the output_dict - 
    Ingenium watches for the status to be Not equal to PENDING 
    
    Note that you will likely have some logic to determine pass/fail (or will base it off entry verification_status)
    '''


    output_dict['custom_script_status'] = 'PASS'

    msg = 'template.py has run to completion with overall status: %s' % custom_script_status
    custom_script_log.info(msg)
    output_dict['custom_script_status'] = custom_script_status

    # Report Final custom_script_status
    write_output_file(output_dict, output_file_abs_path)

