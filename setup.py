from setuptools import setup, find_packages


setup(
    name='scripts',
    description='Scripts to aux AppRecommender project',
    version='0.1',
    url='https://gitlab.com/TCC-AppRecommender/scripts',
    author='Luciano Prestes Cavalcanti',
    author_email='lucianopcbr@gmail.com',
    license='LICENSE.md',
    packages=find_packages(),
    setup_requires=['nose>=1.3'],
    test_suite='nose.collector',
)
