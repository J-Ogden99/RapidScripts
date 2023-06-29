import os
from glob import glob


def extract_numeric_value(filename):
    return int(filename.split('_')[-1].split('to')[0])

# for i in range(20):
#     id = f'1000{i}'
#     for j in range(10):
#         os.makedirs(os.path.join('namelists', id, f'vpu_{j}'))
#         for start, end in zip(range(1940, 1980, 10), range(1949, 1989, 10)):
#             with open(os.path.join('namelists', id, f'vpu_{j}', f'rapid_namelist_{start}to{end}'), 'w') as f:
#                 f.write('')

rapid_exec_dir = 'rapid/run'
namelists_dir_main = '~/rapid/namelists'
os.chdir(rapid_exec_dir)
for namelist_dir in glob(os.path.join(namelists_dir_main, '*/vpu_*')):
    namelist_files = glob(os.path.join(namelist_dir, 'rapid_namelist_*'))
    namelist_files.sort(key=extract_numeric_value)
    for namelist_path in namelist_files:
        rapid_command = f'./rapid_script.sh --namelist {namelist_path}'
        # os.subprocess(rapid_command)
