from setuptools import setup
setup(
    name='mosaic',
    version='0.1.0',    
    description='A simple Python package for the creation of mosaics.',
    author='Federico Ricciuti',
    author_email='ricciuti.federico@gmail.com',
    packages=['mosaic'],
    install_requires=[
        'rasterio',
        'numpy', 
        'sentinelhub',
        'fiona',
        's2cloudless',
        'pytest',
        'dynamicworld @ git+https://github.com/DeepCube-org/dynamicworld.git',            
    ]
)