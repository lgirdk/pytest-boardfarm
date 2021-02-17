"""Placeholder for calling all boardfarm specific hooks."""
from boardfarm.plugins import BFPluginManager

# should be called by some main method.
pm = BFPluginManager()
pm.load_hook_specs()
pm.load_all_impl_classes()


def contingency_check(env_req, dev_mgr, env_helper):
    """Relay _hook_invoke to all boardfarm contingency hooks."""
    result = pm.hook.contingency_check(
        env_req=env_req, dev_mgr=dev_mgr, env_helper=env_helper
    )
    # returning the IP from the BF DOCSIS check_interface service
    ip = {}
    if result:
        for item in result:
            ip.update(item[-1])
    return ip
