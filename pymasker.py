import os
import argparse
import numpy as np

class Masker(object):
    '''Provides access to functions that produces masks from remote sensing image, according to its bit structure.'''

    def __init__(self, band, *var):

        if type(band) is str:
            if len(var) > 0:
                self.load_file(band, var[0])
            else:
                self.load_file(band)
        else:
            self.load_data(band)

    def load_file(self, file_path, band_num = 0):
        '''Load the QA file from a give path

        Parameters
            file_path	-	Path of band file.
            band_num	-	Number of band.
        '''
        import gdal

        self.file_path = file_path
        extension = os.path.splitext(file_path)[1].lower()

        # load file according to the file format.
        if extension == '.hdf':
            dataset = gdal.Open(file_path)
            subdataset = dataset.GetSubDatasets()[band_num][0]
            self.band_data = gdal.Open(subdataset).ReadAsArray()
        else:
            bandfile = gdal.Open(file_path)
            self.band_data = bandfile.GetRasterBand(1).ReadAsArray()

    def load_data(self, array):
        '''Load the BQA ban from a np.array

        Parameters
            array		-	Numpy array that contains the band data.
        '''
        self.file_path = None
        self.band_data = array

    def get_mask(self, bit_pos, bit_len, value):
        '''Generates mask with given bit information.

        Parameters
            bit_pos		-	Position of the specific QA bits in the value string.
            bit_len		-	Length of the specific QA bits.
            value  		-	A value indicating the desired condition.
        '''
        bitlen = int('1' * bit_len, 2)

        if type(value) == str:
            value = int(value, 2)

        pos_value = bitlen << bit_pos
        con_value = value << bit_pos
        mask = (self.band_data & pos_value) == con_value

        return mask.astype(int)

    def save_tif(self, mask, file_path):
        '''Save the given mask as a .tif file.

        Parameters
            mask 		-	A mask generated with masker.
            file_path	-	Path of .tif file.
        '''
        import gdal

        driver = gdal.GetDriverByName('GTiff')

        x_pixels = mask.shape[1]
        y_pixels = mask.shape[0]

        dataset = driver.Create(file_path, x_pixels, y_pixels, 1, gdal.GDT_Int32)

        if self.file_path is not None:
            extension = os.path.splitext(self.file_path)[1].lower()
            if extension == '.hdf':
                hdfdataset = gdal.Open(self.file_path)
                subdataset = hdfdataset.GetSubDatasets()[0][0]
                bandfile = gdal.Open(subdataset)
            else:
                bandfile = gdal.Open(self.file_path)

            dataset.SetGeoTransform(bandfile.GetGeoTransform())
            dataset.SetProjection(bandfile.GetProjectionRef())

        dataset.GetRasterBand(1).WriteArray(mask)
        dataset.FlushCache()

class LandsatConfidence(object):
    '''Level of confidence that a condition exists

    high 		-	Algorithm has high confidence that this condition exists (67-100 percent confidence).
    medium 		-	Algorithm has medium confidence that this condition exists (34-66 percent confidence).
    low 		-	Algorithm has low to no confidence that this condition exists (0-33 percent confidence)
    undefined	- 	Algorithm did not determine the status of this condition.
    none		-	Nothing.
    '''
    high = 3
    medium = 2
    low = 1
    undefined = 0
    none = -1

