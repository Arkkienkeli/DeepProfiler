import setuptools


## TODO: add project dependencies (e.g., click, pickle, anything not standard library)
setuptools.setup(
    name="deep-profiler",
    version="0.0.0",
    author="Juan Caicedo",
    author_email="jcaicedo@gmail.com",  # TODO: use a personal email
    description=("Tools for representation learning in high throughput image collections"),
    license="BSD",
    keywords="",
    url="https://github.com/jccaicedo/DeepProfiler",
    packages=["deepprofiler"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=["scikit-image"],
    setup_requires=["pytest-runner"],
    tests_requires=["pytest"]
)
