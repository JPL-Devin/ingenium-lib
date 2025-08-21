
'''
This is reference Ingenium Custom Script it intended as a demo of the capabilities in a custom script
 and as a template to follow for implementation.


Authors:
    * Chris Swan 
    * Hongman Kim 

'''

import os
import time
from datetime import datetime, timedelta
import copy
import os
import matplotlib.pyplot as plt
import random
from ing_lib.logs import init_console_logger, get_logger
init_console_logger()
logger = get_logger(__name__)

from ing_lib.steps import *

GRAPH_FILE_NAME = 'sample_graph.png'

def plot_series(series: list, output_dir: str,
                     png_name: str = GRAPH_FILE_NAME):
    """
    Plot **all** channel time‑series on a single figure and save as PNG.

    Parameters
    ----------
    series : list[dict]
        List of channel dictionaries built earlier (each contains
        ``name``, ``color`` and ``data`` = [(dn, ert), …]).
    output_dir : str
        Directory where the PNG will be written.
    png_name : str, optional
        Filename (without path) for the combined plot.
    """
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    plt.figure(figsize=(12, 6))

    plotted_any = False   # <-- will stay False if no channel has valid points

    # Iterate over every channel, plotting its points
    for ch in series:
        chan_id = ch.get("name", "unknown")
        colour  = ch.get("color", "#000000")
        raw_data = ch.get("data", [])

        dn_vals = []
        ert_vals = []

        for point in raw_data:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                continue
            dn, ert = point
            try:
                ert_dt= datetime.strptime(ert, "%Y-%jT%H:%M:%S.%f")
            except Exception as exc:
                logger.debug(f"Could not parse ERT '{ert}' for channel {chan_id}: {exc}")
                continue

            dn_vals.append(float(dn))
            ert_vals.append(ert_dt)

        if not dn_vals:
            logger.warning(f"No valid telemetry points for channel {chan_id}; skipping plot.")
            continue

        # Plot this channel’s line (with markers for visibility)
        plt.plot(ert_vals, dn_vals,
                 color=colour,
                 linewidth=2,
                 marker='o',
                 markersize=4,
                 label=f"Channel {chan_id}")
        plotted_any = True  # at least one line was drawn

    # ------------------------------------------------------------------
    # Only add a legend if something was actually plotted.
    # ------------------------------------------------------------------
    if plotted_any:
        plt.title("Telemetry – DN vs. Earth Return Time (All Channels)")
        plt.xlabel("Earth Return Time (ERT)")
        plt.ylabel("DN Value")
        plt.grid(True, which="both", ls="--", lw=0.5, alpha=0.7)
        plt.legend(title="Channels", loc="best", fontsize="small")
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
    else:
        # Still produce a minimal figure so the PNG exists, but warn the user.
        plt.title("No valid telemetry data to display")
        plt.axis('off')  # hide axes

    # Save the combined image
    png_path = os.path.join(output_dir, png_name)
    plt.savefig(png_path, dpi=300)
    plt.close()

    logger.info(f"Saved combined telemetry plot → {png_path}")

