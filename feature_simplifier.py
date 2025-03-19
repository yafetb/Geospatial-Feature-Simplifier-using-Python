import numpy as np
import geojson
import os
import math

geojson_file = 'us_airspace.geojson'  #it will be replaced by input
geojson_file = input('Please type the geojson file name in the same directory : ')
if len(geojson_file)==0:
    geojson_file = input('No file name typed! \nPlease type the geojson file name :  ')
elif geojson_file[-8:] != '.geojson':
    geojson_file = input('input should have .geojson extension. Please Type again! : ')

new_file_name =  'simplified_'+geojson_file


var_quantile = input("Enter the level of simplification from 0 to 1 :")
tolerance_value = 0.1   #will be replaced by calculation from quantiles


if os.path.isfile(geojson_file):
    # Open and read the JSON file
    with open(geojson_file, 'r') as file:
        data = geojson.load(file)
else:
    print('File not found! \nPlease make sure the geojson file exists in the folder and rerun the script.')


def getFeatures():
    return data['features']

features = getFeatures()

def angleChange(lon, lat,  next_lon, next_lat,  prev_lon, prev_lat):
    p_op = prev_lat -lat
    p_adj = prev_lon -lon
    n_op = lat - next_lat
    n_adj = lon - next_lon

    p_tan = math.atan2(p_op, p_adj)
    n_tan = math.atan2(n_op, n_adj)
    angle_diff = abs(p_tan-n_tan)*180/math.pi
    if angle_diff>180:
        angle_diff=360-angle_diff
    return angle_diff


varlist = []
import time
numboffeatures = 0
affected_coord = 0
total_coordinates = 0
def optimizer(feature_coord, get_quantiles): 
    global numboffeatures
    global affected_coord
    global total_coordinates
    coodlength =len(feature_coord)
    if not get_quantiles:
        numboffeatures += 1 
        total_coordinates += coodlength

    scanspot=coodlength-2  # the last item in the array should not be touched
    
    while (scanspot > 0):           # effectivly excludes the first index       
        #print (coords[scanspot].split()[0])       
        lon=float(feature_coord[scanspot][0])
        lat=float(feature_coord[scanspot][1])
        next_lon=float(feature_coord[scanspot+1][0])
        next_lat=float(feature_coord[scanspot+1][1])
        prev_lon=float(feature_coord[scanspot-1][0])
        prev_lat=float(feature_coord[scanspot-1][1])
        angle_diff = angleChange(lon, lat,  next_lon, next_lat,  prev_lon, prev_lat)
        lon_diff = abs(next_lon - lon) + abs(prev_lon-lon)
        lat_diff= abs(next_lat-lat) + abs(prev_lat-lat)
        
        variance=lat_diff + lon_diff        # number tells how close this vertex is with the nighbours
                            # used decending iteration bc edit affects index values
        #print("numb: "+ str(scanspot) + " - " +str(variance))
        varlist.append(variance)

        if not get_quantiles:
            # if angle_diff < 3 or variance < tolerance_value:
            if angle_diff < 3 or variance < tolerance_value:
                feature_coord.pop(scanspot)        # deletes this specific coordinate
                affected_coord +=1            
        scanspot -= 1   
    if not get_quantiles:
        print("numb: "+ str(numboffeatures)+" Coords: " + str(coodlength) + "  Affected: " + str(affected_coord),  end = '\r')
    else:
        print('Number of features analysed : ' + str(numboffeatures), end = '\r')
        time.sleep(0.0002)


def processOptimization(features, get_quantiles):        
    for items in features:
        if not get_quantiles:
            fProperties = items['properties']             
            fProperties.pop('WKT', None)
        geometry = items['geometry']
        fType = geometry['type']
        coordinates = geometry['coordinates']
        if fType == 'MultiPolygon':        
            for feature_group in coordinates:       
                for feature_coord in feature_group:
                    optimizer(feature_coord, get_quantiles)
        elif fType == 'MultiLineString' or fType == 'Polygon':
            for feature_coord in coordinates:
                optimizer(feature_coord, get_quantiles)
        else:
            print('Optimization is not done for ' + fType + ' type features!')

       
processOptimization(features, True)
tolerance_value = np.quantile(varlist, float(var_quantile)) 
processOptimization(features, False)

print("Number of features : "+ str(numboffeatures)+", Coordinates Count: " + str(total_coordinates) + ",  Affected Coordinates: " + str(affected_coord))
percent_affected = round((affected_coord/total_coordinates)*100, 1)
print(str(percent_affected) + '% of coordinate points are affected.')


with open(new_file_name, 'w') as f:
    geojson.dump(data, f)
    print('Output file name "' + new_file_name +'"')

