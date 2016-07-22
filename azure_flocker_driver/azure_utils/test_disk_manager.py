from arm_disk_manager import DiskManager
from auth_token import AuthToken
from twisted.trial import unittest
from eliot import Logger
from azure.storage.blob import BlobService
from azure.mgmt.common import SubscriptionCloudCredentials
from azure.mgmt.resource import ResourceManagementClient
import os
import yaml

azure_config = None
_logger = Logger()
config_file_path = os.environ.get('AZURE_CONFIG_FILE')

if config_file_path is not None:
        config_file = open(config_file_path)
        config = yaml.load(config_file.read())
        azure_config = config['azure_settings']


class DiskCreateTestCase(unittest.TestCase):

        def setUp(self):
            auth_token = AuthToken.get_token_from_client_credentials(
                azure_config['subscription_id'],
                azure_config['tenant_id'],
                azure_config['client_id'],
                azure_config['client_secret'])
            creds = SubscriptionCloudCredentials(
                azure_config['subscription_id'],
                auth_token)
            self._resource_client = ResourceManagementClient(creds)
            self._azure_storage_client = BlobService(
                azure_config['storage_account_name'],
                azure_config['storage_account_key'])
            self._manager = DiskManager(
                self._resource_client,
                self._azure_storage_client,
                azure_config['storage_account_container'],
                azure_config['group_name'],
                azure_config['location'])

        def test_create_blank_vhd(self):
            link = self._manager.create_disk(azure_config['test_vhd_name'],
                                             2)
            self.assertEqual(link,
                             'https://' +
                             self._azure_storage_client.account_name +
                             '.blob.core.windows.net/' +
                             azure_config['storage_account_container'] +
                             '/' + azure_config['test_vhd_name'] + '.vhd')
            disks = self._manager.list_disks()

            found = False
            for i in range(len(disks)):
                disk = disks[i]
                if disk.name == azure_config['test_vhd_name']:
                    found = True
                    break

            self.assertEqual(found, True,
                             'Expected disk: ' +
                             azure_config['test_vhd_name'] +
                             ' to be listed in DiskManager.list_disks')

            self._manager.destroy_disk(azure_config['test_vhd_name'])
            disks = self._manager.list_disks()
            found = False
            for i in range(len(disks)):
                disk = disks[i]
                if disk.name == azure_config['test_vhd_name']:
                    found = True
                    break

            self.assertEqual(found, False, 'Expected disk: '
                             + azure_config['test_vhd_name'] +
                             ' not to be listed in DiskManager.list_disks')

        def test_attach_blank_vhd(self):
            node_name = azure_config['test_vm_name']
            vhd_name = azure_config['test_vhd_name']

            self._manager.create_disk(azure_config['test_vhd_name'], 2)

            self._manager.attach_disk(node_name, vhd_name, 2)

            self._manager.detach_disk(node_name, vhd_name)

            self._manager.destroy_disk(vhd_name)

            all_disks = self._manager.list_disks()
            for i in range(len(all_disks)):
                disk = all_disks[i]
                if disk.name == vhd_name:
                    break
