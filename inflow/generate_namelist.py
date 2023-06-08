import os
import pandas as pd


def generate_namelist(
        namelist_save_path: str,

        k_file: str,
        x_file: str,
        riv_bas_id_file: str,
        rapid_connect_file: str,
        vlat_file: str,
        qout_file: str,

        time_total: int,
        timestep_calc_routing: int,
        timestep_calc: int,
        timestep_inp_runoff: int,

        # Optional - Flags for RAPID Options
        run_type: int = 1,
        routing_type: int = 1,

        use_qinit_file: bool = False,
        qinit_file: str = '',  # qinit_VPU_DATE.csv

        write_qfinal_file: bool = True,
        qfinal_file: str = '',

        compute_volumes: bool = False,
        v_file: str = '',

        use_dam_model: bool = False,  # todo more options here
        use_influence_model: bool = False,
        use_forcing_file: bool = False,
        use_uncertainty_quantification: bool = False,

        opt_phi: int = 1,

        # Optional - Can be determined from rapid_connect
        reaches_in_rapid_connect: int = None,
        max_upstream_reaches: int = None,

        # Optional - Can be determined from riv_bas_id_file
        reaches_total: int = None,

        # Optional - Optimization Runs Only
        time_total_optimization: int = 0,
        timestep_observations: int = 0,
        timestep_forcing: int = 0,
) -> None:
    """
    Generate a namelist file for RAPID

    Note all times should be in seconds

    Returns:
        None
    """
    # """
    # Args:
    #     k_file (str): Path to the k_file (input)
    #     x_file (str): Path to the x_file (input)
    #     rapid_connect_file (str): Path to the rapid_connect_file (input)
    #     Qout_file (str): Path to save the Qout_file (routed discharge file)
    #     Vlat_file (str): Path to the Vlat_file (inflow file)
    #
    #     BS_opt_Qfinal: Path to the save the Qfinal file (optional output)
    #     BS_opt_Qinit: Path to the initialization file (optional input)
    # """

    assert(run_type in (1, 2), 'run_type must be 1 or 2')
    assert(routing_type in (1, 2, 3, 4), 'routing_type must be 1, 2, 3, or 4')
    assert(opt_phi in (1, 2), 'opt_phi must be 1, or 2')

    if any([x is None for x in (reaches_in_rapid_connect, max_upstream_reaches)]):
        df = pd.read_csv(rapid_connect_file, header=None)
        reaches_in_rapid_connect = df.shape[0]
        rapid_connect_columns = ['rivid', 'next_down', 'count_upstream']  # plus 1 per possible upstream reach
        max_upstream_reaches = df.columns.shape[0] - len(rapid_connect_columns)

    if reaches_total is None:
        df = pd.read_csv(riv_bas_id_file, header=None)
        reaches_total = df.shape[0]

    namelist_options = {
        'BS_opt_Qfinal': f'.{str(write_qfinal_file).lower()}.',
        'BS_opt_Qinit': f'.{str(use_qinit_file).lower()}.',
        'BS_opt_dam': f'.{str(use_dam_model).lower()}.',
        'BS_opt_for': f'.{str(use_forcing_file).lower()}.',
        'BS_opt_influence': f'.{str(use_influence_model).lower()}.',
        'BS_opt_V': f'.{str(compute_volumes).lower()}.',
        'BS_opt_uq': f'.{str(use_uncertainty_quantification).lower()}.',

        'k_file': f'"{k_file}"',
        'x_file': f'"{x_file}"',
        'rapid_connect_file': f'"{rapid_connect_file}"',
        'riv_bas_id_file': f'"{riv_bas_id_file}"',
        'Qout_file': f'"{qout_file}"',
        'Vlat_file': f'"{vlat_file}"',
        'V_file': f'"{v_file}"',

        'IS_opt_run': run_type,
        'IS_opt_routing': routing_type,
        'IS_opt_phi': opt_phi,
        'IS_max_up': max_upstream_reaches,
        'IS_riv_bas': reaches_in_rapid_connect,
        'IS_riv_tot': reaches_total,

        'IS_dam_tot': 0,
        'IS_dam_use': 0,
        'IS_for_tot': 0,
        'IS_for_use': 0,

        'Qinit_file': f'"{qinit_file}"',
        'Qfinal_file': f'"{qfinal_file}"',

        'ZS_TauR': timestep_inp_runoff,
        'ZS_dtR': timestep_calc_routing,
        'ZS_TauM': time_total,
        'ZS_dtM': timestep_calc,
        'ZS_TauO': time_total_optimization,
        'ZS_dtO': timestep_observations,
        'ZS_dtF': timestep_forcing,
    }

    # generate the namelist file
    namelist_string = '\n'.join([
        '&NL_namelist',
        *[f'{key} = {value}' for key, value in namelist_options.items()],
        '/',
    ])

    with open(namelist_save_path, 'w') as f:
        f.write(namelist_string)

if __name__ == "__main__":
    rapid_inputs_dir = "/Users/joshogden/Documents/rapid_io/rapid/input/"
    sub_dir = '7020065090/'
    start_date = 19700101
    end_date = 19791231
    generate_namelist(
        namelist_save_path = "/Users/joshogden/Documents/namelist",

        k_file = os.path.join(rapid_inputs_dir, sub_dir, "k.csv"),
        x_file = os.path.join(rapid_inputs_dir, sub_dir, "x.csv"),
        riv_bas_id_file = os.path.join(rapid_inputs_dir, sub_dir, "riv_bas_id.csv"),
        rapid_connect_file = os.path.join(rapid_inputs_dir, sub_dir, "rapid_connect.csv"),
        vlat_file = os.path.join(rapid_inputs_dir, sub_dir, f"m3_VPU_era5_t640_24hr_{start_date}to{end_date}.nc"), #potentially delete every step
        qout_file = os.path.join(rapid_inputs_dir, sub_dir, f"Qout_VPU_{start_date}to{end_date}.nc"),

        time_total = 189388800,
        timestep_calc_routing = 900,
        timestep_calc = 86400,
        timestep_inp_runoff = 86400,

        # Optional - Flags for RAPID Options
        # run_type: int = 1,
        # routing_type = 1,

        use_qinit_file = True,
        qinit_file = f"Qinit_VPU_{start_date - 8870}.csv", # qinit_VPU_DATE.csv 8870 is difference between numerical representation of Jan. 1st and Dec 31st

        write_qfinal_file = True,
        qfinal_file = f'Qinit_VPU_{end_date}.csv',

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
