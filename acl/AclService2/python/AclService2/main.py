# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service
import ipaddress

class ServiceCallbacks(Service):

    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

        ipcount = 0
        vars = ncs.template.Variables()                    # Initiate variables container object
        vars.add('INTERFACE_ID', service.interface_id)     # Relay some variables over from yang to variables container
        vars.add('ACL_NAME', service.acl_name)
        vars.add('ACL_LINE', service.acl_line)
        vars.add('ACL_SUBNET_ADDRESS', service.acl_subnet_address)

        for dev in service.device:                         # Loop over the devices listed in the service instance instruction
            self.log.info('device: ', dev)
            vars.add('DEVICE', dev)                        # Fill in the DEVICE variable
            # IPAM:
            subnet = service.interface_subnet              # Calculate the IP address to be used for the interface
            interface_subnet_int = int(ipaddress.ip_address(subnet))
            interface_ip = str(ipaddress.IPv4Address(interface_subnet_int+ipcount*4+1))
            self.log.info('Interface IP: ', interface_ip)
            vars.add('INTERFACE_IP', interface_ip)

            ipcount = ipcount + 1                         # Increase counter
            template = ncs.template.Template(service)
            template.apply('AclService2-template', vars)  # Apply variables to template and run it

# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        self.log.info('Main RUNNING')
        self.register_service('AclService2-servicepoint', ServiceCallbacks)

    def teardown(self):
        self.log.info('Main FINISHED')
