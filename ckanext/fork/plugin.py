import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.fork.actions as fork_actions
import ckanext.fork.validators as fork_validators


class ForkPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IValidators)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

    # IDatasetForm
    def create_package_schema(self):
        schema = super(ForkPlugin, self).create_package_schema()
        schema['resources'].update({
            'fork': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_fork'),
            ]
        })
        return schema

    def update_package_schema(self):
        schema = super(ForkPlugin, self).update_package_schema()
        schema['resources'].update({
            'fork': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('valid_fork')
            ]
        })
        return schema

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
            'package_update': fork_actions.package_create_update
        }

    # IValidators
    def get_validators(self):
        return {
            'valid_fork': fork_validators.valid_fork
        }
