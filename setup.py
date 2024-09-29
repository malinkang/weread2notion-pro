from setuptools import setup, find_packages

setup(
    name="weread2notionpro",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pendulum",
        "retrying",
        "notion-client",
        "github-heatmap",
    ],
    entry_points={
        "console_scripts": [
            "book = weread2notionpro.book:main",
            "weread = weread2notionpro.weread:main",
            "read_time = weread2notionpro.read_time:main",
        ],
    },
    author="malinkang",
    author_email="linkang.ma@gmail.com",
    description="自动将微信读书笔记和阅读记录同步到Notion",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/malinkang/weread2notion-pro",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
