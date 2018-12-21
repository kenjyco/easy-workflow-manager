from setuptools import setup, find_packages


with open('README.rst', 'r') as fp:
    long_description = fp.read()

setup(
    name='easy-workflow-manager',
    version='0.0.8',
    description='Tools to support a straightforward branch/qa/merge/release process',
    long_description=long_description,
    author='Ken',
    author_email='kenjyco@gmail.com',
    license='MIT',
    url='https://github.com/kenjyco/easy-workflow-manager',
    download_url='https://github.com/kenjyco/easy-workflow-manager/tarball/v0.0.8',
    packages=find_packages(),
    install_requires=[
        'input-helper',
        'settings-helper',
        'dt-helper',
        'bg-helper',
        'fs-helper',
        'click>=6.0',
    ],
    include_package_data=True,
    package_dir={'': '.'},
    package_data={
        '': ['*.ini'],
    },
    entry_points={
        'console_scripts': [
            'ewm-new-branch-from-source=easy_workflow_manager.scripts.new_branch_from_source:main',
            'ewm-branch-from=easy_workflow_manager.scripts.branch_from:main',
            'ewm-deploy-to-qa=easy_workflow_manager.scripts.deploy_to_qa:main',
            'ewm-qa-to-source=easy_workflow_manager.scripts.qa_to_source:main',
            'ewm-clear-qa=easy_workflow_manager.scripts.clear_qa:main',
            'ewm-show-qa=easy_workflow_manager.scripts.show_qa:main',
            'ewm-show-branches=easy_workflow_manager.scripts.show_branches:main',
            'ewm-repo-info=easy_workflow_manager.scripts.show_repo_info:main',
            'ewm-update-branch=easy_workflow_manager.scripts.update_branch:main',
            'ewm-tag-release=easy_workflow_manager.scripts.tag_release:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
    ],
    keywords=['git', 'workflow', 'helper', 'branch', 'merge', 'qa', 'deploy']
)
