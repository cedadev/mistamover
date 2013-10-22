try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name = 'mistamover',
    version = "0.9.0",
    description = 'A tool for robust data transfer using existing protocols',
    author = 'Ag Stephens',
    author_email = 'ag.stephens@stfc.ac.uk',
    url = 'http://proj.badc.rl.ac.uk/cedaservices/wiki/JASMIN/MiStaMover',
    install_requires = [],
    dependency_links = [],
    packages = find_packages(exclude = ['ez_setup']),
    include_package_data = True,

    test_suite = '',
    tests_require = [],
    
    package_data = {},
    entry_points = """
    """,
)
