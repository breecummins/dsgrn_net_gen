from distutils.core import setup

setup(
    name='dsgrn_net_gen',
    version='0.0.1',
    package_dir={'':'src'},
    packages = ['dsgrn_net_gen'],
    install_requires=["networkx","DSGRN"],
    author="Bree Cummins",
    url='https://github.com/breecummins/dsgrn_net_gen'
    )