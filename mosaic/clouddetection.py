"""
Cloud detection wrapper
"""

from s2cloudless import S2PixelCloudDetector

class Inference:
    """
    Extraction of a cloud mask from a Sentinel-2 image in input.
    """
    def __init__(self, all_bands=False):
        self.model = S2PixelCloudDetector(threshold=None, average_over=0, dilation_size=0, all_bands=all_bands)
    
    """
    image is expected to be of shape [H, W, 13] with all the Sentinel-2 Bands if 
    self.all_bands = True otherwise [H, W, C] with the bands required by s2cloudless
    """
    def predict(self, image):
        cloud_prob = self.model.get_cloud_probability_maps(image)
        return(cloud_prob)