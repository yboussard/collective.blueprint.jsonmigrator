from setuptools import setup, find_packages
import os

version = '0.2.5'

setup(name='collective.blueprint.jsonmigrator',
      version=version,
      description="useful transmogrifier blueprints for large migrations from Plone, from 2.0 to 4.0",
      long_description=open("README.txt").read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='',
      author='garbas + yboussard',
      author_email='y.boussard@alterway.fr',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', 'collective.blueprint'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'simplejson',
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
