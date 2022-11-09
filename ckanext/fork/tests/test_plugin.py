import ckanext.fork.plugin as plugin


def test_plugin():
    p = plugin.ForkPlugin()
    assert p
