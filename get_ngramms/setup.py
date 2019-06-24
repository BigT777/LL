import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='calculate_collocations',  
     version='0.1',
     scripts=['colloc_lib.'] ,
     author="Nikolay Babakov",
     author_email="bbkhse@gmail.com",
     description="Collocation calculation for Russian and English languages",
     url="https://github.com/bbkjunior/calculate_collocations",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )