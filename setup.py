from setuptools import setup

setup(
    name='pritunl',
    version='0.0.0',
    description='Simple openvpn server',
    author='Zachary Huff',
    author_email='zach.huff.386@gmail.com',
    url='https://github.com/zachhuff386/pritunl',
    keywords='openvpn',
    packages=['pritunl'],
    license='AGPLv3',
    zip_safe=False,
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Networking',
    ],
)
