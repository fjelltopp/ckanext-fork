import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.fork.actions as fork_actions
import ckanext.fork.validators as fork_validators
from ckanext.fork.helpers import get_parent_resource_details

class ForkPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

    # IDatasetForm
    def create_package_schema(self):
        schema = super(ForkPlugin, self).update_package_schema()
        schema.update({
            'fork_dataset': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_dataset_id')
            ],
            'fork_activity': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_activity_id'),
                toolkit.get_validator('check_forked_object')
            ]
        })
        schema['resources'].update({
            'fork_resource': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_resource_id'),
            ],
            'fork_activity': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_activity_id'),
                toolkit.get_validator('check_forked_object')
            ]
        })
        return schema()

    def update_package_schema(self):
        schema = super(ForkPlugin, self).update_package_schema()
        schema.update({
            'fork_dataset': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('dataset_field_not_changed')
            ],
            'fork_activity': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('dataset_field_not_changed')
            ]
        })
        schema['resources'].update({
            'fork_resource': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_resource_id'),
            ],
            'fork_activity': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_activity_id'),
                toolkit.get_validator('check_forked_object')
            ]
        })
        return schema()

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # IActions
    def get_actions(self):
        return {
            'resource_autocomplete': fork_actions.resource_autocomplete,
            'package_show': fork_actions.package_show,
            'package_create': fork_actions.package_create_update,
            'package_update': fork_actions.package_create_update,
            'dataset_fork': fork_actions.dataset_fork,
            'resource_fork': fork_actions.resource_fork
        }

    # IValidators
    def get_validators(self):
        return {
            'valid_resource_id': fork_validators.valid_resource_id,
            'valid_dataset_id': fork_validators.valid_dataset_id,
            'valid_activity_id': fork_validators.valid_activity_id,
            'check_forked_object': fork_validators.check_forked_object,
            'dataset_field_not_changed': fork_validators.dataset_field_not_changed
        }

    # ITemplateHelpers
    def get_helpers(self):
    # Template helper function names should begin with the name of the
    # extension they belong to, to avoid clashing with functions from
    # other extensions.
        return {'fork_get_parent_resource_details': get_parent_resource_details}