if __name__ == '__main__':


    # Locate the custom script input file
    error_msg = 'USAGE: python reference_step.py input_file_path output_file_path'
    input_file_abs_path, output_file_abs_path = get_input_output_paths(error_msg)
    logger.info(f'input_file_abs_path: {input_file_abs_path}')
    logger.info(f'output_file_abs_path: {output_file_abs_path}')

    # Read the input file
    logger.info('Reading custom script inputs')
    input_dict = read_input_file(input_file_abs_path)

    # Initialize the Output Data
    '''
    Users should construct the output data structure as a python dictionary and initialize the status to "PENDING"
    Later the script will update this dictionary as results are produced and it can be easily saved to the outputs.json
    
    Note that this varies per script (as the outputs vary)
    '''


    # Initialize output data
    inputs = copy.deepcopy(input_dict.get('inputs', []))
    variables = input_dict.get('variables', {})
    telemetry= copy.deepcopy(variables.get('telemetry', {}))
    parameters=copy.deepcopy(variables.get('parameters', {}))    
    entries = copy.deepcopy(input_dict.get('entries', {}))
    outputs = {
        'start_time': '',
        'query_start': '',
        'query_end': '',
        'file_output': '',
        'image_output': '',
        'series_output': '',
    }

    my_output_array = []

    output_dict = {
        'custom_script_status': 'PENDING',
        'inputs': inputs,
        'entries': entries,
        'outputs': outputs,
        'output_array': my_output_array
    }

    # Step through each entry and initialize the outputs
    for i, entry in enumerate(entries):
        entry['verification_status'] = 'PENDING'
        entry['entry_outputs'] = {
            'entry_output_1': 0,   # INT
            'entry_output_2': 0.0, # FLOAT
            'entry_output_3': 0,   # INT
            'entry_output_4': 0.0, # FLOAT
            'entry_output_5': 0.0, # FLOAT
            'entry_output_6': 0,   # INT
        }
        entry['entry_output_array'] = []

    # Write initial output
    write_output_file(output_dict, output_file_abs_path)
    logger.info('Output file was initialized')

    '''
    Add the custom script logic here
    Remember to:
        - Program defensibly (use try/except, think about what happens if actions fail)
        - Update the output_dict as you go and save it when new results are available (this will provide visibility while it is executing)
        - Log the actions - it helps with visibility and troubleshooting
        - Remember that the script will likley be running as an application user - not as you
    '''

    '''
    The following code builds random ouputs for the script
    '''

    # Convert the start_time to a datetime object
    start_time = datetime.strptime(inputs['start_time'], '%Y-%jT%H:%M:%S.%f')
    
    # Compute the query range
    query_start = start_time - timedelta(seconds=inputs['lookback'])
    query_end = start_time + timedelta(seconds=inputs['timeout'])
    
    # Update the query range in the outputs
    outputs['start_time_date_time'] = start_time.strftime('%Y-%jT%H:%M:%S.%f')
    outputs['query_start'] = query_start.strftime('%Y-%jT%H:%M:%S.%f')
    outputs['query_end'] = query_end.strftime('%Y-%jT%H:%M:%S.%f')

    # Populate output values
    for i, entry in enumerate(entries):
        entry['verification_status'] = 'PASS'
        entry['entry_outputs']['entry_output_1'] = '' + str(i)
        entry['entry_outputs']['entry_output_2'] = '' + str(10*i)

        entry_output_array = entry['entry_output_array']
        for j in range(random.randint(2,6)):
            elem = {
                'entry_output_array_field_1': '' + str(j),
                'entry_output_array_field_2': '' + str(10*j),
            }
            entry_output_array.append(elem)
        
        write_output_file(output_dict, output_file_abs_path)
        logger.info(f'Entry was added: {i}')
            
        time.sleep(1)

    # Populate my_output_array (top‑level) with the defined fields
    for i in range(random.randint(2,15)):
        item = {
            'output_array_field_1': i,               # INT
            'output_array_field_2': float(10 * i),   # FLOAT
            'output_array_field_3': float(20 * i),   # FLOAT
            'output_array_field_4': i * 2,           # INT
            'output_array_field_5': i * 3,           # INT
            'output_array_field_6': float(30 * i),   # FLOAT
            'output_array_field_7': i * 4,           # INT
        }
        my_output_array.append(item)

    # Build a series

    series= {'series' :[
                {
                'name': 'BATMAN',
                'series_type': 'HORIZONTAL',
                'timetype': 'Earth Return Time',
                'color': '#499894',
                'data': []
                },
                {
                'name': 'ROBIN',
                'series_type': 'HORIZONTAL',
                'timetype': 'Earth Return Time',
                'color': '#FF0000',
                'data': []
                }
            ]
    }
    for s in series['series']:
        for i in range(random.randint(8,20)):
            time = start_time + timedelta(seconds=i*random.randint(1,10))
            value = random.randrange(3,14)
            s['data'].append((value,time.strftime('%Y-%jT%H:%M:%S.%f')))

      
        s['data'].sort(key=lambda pt: datetime.strptime(pt[1], '%Y-%jT%H:%M:%S.%f'))




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

    msg = f'reference_step.py has run to completion with overall status: {custom_script_status}' 
    logger.info(msg)
    output_dict['custom_script_status'] = custom_script_status

    # Write any series or image data
    output_dir = os.path.dirname(output_file_abs_path)
    write_series_file(series,output_dir)

   # Write image of channels graphed
    plot_series(series['series'], output_dir)

    # Report Final custom_script_status
    write_output_file(output_dict, output_file_abs_path)

