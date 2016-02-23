from distutils.core import setup

import spelt

setup(
    name='Spelt',
    version=spelt.__version__,
    packages=['spelt'],
    url='https://github.com/amka/spelt',
    license='MIT',
    author='Andrey Maksimov',
    author_email='meamka@ya.ru',
    description='Spelt is a small python application aimed to allow users '
                'to backup their photo from https://vk.com to local storage.',
    entry_points={
        'console_scripts': ['spelt=spelt.__init__:run_app'],
    },
)
