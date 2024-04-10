import ncs
import ncs.maapi as maapi
from ncs.maapi import CommitParams
import ncs.maagic as maagic


def id_request_async(service, svc_xpath, username, pool_name, allocation_name,
                       sync, alloc_sync,requested_id=-1, redeploy_type="default"):
    
    
    
    template = ncs.template.Template(service)
    vars = ncs.template.Variables()
    vars.add("POOL", pool_name)
    vars.add("ALLOCATIONID", allocation_name)
    vars.add("REDEPLOY_TYPE", redeploy_type)
    vars.add("USERNAME", username)
    vars.add("SERVICE", svc_xpath)
    vars.add("SYNC", sync)
    vars.add("SYNC_ALLOC", "true" if alloc_sync  else "")
    vars.add("REQUESTEDID", requested_id)
    template.apply('resource-manager-id-allocation', vars)
    
    

def id_request_sync(root, service, username, pool_name, allocation_name,
                     sync,requested_id=-1,):
    if root is None:
        raise Exception(
            "root node is required in API argument for synchronous id allocation request.")

    is_dry_run = CommitParams(maagic.get_trans(root).get_trans_params()).is_dry_run()
    internal_action = maagic.get_node(maagic.get_trans(root), "/ralloc:rm-action/sync-alloc-id")
    internal_action_input = internal_action.get_input()
    internal_action_input.pool = pool_name
    internal_action_input.allocid = allocation_name
    internal_action_input.user = username
    internal_action_input.owner = service._path
    internal_action_input.requestedId = requested_id
    internal_action_input.dryrun = is_dry_run
    internal_action_input.sync = sync
    internal_action_output = internal_action(internal_action_input)
    allocatedId = internal_action_output.allocatedId
    error = allocatedId if "Exception" in allocatedId  else ""

    variables = ncs.template.Variables()          
    variables.add('ERROR', error)
    variables.add('ALLOCID', allocatedId)
    variables.add('POOL', pool_name)
    variables.add('DRYRUN', "true" if is_dry_run else "")
    variables.add('ALLOCATIONID', allocation_name)

    template = ncs.template.Template(service)
    template.apply('resource-manager-id-allocation-response', variables)

def id_read_async(username, root, pool_name, allocation_name):
    # Look in the current transaction
    
    # Look in the current transaction
    id_pool_l = root.ralloc__resource_pools.id_pool

    if pool_name not in id_pool_l:
        raise LookupError("ID pool %s does not exist" % (pool_name))

    id_pool = id_pool_l[pool_name]

    if allocation_name not in id_pool.allocation:
        raise LookupError("allocation %s does not exist in pool %s" %
                          (allocation_name, pool_name))

    # Now we switch from the current trans to actually see if
    # we have received the alloc
    with maapi.single_read_trans(username, "system",
                                 db=ncs.OPERATIONAL) as th:
        id_pool_l = maagic.get_root(th).ralloc__resource_pools.id_pool

        if pool_name not in id_pool_l:
            return None

        id_pool = id_pool_l[pool_name]

        if allocation_name not in id_pool.allocation:
            return None

        alloc = id_pool.allocation[allocation_name]

        if alloc.response.id:
            return str(alloc.response.id)
        elif alloc.response.error:
            raise LookupError(alloc.response.error)
        else:
            return None
