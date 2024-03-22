from setuptools import find_packages, setup

# Dynamically read dependencies from requirements file
with open("requirements.txt") as f:
    requirements = f.readlines()

if __name__ == "__main__":
    setup(
        name="echoshader",
        author="Dingrui Lei",
        author_email="leidingrui426@gmail.com",
        maintainer="Dingrui Lei",
        maintainer_email="leidingrui426@gmail.com",
        description="Open Source Python package for building ocean sonar data visualizations.",
        url="https://github.com/OSOceanAcoustics/echoshader",
        packages=find_packages(),
        install_requires=requirements,
    )
