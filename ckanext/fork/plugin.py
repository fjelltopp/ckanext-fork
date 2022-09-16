import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.fork.actions as fork_actions


class ForkPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

    # IActions
    def get_actions(self):
        return {
            'resource_autocomplete': fork_actions.resource_autocomplete
        }
