Azure playbooks requires installing the following items:
* azure.azcollection: ```ansible-galaxy collection install azure.azcollection```
* Azure Ansible requirements: ```pip install -r https://raw.githubusercontent.com/ansible-collections/azure/dev/requirements-azure.txt```

Note: To see output of playbooks like *get_subscriptions.yml*, run with -vvv.
I.e., ```ansible-playbook get_subscriptions.yml -vvv```