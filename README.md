[![Tests](https://github.com/jonathansberry/ckanext-fork/workflows/Tests/badge.svg?branch=main)](https://github.com/jonathansberry/ckanext-fork/actions)

# ckanext-fork

This extension offers tools to "fork" datasets and resources in CKAN.  To "fork" a dataset or resources is to duplicate/copy/clone the object from one part of the system to another, whilst making sure we record the action appropriatley in the metadata. 

The extension can only be used with CKAN instances using ckanext-blob-storage and Giftless as a file store. This is because duplicating data files is a costly and resource-intensive task in a traditional CKAN instance, but ckanext-blob-storage reduces this task to just duplicating metadata. 

For the purposes of forking a resource, this extension introduces three optional new metadata fields for resources: 
 - `fork_resource` records the resource_id of the forked_resource;
 - `fork_activity` records the activity ID of the forked resource's dataset at the time of forking;
 - `fork_synced` is a pseudo field generated when viewing a dataset that informs you whether the current data matches the forked data.

If `fork_resource` exists in a `package_update/create` request, or a `resource_update/create` request, then the blob_storage metadata will always be overwritten with the metadata of the specified forked_resource. To stop forking a resource, you must set this field to be Falsy. 


## Requirements

**TODO:** For example, you might want to mention here which versions of CKAN this
extension works with.

If your extension works across different versions you can add the following table:

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.6 and earlier | not tested    |
| 2.7             | not tested    |
| 2.8             | not tested    |
| 2.9             | not tested    |

Suggested values:

* "yes"
* "not tested" - I can't think of a reason why it wouldn't work
* "not yet" - there is an intention to get it working
* "no"


## Installation

**TODO:** Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-fork:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/jonathansberry/ckanext-fork.git
    cd ckanext-fork
    pip install -e .
	pip install -r requirements.txt

3. Add `fork` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config settings

None at present

**TODO:** Document any optional config settings here. For example:

	# The minimum number of hours to wait before re-checking a resource
	# (optional, default: 24).
	ckanext.fork.some_setting = some_default_value


## Developer installation

To install ckanext-fork for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/jonathansberry/ckanext-fork.git
    cd ckanext-fork
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Releasing a new version of ckanext-fork

If ckanext-fork should be available on PyPI you can follow these steps to publish a new version:

1. Update the version number in the `setup.py` file. See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version:

       python setup.py sdist bdist_wheel && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI:

       twine upload dist/*

5. Commit any outstanding changes:

       git commit -a
       git push

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:

       git tag 0.0.1
       git push --tags

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
