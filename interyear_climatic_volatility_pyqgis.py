
###############################################################
########### Average Interannual Climatic Volatility ###########

'''
This code calculates Interannual Climatic Volatility averaged across months based on temperature of precipitation.

Assumptions:
- CRU TS file for temperature of precipitation
- 10 years
- averaging across all 12 months

The code may be modified to accommodate alternative assumptions.
'''

import os

nc_input_path = 'cru_ts4.07.1961.1970.pre.dat'
l_prefix_prec = nc_layer_name + ' — pre@' # layer prefix
nc_layer_input_pathname = 'NETCDF:' + os.path.join(nc_input_path, l_prefix_prec) + '.nc":pre'
#
output_path = ''
raster_for_calculation = 'prec'
raster_nameroot = raster_for_calculation

def av_formula_generator(month = 1,
                         l_prefix = l_prefix_prec, 
                         num_years = 10):
    '''
    This function creates the Interannual Average formula for the parameters dictionary for the QGIS Raster Calculator tool
    '''
    layer_number_list = list(range(month, month + num_years*12, 12))
    av_formula = ['"' + l_prefix + str(i) + '"' for i in layer_number_list[0]]
    av_formula = str(1)+'/{}*'.format(num_years) + '(' + ' + '.join(av_formula) + ')'
    return av_formula

def sd_formula_generator(month = 1,
                         l_prefix = l_prefix_prec, 
                         num_years = 10,
                         av_layer_name = ''):
    '''
    This function creates the Interannual StD formula for the parameters dictionary for the QGIS Raster Calculator tool
    '''
    av_formula = av_formula_generator(month = month,
                                      l_prefix = l_prefix, 
                                      num_years = num_years)
    
    layer_number_list = list(range(month, month + num_years*12, 12))
    sd_formula = ['("' + l_prefix + str(i) + '" - "' + av_layer_name + '")^2' for i in layer_number_list]
    sd_formula = 'sqrt(' + str(1)+'/{}*'.format(num_years) + '(' + ' + '.join(sd_formula) + '))'
    return sd_formula

def sd_raster_generator(month = 1,
                        l_prefix = l_prefix_prec, 
                        num_years = 10,
                        input_layer = [nc_layer_input_pathname],
                        output_path = output_path,
                        raster_nameroot = raster_nameroot):
                            
    # Temperature / Precipitation, Formula: Interannual Monthly Averages
    av_formula = av_formula_generator(month = month,
                                      l_prefix = l_prefix, 
                                      num_years = num_years)
                                      
    # Temperature / Precipitation, Calculation: Interannual Monthly Averages
    av_params = {'CELLSIZE' : 0, 
                   'CRS' : QgsCoordinateReferenceSystem('EPSG:4326'),
                   'EXPRESSION' : av_formula, 
                   'EXTENT' : None, 
                   'LAYERS' : input_layer, 
                   'OUTPUT' : os.path.join(output_path, 'av_' + raster_nameroot + str(month) + '.tiff') }
    av_raster = processing.run("qgis:rastercalculator", av_params)
    av_templayer = QgsRasterLayer(av_raster['OUTPUT'], 'av_templayer')
    QgsProject.instance().addMapLayer(av_templayer)
    
    # Temperature / Precipitation, Formula: Interannual Monthly StDs
    sd_formula = sd_formula_generator(month = month,
                                      l_prefix = l_prefix, 
                                      num_years = num_years, 
                                      av_layer_name = av_templayer.name() + '@1')
                                      
    # Temperature / Precipitation, Calculation: Interannual Monthly StDs
    sd_params = {'CELLSIZE' : 0, 
                   'CRS' : QgsCoordinateReferenceSystem('EPSG:4326'),
                   'EXPRESSION' : sd_formula, 
                   'EXTENT' : None, 
                   'LAYERS' : input_layer + [av_templayer], 
                   'OUTPUT' : os.path.join(output_path, 'sd_' + raster_nameroot + str(month) + '.tiff') }
    sd_raster = processing.run("qgis:rastercalculator", sd_params)
    sd_templayer = QgsRasterLayer(sd_raster['OUTPUT'], 'sd_templayer_mth' + str(month))
    QgsProject.instance().addMapLayer(sd_templayer)

sd_raster_generator(month = 5)


















