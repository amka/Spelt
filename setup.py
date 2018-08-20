import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='Spelt',
    version='0.3.0',
    url='https://github.com/amka/spelt',
    license='MIT',
    author='Andrey Maksimov',
    author_email='meamka@ya.ru',
    description='Spelt is a small python application aimed to allow users '
    'to backup their photo from https://vk.com to local storage.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': ['spelt=spelt.__init__:run_app'],
    },
    packages=setuptools.find_packages(),
    install_requires=[
        'requests==2.19.1',
        'vk-api==11.0.0',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: POSIX"
    ],
)
