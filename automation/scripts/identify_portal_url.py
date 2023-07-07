import os
import toml
import yaml

def get_clients(clients_string):
    """
    Converts comma separated string into a list of clients
    """
    return clients_string.split(',')

def generate_automation_test_pipeline(clients_portal_urls):
    # Reads environment variables for repo path and branch
    automation_testing_repo_path = os.environ['AUTOMATION_TESTING_REPO_PATH']
    automation_testing_repo_branch = os.environ['AUTOMATION_TESTING_REPO_BRANCH']
    print(automation_testing_repo_branch, automation_testing_repo_path)
    # Defines dynamic_config for triggering automation tests
    dynamic_config = {
        'stages': ['trigger'],
        'trigger_automation_test': {
            'stage': 'trigger',
            'trigger': {
                'project': automation_testing_repo_path,
                'branch': automation_testing_repo_branch,
                'strategy': 'depend'
            },
            'parallel': {
                'matrix': []
            },
        }
    }
    for client_portal_url in clients_portal_urls:
        dynamic_config["trigger_automation_test"]["parallel"]["matrix"].append({
                "PORTAL_URL": client_portal_url,
            })
    return dynamic_config

def main():
    # Gets comma separated clients string from environment variables and split them into a list
    clients_string = os.environ['CLIENTS']
    clients = get_clients(clients_string)
    print(clients)
    clients_portal_urls = []  # To store portal URLs of all clients

    for client in clients:
        # For each client, loads TOML deployment configuration from environment variable
        raw_deployment_config = os.environ[f'{client}_DEPLOYMENT_CONFIG']
        deployment_config_toml = toml.loads(raw_deployment_config)
        portal_url = deployment_config_toml['client']['portal_url']
        print(client, portal_url)

        # Adds the portal_url to the clients_portal_urls list
        clients_portal_urls.append(portal_url)

    # Generates the dynamic configuration for the automation test pipeline
    dynamic_config = generate_automation_test_pipeline(clients_portal_urls)

    # Writes the dynamic configuration to a YAML file
    with open(f'trigger-automation-test.yml', 'w') as f:
        yaml.dump(dynamic_config, f)
    print(f'Generated trigger-automation-test.yml')

if __name__ == "__main__":
    main()
