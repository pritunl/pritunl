from setuptools import setup
import pritunl

setup(
    name='pritunl',
    version=pritunl.__version__,
    description='Simple openvpn server',
    long_description=open('README.rst').read(),
    author='Zachary Huff',
    author_email='zach.huff.386@gmail.com',
    url='https://github.com/zachhuff386/pritunl',
    keywords='openvpn',
    packages=['pritunl'],
    license=open('LICENSE').read(),
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
