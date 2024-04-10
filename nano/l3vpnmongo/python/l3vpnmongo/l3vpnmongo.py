# -*- mode: python; python-indent: 4 -*-
import ncs
import math
from .mongo_vpnid import id_allocator

# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class IdAllocationNanoService(ncs.application.NanoService):
    @ncs.application.NanoService.create
    def cb_nano_create(self, tctx, root, service, plan, component, state, proplist, component_proplist):
        self.log.debug("NanoService create ", state)

        vpn_id = id_allocator.id_request(service.name)
        root.mongo_vpnid_alloc.append({"vpn_name": service.name})
        root.mongo_vpnid_alloc[service.name].vpn_id = vpn_id
        self.log.info(f'VPN ID: {vpn_id})')

class L3MPLSNanoService(ncs.application.NanoService):
    @ncs.application.NanoService.create
    def cb_nano_create(self, tctx, root, service, plan, component, state, proplist, component_proplist):
        self.log.debug("NanoService create ", state)

        vpn_id = root.mongo_vpnid_alloc[service.name].vpn_id
        self.log.info(f'Vpn ID read: {vpn_id}')

        for link in service.link:
            vpn_link = {'pe-ip': link.pe_ip, 'ce-ip': link.ce_ip, 'rip-net': link.rip_net}
            pe_ip_o2 = 16 + math.ceil(link.link_id / 4096)
            pe_ip_o3 = math.ceil((link.link_id % 4096) / 16)
            pe_ip_o4 = (link.link_id % 16) * 16 + 1
            ce_ip_o4 = pe_ip_o4 + 1

            if not link.pe_ip:
                vpn_link['pe-ip'] = f'172.{pe_ip_o2}.{pe_ip_o3}.{pe_ip_o4}'
            if not link.ce_ip:
                vpn_link['ce-ip'] = f'172.{pe_ip_o2}.{pe_ip_o3}.{ce_ip_o4}'
            if not link.rip_net:
                vpn_link['rip-net'] = f'172.{pe_ip_o2}.0.0'
            
            tvars = ncs.template.Variables()
            template = ncs.template.Template(service)
            tvars.add('VPNID', vpn_id)
            tvars.add('DEVICE', link.device)
            tvars.add('PEIP', vpn_link['pe-ip'])
            tvars.add('CEIP', vpn_link['ce-ip'])
            tvars.add('ROUTING-PROTOCOL', link.routing_protocol)

            if link.routing_protocol == 'rip':
                tvars.add('RIP-NET', vpn_link['rip-net'])
            else:
                tvars.add('RIP-NET', '')
            tvars.add('INTERFACE', link.interface)
            self.log.info(f'Service create(applying template for device {link.device})')
            template.apply('l3vpndynid-template', tvars)

        return proplist

# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class L3VpnMongo(ncs.application.Application):
    def setup(self):
        self.log.info('L3VpnMongo RUNNING')
        self.register_nano_service('l3vpnmongo-servicepoint', 'l3vpnmongo:l3vpnmongo', 'l3vpnmongo:id-allocated', IdAllocationNanoService)
        self.register_nano_service('l3vpnmongo-servicepoint', 'l3vpnmongo:l3vpnmongo', 'l3vpnmongo:l3vpnmongo-configured', L3MPLSNanoService)

    def teardown(self):
        self.log.info('L3VpnMongo FINISHED')
