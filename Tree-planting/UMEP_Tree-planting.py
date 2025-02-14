# Tree-planting algorithm (version 1.2)
# G. Oukawa - Oct 2024

import sys
import random
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Note that the input files are in .gpkg format with UTM projection (in meters)  
# .SHP files can also be used
trees = gpd.read_file('X:/UMEP/Trees/Trees.gpkg')
free_public_spaces = gpd.read_file('X:/UMEP/Trees/Planting_spaces.gpkg')
power_lines = gpd.read_file('X:/UMEP/Trees/Power_lines.gpkg')
buildings = gpd.read_file('X:/UMEP/Trees/Buildings.gpkg')

# Select which scenario to run
run_scenario = input('Use vacant lots? (yes/no): ')
if run_scenario == 'yes':
    planting_zones = free_public_spaces.copy()
    vacant_lots = gpd.read_file('X:/UMEP/Trees/Vacant_lots.gpkg')
    planting_zones = pd.concat([planting_zones, vacant_lots], ignore_index=True)
    scenario = 'with_vacant'

elif run_scenario == 'no':
    planting_zones = free_public_spaces.copy()
    scenario = 'public_only'

else:
    print('Invalid option')
    sys.exit()

# Size tiers with diameter-height pairing
sorted_trees = trees.sort_values('diameter').reset_index(drop=True)

percentiles = [0.8, 0.75, 0.7, 0.65,
               0.6, 0.55, 0.5, 0.45,
               0.4, 0.35, 0.3, 0.25,
               0.2]

size_tiers = [(sorted_trees.iloc[int(p*(len(sorted_trees)-1))]['diameter'],
              sorted_trees.iloc[int(p*(len(sorted_trees)-1))]['height'],
              sorted_trees.iloc[int(p*(len(sorted_trees)-1))]['trunk_height'])
             for p in percentiles]

def tree_planting(polygon, existing_trees, buildings, power_lines, size_tiers, max_attempts=50):
    for attempt in range(max_attempts):
        tier_idx = min(attempt, len(size_tiers)-1)
        current_diam, current_height, current_trunk = size_tiers[tier_idx]
        
        random_point = Point(random.uniform(polygon.bounds[0], polygon.bounds[2]),
                          random.uniform(polygon.bounds[1], polygon.bounds[3]))
        
        if polygon.contains(random_point):
            collision = any(random_point.distance(t.geometry) < (t.diameter + current_diam)/2 
                          for t in existing_trees.itertuples())
            
            if not collision:
                buffer = random_point.buffer(current_diam/2)
                if not buildings.intersects(buffer).any() and not power_lines.intersects(buffer).any():
                    return random_point, current_height, current_diam, current_trunk
    return None

# Step 1: Replace smaller trees (height < 5 m)
original_count = len(trees)
replacement_count = 0

for idx, tree in trees.iterrows():
    if tree.height < 5:
        current_zone = free_public_spaces[free_public_spaces.contains(tree.geometry)]
        zone = current_zone.geometry.iloc[0] if not current_zone.empty else random.choice(planting_zones.geometry)
        
        new_tree = tree_planting(zone, trees, buildings, power_lines, size_tiers)
        if new_tree:
            trees.at[idx, 'geometry'] = new_tree[0]
            trees.at[idx, 'height'] = new_tree[1]
            trees.at[idx, 'diameter'] = new_tree[2]
            trees.at[idx, 'trunk_height'] = new_tree[3]
            replacement_count += 1

# Step 2: Add new trees
max_new_trees = original_count
new_trees = []
consecutive_failures = 0

for i in range(max_new_trees):
    zone = random.choice(planting_zones.geometry)
    new_tree = tree_planting(zone, trees, buildings, power_lines, size_tiers)
    
    if new_tree:
        new_trees.append({
            'geometry': new_tree[0],
            'height': new_tree[1],
            'diameter': new_tree[2],
            'trunk_height': new_tree[3]
        })
        consecutive_failures = 0
    else:
        consecutive_failures += 1
        if consecutive_failures >= 10:
            print(f'Stopped early at {i+1} trees')
            break

final_trees = pd.concat([trees, gpd.GeoDataFrame(new_trees, crs=trees.crs)])
final_trees.to_file(f'X:/UMEP/Trees/Trees_{scenario}.gpkg', driver='GPKG')

run_generator = input('Generate new CDSM and TDSM rasters? (yes/no): ')

if run_generator == 'yes':

    import processing
    from qgis.core import QgsApplication, QgsProcessingFeedback
    from qgis.analysis import QgsNativeAlgorithms
    from PyQt5.QtWidgets import QProgressDialog

    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    # Tree generator parameters
    params = {
        'INPUT_POINTLAYER': f'X:/UMEP/Trees/Trees_{scenario}.gpkg',
        'INPUT_BUILD': None, 
        'INPUT_DSM': None, 
        'INPUT_DEM': None, 
        'INPUT_CDSM': None, 
        'INPUT_TDSM': None, 
        'DIA': 'diameter', 
        'TOT_HEIGHT': 'height',
        'TRUNK_HEIGHT': 'trunk_height',
        'TREE_TYPE': 'tree_type', 
        'CDSM_GRID_OUT': 'X:/UMEP/Trees/CDSM_{scenario}.tif',
        'TDSM_GRID_OUT': 'X:/UMEP/Trees/TDSM_{scenario}.tif',
    }

    progress_dialog = QProgressDialog("Running Tree generator...", "Abort", 0, 100)
    progress_dialog.setWindowTitle("Processing")
    progress_dialog.setModal(True)
    progress_dialog.show()

    class Feedback(QgsProcessingFeedback):
        def setProgress(self, progress):
            progress_dialog.setValue(progress)

    feedback = Feedback()

    try:
        result = processing.run("umep:Spatial Data: Tree Generator", params, feedback=feedback)
        QgsApplication.messageLog().logMessage(f"Task finished with result: {result}", 'Info')
    except Exception as e:
        QgsApplication.messageLog().logMessage(f"Task failed: {str(e)}", 'Info')

    progress_dialog.close()

else:
    sys.exit()