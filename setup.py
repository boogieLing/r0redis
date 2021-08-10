from setuptools import setup, find_packages

with open('README.rst', 'r') as fp:
    long_description = fp.read()

setup(
    name='r0redis',
    version='0.4.5',
    description='Easily store, index, and modify Python dicts in Redis (with flexible searching)',
    long_description=long_description,
    author='r0',
    author_email='boogieLing_o@163.com',
    license='MIT',
    url='https://github.com/boogieLing/r0-redis-helper',
    download_url='https://github.com/boogieLing/r0-redis-helper/tarball/v0.4.1',
    packages=find_packages(),
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[
        'bg-helper',
        'click>=6.0',
        'dt-helper',
        'fs-helper',
        'hiredis==1.1.0',
        'input-helper',
        'pytz',
        'redis==3.5.3',
        'settings-helper',
        'ujson==4.0.1',
    ],
    include_package_data=True,
    package_dir={'': '.'},
    package_data={
        '': ['*.ini'],
    },
    entry_points={
        'console_scripts': [
            'rh-download-examples=r0redis.scripts.download_examples:main',
            'rh-download-scripts=r0redis.scripts.download_scripts:main',
            'rh-notes=r0redis.scripts.notes:main',
            'rh-shell=r0redis.scripts.shell:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
    ],
    keywords=['redis', 'dictionary', 'secondary index', 'model', 'log', 'prototype', 'helper']
)
