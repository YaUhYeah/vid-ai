from setuptools import setup, find_packages

setup(
    name="ai-edit-pro",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'moviepy>=1.0.3',
        'opencv-python>=4.5.0',
        'transformers>=4.15.0',
        'torch>=1.9.0',
        'numpy>=1.19.0',
        'ffmpeg-python>=0.2.0'
    ],
    entry_points={
        'console_scripts': [
            'ai-edit-pro=src.main:main',
        ],
    },
    author="OpenHands",
    author_email="openhands@all-hands.dev",
    description="AI-powered video editor for creating viral content",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="video editing, ai, machine learning, viral content",
    url="https://github.com/openhands/ai-edit-pro",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Video :: Non-Linear Editor",
    ],
    python_requires=">=3.8",
)