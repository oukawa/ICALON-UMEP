# Run SOLWEIG from the QGIS/OSGeo Shell
# G. Oukawa - May 2024

import os
import processing
from qgis.core import QgsApplication, QgsProcessingFeedback
from qgis.analysis import QgsNativeAlgorithms
from PyQt5.QtWidgets import QProgressDialog

QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

spatial_res = input("Enter spatial resolution (2- or 10-m): ")
if spatial_res not in ('2', '10'):
    print("Invalid spatial resolution.")
    exit(1)
seasons = ['winter', 'summer']
season = input("Select season (winter/summer): ")
if season not in seasons:
    print("Invalid season.")
    exit(1)

met_base_path = 'X:/UMEP/Meteorology_Clusters/'
output_base_path = 'X:/UMEP/'

params = {
    'INPUT_DSM': f'X:/UMEP/Input_Rasters_{spatial_res}m/DSM.tif',
    'INPUT_DEM': f'X:/UMEP/Input_Rasters_{spatial_res}m/DEM.tif',
    'INPUT_HEIGHT': f'X:/UMEP/Input_Rasters_{spatial_res}m/WallHeight.tif',
    'INPUT_ASPECT': f'X:/UMEP/Input_Rasters_{spatial_res}m/WallAspect.tif',
    'INPUT_LC': f'X:/UMEP/Input_Rasters_{spatial_res}m/LandClass.tif',
    'INPUT_SVF': f'X:/UMEP/Input_Rasters_{spatial_res}m/SVF.zip',

    'ALBEDO_GROUND': 0.15, # Default parameters (ignored when using LC raster)
    'ALBEDO_WALLS': 0.2, # Default parameters (ignored when using LC raster)
    'EMIS_GROUND': 0.95, # Default parameters (ignored when using LC raster)
    'EMIS_WALLS': 0.9, # Default parameters (ignored when using LC raster)

    'ONLYGLOBAL': True, # Estimate diffuse and direct shortwave radiation
    'UTC': -3, # Convert to local time
    
    'INPUT_ANISO': '',

    'INPUT_CDSM': f'X:/UMEP/Input_Rasters_{spatial_res}m/CDSM.tif', # Use tree canopy DSM (optional)
    'INPUT_TDSM': f'X:/UMEP/Input_Rasters_{spatial_res}m/TDSM.tif', # Use trunk DSM (optional)
    'CONIFER_TREES': False, # Deciduous trees as default
    'LEAF_START': 280, # Set to southern hemisphere
    'LEAF_END': 120, # Set to southern hemisphere
    'INPUT_THEIGHT': 25, # Percent of canopy height (only used if no TDSM is provided)
    'TRANS_VEG': 7,

    'USE_LC_BUILD': False,

    'OUTPUT_KDOWN': False,
    'OUTPUT_KUP': False,
    'OUTPUT_LDOWN': False,
    'OUTPUT_LUP': False,
    'OUTPUT_SH': False,
    'OUTPUT_TMRT': True,
    'OUTPUT_TREEPLANTER': True, # Option to save additional rasters needed to calculate UTCI
    'SAVE_BUILD': False, # Save building grid
}

clusters = ['C1', 'C2', 'C3']

for cluster in clusters:
    
    met_file = f'{met_base_path}{season}_met_{cluster}.txt'
    output_dir = f'{output_base_path}{cluster}_{season}_{spatial_res}'

    params['INPUTMET'] = met_file
    params['OUTPUT_DIR'] = output_dir

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    progress_dialog = QProgressDialog("Running SOLWEIG...", "Abort", 0, 100)
    progress_dialog.setWindowTitle("Processing")
    progress_dialog.setModal(True)
    progress_dialog.show()

    class Feedback(QgsProcessingFeedback):
        def setProgress(self, progress):
            progress_dialog.setValue(progress)

    feedback = Feedback()

    try:
        result = processing.run("umep:Outdoor Thermal Comfort: SOLWEIG", params, feedback=feedback)
        QgsApplication.messageLog().logMessage(f"Task finished with result: {result}", 'Info')
    except Exception as e:
        QgsApplication.messageLog().logMessage(f"Task failed: {str(e)}", 'Info')

    progress_dialog.close()