class LandsatMasker(Masker):
    '''Provides access to functions that produces masks from quality assessment band of Landsat 8.'''

    def get_cloud_mask(self, conf, cumulative = False):
        '''Generate a cloud mask.

        Parameters
            conf		-	Level of confidence that cloud exists.
            cumulative	-	A Boolean value indicating whether the masking is cumulative.

        Return
            mask 		-	A two-dimension binary mask.
        '''

        return self.__get_mask(14, 3, conf, cumulative).astype(int)

    def get_cirrus_mask(self, conf, cumulative = False):
        '''Generate a cirrus mask.

        Parameters
            conf		-	Level of confidence that cloud exists.
            cumulative	-	A Boolean value indicating whether the masking is cumulative.

        Return
            mask 		-	A two-dimension binary mask.
        '''

        return self.__get_mask(12, 3, conf, cumulative).astype(int)

    def get_veg_mask(self, conf, cumulative = False):
        '''Generate a vegetation mask.

        Parameters
            conf		-	Level of confidence that veg exists.
            cumulative	-	A Boolean value indicating whether the masking is cumulative.

        Return
            mask 		-	A two-dimension binary mask.
        '''
        return self.__get_mask(8, 3, conf, cumulative).astype(int)

    def get_water_mask(self, conf, cumulative = False):
        '''Generate a water body mask.

        Parameters
            conf		-	Level of confidence that water body exists.
            cumulative	-	A Boolean value indicating whether the masking is cumulative.

        Return
            mask 		-	A two-dimension binary mask.
        '''
        return self.__get_mask(4, 3, conf, cumulative).astype(int)

    def get_snow_mask(self, conf, cumulative = False):
        '''Generate a water body mask.

        Parameters
            conf		-	Level of confidence that snow/ice exists.
            cumulative	-	A Boolean value indicating whether the masking is cumulative.

        Return
            mask 		-	A two-dimension binary mask.
        '''
        return self.__get_mask(10, 3, conf, cumulative).astype(int)

    def get_fill_mask(self):
        '''Generate a fill mask.

        Return
            mask        -   A two-dimensional binary mask
        '''
        return self.__get_mask(0, 1, 1, False)

    def get_multi_mask(self,
        cloud = LandsatConfidence.none, cloud_cum = False,
        cirrus = LandsatConfidence.none, cirrus_cum = False,
        snow = LandsatConfidence.none, snow_cum = False,
        veg = LandsatConfidence.none, veg_cum = False,
        water = LandsatConfidence.none, water_cum = False,
        inclusive = False):
        '''Get mask with multiple conditions.

        Parameters
            cloud		-	Level of confidence that cloud exists. (default: confidence.none)
            cloud_cum	-	A Boolean value indicating whether the cloud masking is cumulative.
            cirrus		-	Level of confidence that cirrus exists. (default: confidence.none)
            cirrus_cum	-	A Boolean value indicating whether the cirrus masking is cumulative. (default: False)
            snow		-	Level of confidence that snow/ice exists. (default: confidence.none)
            snow_cum 	-	A Boolean value indicating whether the snow masking is cumulative. (default: False)
            veg			-	Level of confidence that vegetation exists. (default: confidence.none)
            veg_cum		-	A Boolean value indicating whether the vegetation masking is cumulative. (default: False)
            water		-	Level of confidence that water body exists. (default: confidence.none)
            water_cum	-	A Boolean value indicating whether the water body masking is cumulative. (default: False)
            inclusive	-	A Boolean value indicating whether the masking is inclusive or exclusive.

        Returns
            mask 		-	A two-dimension binary mask.
        '''

        # Basic mask
        if inclusive:
            final_mask = self.band_data < 0
        else:
            final_mask = self.band_data >= 0

        tasks = [
            [8, veg, veg_cum],     # veg pixel
            [10, snow, snow_cum],    # Snow pixel
            [12, cirrus, cirrus_cum],    # Cirrus pixel
            [14, cloud, cloud_cum],    # Cloud pixel
            [4, water, water_cum]      # Water body pixel
        ]

        for task in tasks:
            mask = self.__get_mask(task[0], 3, task[1], task[2])

            if inclusive:
                final_mask = np.logical_or(final_mask, mask)
            else:
                final_mask = np.logical_and(final_mask, mask)

        return final_mask.astype(int)

    def __get_mask(self, bit_loc, bit_len, value, cumulative):
        '''Get mask with specific parameters.

        Parameters
            bit_loc		-	Location of the specific QA bits in the value string.
            bit_len		-	Length of the specific QA bits.
            value  		-	A value indicating the desired condition.
            cumulative	-	A Boolean value indicating whether the masking is cumulative.
        '''

        pos_value = bit_len << bit_loc
        con_value = value << bit_loc

        if cumulative:
            mask = (self.band_data & pos_value) >= con_value
        else:
            mask = (self.band_data & pos_value) == con_value

        return mask

class ModisQuality(object):
    '''Level of data quality of MODIS land products at each pixel.

    high		-	Corrected product produced at ideal quality for all bands.
    medium		-	Corrected product produced at less than ideal quality for some or all bands.
    low 		-	Corrected product not produced due to some reasons for some or all bands.
    low_cloud	-	Corrected product not produced due to cloud effects for all bands.
    '''

    high = 0
    medium = 1
    low = 2
    low_cloud = 3

class ModisMasker(Masker):
    '''Provides access to functions that produce QA masks from quality assessment band of MODIS land products.'''

    def __init__(self, file_path):
        super(ModisMasker, self).__init__(file_path, 3)

    def get_qa_mask(self, quality):
        '''Get a quality mask.

        Parameters
            quality		-	Desired level of data quality.

        Returns
            mask 		-	A two-dimension binary mask.
        '''

        return self.get_mask(0, 2, quality).astype(int)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', help='source type: landsat, modis', type=str)
    parser.add_argument('-i', '--input', help='input image file path', type=str)
    parser.add_argument('-o', '--output', help='output raster path')

    # landsat arguments
    parser.add_argument('-c', '--confidence', help='level of confidence that a condition exists in a landsat image: high, medium, low, undefined, none', action='store')
    parser.add_argument('-t', '--target', help='target object: cloud, cirrus, water, vegetation, snow', action='store')

    # modis argument
    parser.add_argument('-q', '--quality', help='Level of data quality of MODIS land products at each pixel: high, medium, low, low_cloud', action='store')

    args = parser.parse_args()

    if args.source == 'landsat':
        conf_value = {
            'high': LandsatConfidence.high,
            'medium': LandsatConfidence.medium,
            'low': LandsatConfidence.low,
            'undefined': LandsatConfidence.undefined,
            'none': LandsatConfidence.none
        }

        masker = LandsatMasker(args.input)

        if args.target == 'cloud':
            mask = masker.get_cloud_mask(conf_value[args.confidence])
        elif args.target == 'cirrus':
            mask = masker.get_cirrus_mask(conf_value[args.confidence])
        elif args.target == 'water':
            mask = masker.get_water_mask(conf_value[args.confidence])
        elif args.target == 'vegetation':
            mask = masker.get_veg_mask(conf_value[args.confidence])
        elif args.target == 'snow':
            mask = masker.get_snow_mask(conf_value[args.confidence])
        else:
            raise Exception('Masker type %s is unrecongized.' % args.target)

        masker.save_tif(mask, args.output)

    elif args.source == 'modis':
        quality_value = {
            'high': ModisQuality.high,
            'medium': ModisQuality.medium,
            'low': ModisQuality.low,
            'low_cloud': ModisQuality.low_cloud
        }

        masker = ModisMasker(args.input)
        mask = masker.get_qa_mask(quality_value[args.quality])
        masker.save_tif(mask, args.output)
    else:
        raise Exception('Given source %s is unrecongized.' % args.source)

if __name__ == "__main__":
    main()
