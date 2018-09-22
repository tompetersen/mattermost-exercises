from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='mattermost-exercises',
    version='0.0.2',
    keywords='mattermost bot exercising',
    description='Exercising with the help of a mattermost bot',
    long_description=readme(),
    url='https://github.com/tompetersen/mattermost-exercises',
    author='Tom Petersen',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Chat',
    ],
    install_requires=[
        'mattermostdriver'
    ],
)
