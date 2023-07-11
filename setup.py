#!/usr/bin/env python3
import os

from setuptools import setup


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


setup(
    name='restsysmon',
    version="0.0.0a0",
    description='IOT',
    url='https://github.com/OpenJarbas/restsysmon',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    packages=['restsysmon'],
    package_data={'': package_files('restsysmon')},
    install_requires=["psutil", "flask", "pulsectl",
                      "zeroconf", "screen-brightness-control"],
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
