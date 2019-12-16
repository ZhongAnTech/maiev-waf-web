#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import ansible.playbook
import ansible.inventory
import ansible.runner
from utils.log import log_setting
from ansible import callbacks
from ansible import utils

logger = log_setting("asb")


def ansble_adhoc_run(ans_mod, ans_host, ans_user, module_args):

    inventory = ansible.inventory.Inventory()
    print inventory.basedir()
    logger.info("Executing Ansible Runner on %s with module %s" %(ans_host, ans_mod))
    run_adhoc = ansible.runner.Runner(
                 module_name=ans_mod,
                 module_args=module_args,
                 pattern=ans_host,
                 inventory=inventory,
                 remote_user=ans_user,
                 ).run()
    logger.info("Executing Ansible Runner on %s with module %s" %(ans_host, ans_mod))
    logger.info("Runner execution completed with Result: %s" %run_adhoc)
    return run_adhoc


ret = ansble_adhoc_run('shell', '', 'admin', 'uname')
print ret