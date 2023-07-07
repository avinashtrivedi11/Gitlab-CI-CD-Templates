import sys
import yaml
import toml
import os
import json
import base64

def load_config(client):
    """
    Load client configuration from environment variable
    """
    raw_deployment_config = os.environ.get(f'{client}_DEPLOYMENT_CONFIG')
    deployment_config = toml.loads(raw_deployment_config)
    return deployment_config, raw_deployment_config

def add_repo_to_config(repo, repos_to_trigger, dynamic_config, path_prefix):
    """
    Add repo details to dynamic configuration if it needs to be triggered
    """
    repo_name = repo["name"]
    if repo_name in repos_to_trigger:
        dynamic_config["trigger_repos"]["parallel"]["matrix"].append({
            "PROJECTS": repo_name,
            "PREFIX": f'{path_prefix}-{repo["type"]}',
        })

def generate_dynamic_config(client, repos_to_trigger, image_tag, path_prefix, vpn_config):
    """
    Generate dynamic config for client deployments
    """
    deployment_config, raw_deployment_config = load_config(client)
    branch = deployment_config['client']['branch']
    environment = deployment_config['client']['environment']
    dynamic_config = {
        'stages': ['trigger'],
        'trigger_repos': {
            'stage': 'trigger',
            'trigger': {
                'project': '$PREFIX/$PROJECTS',
                'branch': branch,
                'strategy': 'depend'
            },
            'parallel': {
                'matrix': []
            },
            'variables': {
                'ENVIRONMENT': client,
                'DEPLOY_ENVIRONMENT': environment,
                'DEPLOY_CONFIG': raw_deployment_config,
                'BRANCH': branch,
                'TAG': image_tag,
                'VPN_CONFIG': vpn_config
            },
        }
    }

    for repo in deployment_config["client"]["repos"]:
        add_repo_to_config(repo, repos_to_trigger, dynamic_config, path_prefix)
    return dynamic_config

def main():
    """
    Main function for the deployment script
    """
    deployments_to_trigger_base64 = sys.argv[1]
    image_tag = os.environ.get('IMAGE_TAG')
    path_prefix = os.environ.get('PATH_PREFIX')
    vpn_config = os.environ.get('VPN_CONFIG')

    deployments_to_trigger_json = base64.b64decode(deployments_to_trigger_base64).decode()
    deployments_to_trigger = json.loads(deployments_to_trigger_json)
    print("Deployments to be triggered")
    print(json.dumps(deployments_to_trigger, indent=2))
    for client, repos_to_trigger in deployments_to_trigger.items():
        dynamic_config = generate_dynamic_config(client, repos_to_trigger, image_tag, path_prefix, vpn_config)
        # Save the dynamic configuration to a file with a unique name for each client
        with open(f'trigger-msa-{client}.yml', 'w') as f:
            yaml.dump(dynamic_config, f)
        print(f'Generated trigger-msa-{client}.yml for {client} client')

if __name__ == '__main__':
    main()
