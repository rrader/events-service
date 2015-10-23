from setuptools import setup

setup(
    name="admin-service",
    version='0.1',
    author='Roman Rader',
    author_email='antigluk@gmail.com',
    packages=["admin_service"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
    ]
)
