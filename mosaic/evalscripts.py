"""
Scripts used for extraction of the data from SentinelHub.
"""


"""
Sentinel-1
"""
SENTINEL1 = """
    //VERSION=3

    function setup() {
    return {
        input: [{
            bands: ["VV","dataMask"]
        }],
        output: {
            bands: 2,
            sampleType:"FLOAT32"
        },
        mosaicking: Mosaicking.ORBIT
    }
    }

    function evaluatePixel(samples) {
        return [
            samples[0].VV, 
            samples[0].dataMask
        ]
    }
"""

"""
Sentinel-2
"""
SENTINEL2 = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B09","B10","B11","B12","dataMask"],
                units: "DN"
            }],
            output: {
                bands: 14,
                sampleType: "INT16"
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B01,
                sample.B02,
                sample.B03,
                sample.B04,
                sample.B05,
                sample.B06,
                sample.B07,
                sample.B08,
                sample.B8A,
                sample.B09,
                sample.B10,
                sample.B11,
                sample.B12,
                sample.dataMask];
    }
"""

"""
Copernicus DEM
"""
DEM_COPERNICUS_30 = """
//VERSION=3
function setup() {
  return {
    input: ["DEM", "dataMask"],
    output:{
      id: "default",
      bands: 2,
      sampleType: SampleType.FLOAT32
    }
  }
}

function evaluatePixel(sample) {
  return [sample.DEM, sample.dataMask]
}
"""

"""
ESA World Cover
"""
WORLDCOVER = """
//VERSION=3

// This custom script visualises WorldCover map 

function setup() {
  return {
    input: ["Map", "dataMask"],
    output: { 
      bands: 2, 
      sampleType: "INT8"
    }
  }
}

function evaluatePixel(sample) {
  return [sample.Map, sample.dataMask];
}
"""