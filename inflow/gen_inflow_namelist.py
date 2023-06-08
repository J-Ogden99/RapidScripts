from RAPIDpy.inflow.lsm_rapid_process import run_lsm_rapid_process
from RAPIDpy.rapid import RAPID
from generate_namelist import generate_namelist
from datetime import datetime
import numpy as np
from glob import glob
import pandas as pd
import xarray as xr
from time import time
import os


def gen_inflow_namelist(rapid_inputs: str,
                        rapid_inflows: str,
                        rapid_outflows: str,
                        lsm_data_dir: str,
                        namelist_dir: str, 
                        start_year: int = 1940, 
                        end_year: int = 2022, 
                        interval: int = 10):
    """
    Generates inflow files to input into RAPID, as well as a cooresponding namelist file that gives
    the correct arguments for RAPID. Is run for every VPU number, and as such all directories given
    as arguments must be unique for the VPU, with the number as the title of the directory.

    Args:
        rapid_inputs (str): Path to directory that holds the input files for RAPID, including the k.csv, x.csv,
                            rapid_connect.csv, weight tables, etc. must be a direct path to a directory titled
                            with just the VPU number. (read only)
        rapid_inflows (str):Path to directory that will contain the inflow files. Should also be a directory 
                            titled with just the VPU number.
        rapid_outflows (str): Path to directory that the namelist will tell RAPID to write Qout files to. Also VPU-specific
        lsm_data_dir (str): Path to directory with Land Surface Model .nc files, one for every day in the run. (read only)
        namelist_dir (str): Path to write namelists to. The namelists will be written as rapid_namelist_{start_date}to{end_date}.
                            This is also VPU-specific.
        start_year (int): Year to begin simulation. Default 1940.
        end_year (int): Year to end simulation (simulation runs through end of year provided). Default 2022
        interval (int): Number of years to simulate over for each step. Default is 10.

    Returns:
        None
    """
    # Get vpu number from directory name
    vpu_id = os.path.basename(rapid_inputs)

    # Ensure all given write directories exist.
    for path in (rapid_inflows, rapid_outflows, namelist_dir):
        if not os.path.exists(path):
            os.makedirs(path)

    # Check for excess years after counting even numbers of years from start_year based on interval.
    # If excess found, set end_year to end of last interval that can be made, old_end stores original value for later use.
    old_end = end_year
    if (end_year - start_year + 1) % interval != 0:
        end_year -= (end_year - start_year + 1) % interval

    # Iterate over intervals, making inflows and namelists that apply to the correct dates for each.
    for start_date, end_date in zip(
        pd.date_range(
            start=datetime(start_year, 1, 1),
            end=datetime(end_year - interval + 1, 1, 1),
            freq=f'{interval}AS-JAN'
        ),
        pd.date_range(
            start=datetime(start_year + interval - 1, 12, 31),
            end=datetime(end_year, 12, 31),
            freq=f'{interval}A-DEC'
        )
        ):
        start_date_code = start_date.strftime("%Y%m%d")
        end_date_code = end_date.strftime("%Y%m%d")

        run_lsm_rapid_process(
            rapid_executable_location='',
            # rapid_io_files_location=rapidio_dir,
            rapid_file_location=rapid_inputs,
            # rapid_input_location='/Users/ricky/Documents/rapidio/rapid/input',
            rapid_output_location=rapid_inflows,
            lsm_data_location=lsm_data_dir,
            simulation_start_datetime=start_date,
            simulation_end_datetime=end_date,
            generate_rapid_namelist_file=False,  # if you want to run RAPID manually later
            run_rapid_simulation=False,  # if you want to run RAPID after generating inflow file
            generate_return_periods_file=False,  # if you want to get return period file from RAPID simulation
            return_period_method='weibull',
            generate_seasonal_averages_file=False,
            generate_seasonal_initialization_file=False,  # if you want to get seasonal init file from RAPID simulation
            generate_initialization_file=False,  # if you want to generate qinit file from end of RAPID simulation
            use_all_processors=True
        )

        # On first iteration, get the timestep for the simulation from the m3 file just made, and the total time within the
        # given interval (changes depending on leap year), both in seconds, to be given as arguments in the namelist file
        if int(start_date.year) == start_year:
            m3_nc_files = sorted(glob(os.path.join(rapid_inflows, 'm3*.nc')))
            simulation_timestep = np.timedelta64(np.diff(xr.open_dataset(m3_nc_files[0]).time.values)[0], 's').astype('int') #open output file, get timestep in seconds, cast to int
            use_qinit_file = False # No qinit file for first step
            qinit_file = ''
        else:
            last_step_date_code = datetime(start_date.year - 1, 12, 31).strftime("%Y%m%d")
            use_qinit_file = True # qinit file is Qfinal from last run.
            qinit_file = f"Qfinal_{vpu_id}_{last_step_date_code}.nc"
        time_total = int((end_date - start_date).total_seconds())
        
        generate_namelist(
            namelist_save_path = os.path.join(namelist_dir, f'rapid_namelist_{start_date_code}to{end_date_code}'),

            k_file = os.path.join(rapid_inputs, "k.csv"),
            x_file = os.path.join(rapid_inputs, "x.csv"),
            riv_bas_id_file = os.path.join(rapid_inputs, "riv_bas_id.csv"),
            rapid_connect_file = os.path.join(rapid_inputs, "rapid_connect.csv"),
            vlat_file = glob(os.path.join(rapid_inflows, f"m3*{start_date_code}to{end_date_code}.nc"))[0], #potentially delete every step
            qout_file = os.path.join(rapid_outflows, f"Qout_{start_date_code}to{end_date_code}.nc"),

            time_total = time_total,
            timestep_calc_routing = 900,
            timestep_calc = simulation_timestep,
            timestep_inp_runoff = simulation_timestep,

            # Optional - Flags for RAPID Options
            # run_type: int = 1,
            # routing_type = 1,

            use_qinit_file = use_qinit_file,
            qinit_file = qinit_file, # qinit_VPU_DATE.csv 8870 is difference between numerical representation of Jan. 1st and Dec 31st

            write_qfinal_file = True,
            qfinal_file = f'Qfinal_{vpu_id}_{end_date_code}.nc',

            # compute_volumes = False,
            # v_file = '',

            use_dam_model = False,  # todo more options here
            use_influence_model = False,
            use_forcing_file = False,
            use_uncertainty_quantification = False,

            opt_phi = 1,

            # Optional - Can be determined from rapid_connect
            reaches_in_rapid_connect = None,
            max_upstream_reaches = None,

            # Optional - Can be determined from riv_bas_id_file
            reaches_total = None,

            # Optional - Optimization Runs Only
            time_total_optimization = 0,
            timestep_observations = 0,
            timestep_forcing = 0
        )

    # Run last x years
    if old_end > end_year:
        start_date = datetime(end_year + 1, 1, 1)
        end_date = datetime(old_end, 12, 31)
        start_date_code = start_date.strftime("%Y%m%d")
        end_date_code = end_date.strftime("%Y%m%d")
        time_total = int((end_date - start_date).total_seconds())
        last_step_date_code = datetime(end_year, 12, 31).strftime("%Y%m%d")

        run_lsm_rapid_process(
            rapid_executable_location='',
            # rapid_io_files_location=rapidio_dir,
            rapid_file_location=rapid_inputs,
            # rapid_input_location='/Users/ricky/Documents/rapidio/rapid/input',
            rapid_output_location=rapid_inflows,
            lsm_data_location=lsm_data_dir,
            simulation_start_datetime=start_date,
            simulation_end_datetime=end_date,
            generate_rapid_namelist_file=False,  # if you want to run RAPID manually later
            run_rapid_simulation=False,  # if you want to run RAPID after generating inflow file
            generate_return_periods_file=False,  # if you want to get return period file from RAPID simulation
            return_period_method='weibull',
            generate_seasonal_averages_file=False,
            generate_seasonal_initialization_file=False,  # if you want to get seasonal init file from RAPID simulation
            generate_initialization_file=False,  # if you want to generate qinit file from end of RAPID simulation
            use_all_processors=True
        )

        generate_namelist(
            namelist_save_path = os.path.join(namelist_dir, f'rapid_namelist_{start_date_code}to{end_date_code}'),

            k_file = os.path.join(rapid_inputs, "k.csv"),
            x_file = os.path.join(rapid_inputs, "x.csv"),
            riv_bas_id_file = os.path.join(rapid_inputs, "riv_bas_id.csv"),
            rapid_connect_file = os.path.join(rapid_inputs, "rapid_connect.csv"),
            vlat_file = glob(os.path.join(rapid_inflows, f"m3*{start_date_code}to{end_date_code}.nc"))[0], #potentially delete every step
            qout_file = os.path.join(rapid_outflows, f"Qout_{start_date_code}to{end_date_code}.nc"),

            time_total = time_total,
            timestep_calc_routing = 900,
            timestep_calc = simulation_timestep,
            timestep_inp_runoff = simulation_timestep,

            # Optional - Flags for RAPID Options
            # run_type: int = 1,
            # routing_type = 1,

            use_qinit_file = True,
            qinit_file = f"Qfinal_{vpu_id}_{last_step_date_code}.nc",

            write_qfinal_file = True,
            qfinal_file = f'Qfinal_{vpu_id}_{end_date_code}.nc',

            # compute_volumes = False,
            # v_file = '',

            use_dam_model = False,  # todo more options here
            use_influence_model = False,
            use_forcing_file = False,
            use_uncertainty_quantification = False,

            opt_phi = 1,

            # Optional - Can be determined from rapid_connect
            reaches_in_rapid_connect = None,
            max_upstream_reaches = None,

            # Optional - Can be determined from riv_bas_id_file
            reaches_total = None,

            # Optional - Optimization Runs Only
            time_total_optimization = 0,
            timestep_observations = 0,
            timestep_forcing = 0
        )
        