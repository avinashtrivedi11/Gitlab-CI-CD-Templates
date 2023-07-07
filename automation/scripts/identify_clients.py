import sys
import os
import yaml
import toml
import requests
import json
import base64

def get_clients(clients_string):
    """
    Converts comma separated string into a list of clients
    """
    return clients_string.split(',')

def get_latest_reference(repo, headers, client, branch, gitlab_url):
    """
    Returns the latest commit reference in the provided repo and branch
    """
    project_id = repo['project_id']

    try:
        response = requests.get(f"{gitlab_url}/projects/{project_id}/repository/branches/{branch}", headers=headers)
        branch_data = response.json()
        latest_state = branch_data["commit"]["id"]
        return latest_state if 'commit' in branch_data else None
    except Exception as e:
        print(f"Error while fetching latest reference: {e}")
        return None

def get_latest_deployment(repo, environment, headers, gitlab_url):
    """
    Returns the latest successful deployment in the provided environment
    """
    project_id = repo['project_id']
    env_name = environment

    try:
        response = requests.get(f"{gitlab_url}/projects/{project_id}/deployments?environment={env_name}&status=success&order_by=finished_at&sort=desc", headers=headers)
        deployments = response.json()

        # Get the latest successful deployment
        latest_successful_deployment = deployments[0]["deployable"]["commit"]["id"] if deployments else None
        return latest_successful_deployment
    except Exception as e:
        print(f"Error while fetching latest deployment: {e}")
        return None

def trigger_deployment(repo, deployments_to_trigger, client):
    """
    Adds the repo to be deployed to the client's deployments_to_trigger
    """
    if client not in deployments_to_trigger.keys():
        deployments_to_trigger[client] = []
    deployments_to_trigger[client].append(repo['name'])

def create_dynamic_pipeline(clients, deployments_to_trigger, image_tag):
    """
    Creates a dynamic pipeline config using pyyaml and writes it to a file
    """
    # Filter out deployments_to_trigger for clients with no deployments
    deployments_to_trigger = {client: deployments for client, deployments in deployments_to_trigger.items() if len(deployments) > 0}
    deployments_to_trigger_json = json.dumps(deployments_to_trigger)
    deployments_to_trigger_base64 = base64.b64encode(deployments_to_trigger_json.encode()).decode()

    # Create the dynamic pipeline config
    dynamic_config = {
        'stages': ['generate','trigger'],
        'generate_client_pipeline': {
            'stage': 'generate',
            'image': 'python:3.10',
            'before_script': 'pip install pyyaml toml',
            'script': f'python3 -c "$(curl -fsSL https://github.com/avinashtrivedi11/Gitlab-CI-CD-Templates/raw/dashboard-ci/automation/scripts/generate_pipeline.py)" {deployments_to_trigger_base64}',
            'artifacts': {
                'paths': [
                    'trigger-msa-*.yml'
                ]
            }
        }
    }

    # Create another job to add in dynamic_config for each client
    for client in deployments_to_trigger.keys():
        dynamic_config[f'trigger_{client}_pipeline'] = {
            'stage': 'trigger',
            'trigger': {
                'include': [{
                    'artifact': f'trigger-msa-{client}.yml',
                    'job': 'generate_client_pipeline'
                }],
                'strategy': 'depend',   
            },
            'needs': ['generate_client_pipeline'],
        }

    # Write the dynamic pipeline config to a file
    with open('trigger-deployment.yml', 'w') as outfile:
        yaml.dump(dynamic_config, outfile, default_flow_style=False)

    print(f'Generated trigger-deployment.yml for {clients} clients')

def main():
    """
    Main function for the deployment script
    """
    clients_string = os.environ['CLIENTS']
    image_tag = os.environ['IMAGE_TAG']
    raw_token_config = os.environ['TOKEN_CONFIG']
    latest_deployment_check = os.environ['LATEST_DEPLOYMENT_CHECK']
    clients = get_clients(clients_string)
    gitlab_url = "https://gitlab.com/api/v4"
    deployments_to_trigger = {}

    # Get config file for client and check latest deployments
    for client in clients:
        try:
            raw_deployment_config = os.environ[f'{client}_DEPLOYMENT_CONFIG']
            deployment_config = toml.loads(raw_deployment_config)
            branch = deployment_config['client']['branch']
            client_environment = deployment_config['client']['environment']
            deployed_repos = deployment_config['client']['repos']
            # print(f"Deployed repos for {client}: {deployed_repos}")
            token_config = toml.loads(raw_token_config)

            for deployed_repo in deployed_repos:
                for repo in token_config['repos']:
                    print(f"{client}, {deployed_repo['name']}, {repo['name']}")
                    if deployed_repo['name'] == repo['name']:
                        api_token = repo['api_token']
                        headers = {"Private-Token": api_token}
                        response = requests.get(f"{gitlab_url}/projects/{repo['project_id']}/environments", headers=headers)
                        print(response.json())
                        if response.status_code == 200:
                            environments = response.json()
                            target_environment = next((env['name'] for env in environments if env['name'] == client), None)
                        else:
                            target_environment = None    
                        print(f"Target environment:{target_environment}, Repo:{repo}")
                        if target_environment is None:
                            # Create new environment
                            new_env_payload = {'name': client_environment} 
                            response = requests.post(f"{gitlab_url}/projects/{repo['project_id']}/environments", headers=headers, json=new_env_payload)
                            print(response.json())
                            target_environment = client_environment if response.status_code == 201 else None
                            print(f"Target environment:{target_environment}, Repo:{repo}")
                        if target_environment is not None:
                            latest_reference = get_latest_reference(repo, headers, client, branch, gitlab_url)
                            latest_deployment = get_latest_deployment(repo, target_environment, headers, gitlab_url)
                            if latest_deployment_check == "true":
                                if latest_deployment is None or latest_deployment != latest_reference:
                                    trigger_deployment(repo, deployments_to_trigger, client)
                            else:
                                trigger_deployment(repo, deployments_to_trigger, client)
                        break
        except Exception as e:
            print(f"Error while deploying for client {client}: {e}")
            continue

    # Create dynamic pipeline and write it to a file
    create_dynamic_pipeline(clients, deployments_to_trigger, image_tag)

if __name__ == "__main__":
    main()
