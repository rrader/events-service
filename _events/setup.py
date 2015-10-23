from setuptools import setup, find_packages

setup(name='events_service',
      version='0.1',
      description='Events service',
      platforms=['POSIX'],
      author='Roman Rader',
      author_email='antigluk@gmail.com',
      packages=find_packages(),
      include_package_data = True)
