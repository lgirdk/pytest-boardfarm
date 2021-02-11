"""Placeholder for calling all boardfarm specific hooks."""
from boardfarm.plugins import BFPluginManager

# should be called by some main method.
pm = BFPluginManager()
pm.load_hook_specs()
pm.load_all_impl_classes()


def contingency_check(env_req, dev_mgr):
    """Relay _hook_invoke to all boardfarm contingency hooks."""
    # this will return an empty list.
    pm.hook.contingency_check(env_req=env_req, dev_mgr=dev_mgr)
