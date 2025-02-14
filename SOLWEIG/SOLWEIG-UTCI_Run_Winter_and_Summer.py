# Run SOLWEIG Spatial UTCI from the QGIS/OSGeo Shell
# G. Oukawa - Jun 2024

import os
import processing
from qgis.core import QgsApplication, QgsProcessingFeedback
from qgis.analysis import QgsNativeAlgorithms
from PyQt5.QtWidgets import QProgressDialog

spatial_res = input('Enter spatial resolution (2- or 10-m): ')
if spatial_res not in ('2', '10'):
    print('Invalid spatial resolution.')
    exit(1)
seasons = ['winter', 'summer']
season = input('Select season (winter/summer): ')
if season not in seasons:
    print('Invalid season.')
    exit(1)

Tmrt_base_path = 'X:/UMEP/Tmrt/'
UTCI_output_path = 'X:/UMEP/UTCI/'

# Algorithm parameters (only used for PET)
params = {
    'COMFA': False,
    'CLO': 0.9,
    'ACTIVITY': 80,
    'AGE': 35,
    'HEIGHT': 180,
    'WEIGHT': 75,
    'SEX': 0,
    'TC_TYPE': 1,
}

# WS rasters from URock
ws_fields = {
    'C1': 'WS_C1_{season}_{spatial_res}.tif',
    'C2': 'WS_C2_{season}_{spatial_res}.tif',
    'C3': 'WS_C3_{season}_{spatial_res}.tif',
}

clusters = ['C1', 'C2', 'C3']

def run_solweig_utci_algorithm(input_file, output_file):
    params['TMRT_MAP'] = input_file
    params['TC_OUT'] = output_file

    progress_dialog = QProgressDialog('Running SOLWEIG...', 'Abort', 0, 100)
    progress_dialog.setWindowTitle('Processing')
    progress_dialog.setModal(True)
    progress_dialog.show()

    try:
        result = processing.run('umep:Outdoor Thermal Comfort: Spatial Thermal Comfort', params)
        QgsApplication.messageLog().logMessage(f'Task finished for {input_file} with result: {result}', 'Info')
    except Exception as e:
        QgsApplication.messageLog().logMessage(f'Task failed for {input_file}: {str(e)}', 'Info')

    progress_dialog.close()

for cluster in clusters:
    params['UROCK_MAP'] = os.path.join(Tmrt_base_path, ws_fields[cluster].format(season=season, spatial_res=spatial_res))

    cluster_path = os.path.join(Tmrt_base_path, f'{cluster}_{season}_{spatial_res}')

    tmrt_files = [os.path.join(cluster_path, f) for f in os.listdir(cluster_path) if f.startswith('Tmrt_20') and f.endswith('.tif')]

    tmrt_files.sort()

    if not tmrt_files:
        print(f'No valid Tmrt files found in {cluster_path}.')
        continue

    print(f'Found {len(tmrt_files)} Tmrt files in {cluster_path}.')

    for tmrt_file in tmrt_files:
        file_name = os.path.basename(tmrt_file)
        output_file = os.path.join(cluster_path, file_name.replace('Tmrt_20', 'UTCI_20'))

        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)

        run_solweig_utci_algorithm(tmrt_file, output_file)
