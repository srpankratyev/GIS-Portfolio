
## Brief Description of the Local Isolation Measure
# - The Local Isolation Measure is a spatially disaggregated measure of isolation.
# - It is computed for each point of the land surface.
# - The Local Isolation Measure is based on the Least Cost Path (LCP) algorithm, it computes the LCP for each point of the land surface grid to its nearest localities (i.e. neighboring points).
#
## Algorithm steps:
# - Load data (World Land Surface Grid, 1-by-1 degree + Cost Surface)
# - For each grid point:
#	- Extract a point for which local isolation will be computed (a.k.a. a start point)
#	- Extract points to which the LCP is computed (a.k.a. end points)
# - For each start point, compute LCP to each end point in its respective set of end points
# - For each start point, compute Local Isolation Measure as the average of Least Cost Paths to all its end points
# - Record that in the df_cntry dataframe
# 	- In df_cntry, the points of land surface grid are matched with country boundaries, however, they remain disaggregated
# - Export the df_cntry dataframe
# 
## Notes for usage:
# -  The code assumes that 'grid1dg_ctrd_cntry' file is loaded into QGIS, it is later used by 'QgsProject.instance().mapLayersByName()[0]' command
# - The code uses temporary layers heavily
# - Some of the instructions are below


import os
import pandas as pd
import numpy as np
import time

## Files and paths to them
#
# Data folder path
data_path = '' # insert your data path here
#
# Land surface grid, 1-by-1 degree
grid1dg_ctrds_cntry_file = os.path.join(data_path, 'vectors/grid1dg_wrldintersec', 'grid1dg_ctrd_cntry.shp') # Land surface raster map divided 
grid1dg = 'grid1dg'
#
# Cost surface for Least Cost Path calculation
costsurf_file = '' # insert the path/filename of the cost surface here


############ Auxiliary Functions (for convenience) ############
#
def bufpoint_id_generator(id, list_id_correction = bufcoordchng_rad2dg_grid1dg):
    id_list = [id + key for key in list_id_correction]
    expr_extrbyattr = 'id IN (' + ', '.join(str(x) for x in id_list) + ')'
    return {'buf_id_list': id_list, 'expr_extrbyattr' : expr_extrbyattr}

def pointexpr_generator(id):
    return 'id IN (' + str(id) + ')'





############ Local Isolation Algorithm ############
#
# Loading the world land surface grid file
lyr = QgsProject.instance().mapLayersByName('grid1dg_ctrd_cntry')[0]
cols = ['id', 'isocode']
datagen = ([f[col] for col in cols] for f in lyr.getFeatures())
df = pd.DataFrame.from_records(data=datagen, columns=cols)
#selec_point_ids = df[df['isocode'] == isocode]['id'].unique()
selec_isos = df['isocode'].unique()
#
# Creating dataframe with points (for filling average 
#df_cntry = df[df['isocode'] == isocode]
df_cntry = df
lcpvar_name = 'avlcpcost'
costcol = 'total cost'
df_cntry[lcpvar_name] = np.NaN
#
# Loop across all the centroids of the Land Surface Grid:
error_point_list, error_excpt_list = [], []
for point_id in selec_point_ids:

    # Extracting start point
    expr_startpoint = pointexpr_generator(point_id)
    params_start = {'INPUT' : grid1dg_ctrds_cntry_file, 
        'EXPRESSION': expr_startpoint,
        'OUTPUT' : 'memory:'}
    lcp_start = processing.run("native:extractbyexpression", params_start)
    QgsProject.instance().addMapLayer(lcp_start['OUTPUT']) # 
    
    # Extracting end-points
    expr_bufpoints = bufpoint_id_generator(point_id)['expr_extrbyattr']
    params_dests = {'INPUT': grid1dg_ctrds_cntry_file,
        'EXPRESSION': expr_bufpoints,
        'OUTPUT':'memory:'}
    lcp_dests = processing.run("native:extractbyexpression", params_dests)
    QgsProject.instance().addMapLayer(lcp_dests['OUTPUT'])
    
    # Computing Least Cost Path (LCP)
    # The code below might generate an exception for start points that don't have end points, so I run it under 'try' method and record point IDs that returned error
    try:
        params_lcp = { 'BOOLEAN_FIND_LEAST_PATH_TO_ALL_ENDS' : False, 
            'BOOLEAN_OUTPUT_LINEAR_REFERENCE' : False, 
            'INPUT_COST_RASTER' : costsurf_file, 
            'INPUT_END_LAYER' : lcp_dests['OUTPUT'], 
            'INPUT_RASTER_BAND' : 1, 
            'INPUT_START_LAYER' : lcp_start['OUTPUT'], 
            'OUTPUT' : 'memory:' }
        lcp_calc_result = processing.run("Cost distance analysis:Least Cost Path", params_lcp)
        QgsProject.instance().addMapLayer(lcp_calc_result['OUTPUT'])

        # Aggregating, Calculating average LCP
        datagen = ([f[costcol]] for f in lcp_calc_result['OUTPUT'].getFeatures())
        av_lcp_cal = np.mean(pd.DataFrame.from_records(data=datagen, columns=[costcol])[costcol])
        # Writing the result in the table
        df_cntry.loc[df_cntry['id'] == point_id, lcpvar_name] = av_lcp_cal
        # Deleting temporary files
        del lcp_dests, lcp_start, lcp_calc_result # deleting temporary results

        # Letting the computer catch a breath – otherwise it may overload
        time.sleep(2)
    except Exception as exc:
        error_point_list += [point_id]
        error_excpt_list += [exc]
# Writing the table on hard drive
df_cntry.to_csv(os.path.join(tab_output_path, 'locisol' + '_hmi' + '.csv'))
        
       
