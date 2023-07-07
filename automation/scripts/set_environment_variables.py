import os
import toml

DEPLOYMENT_CONFIG_FILE = os.environ.get("DEPLOY_CONFIG")
CI_PROJECT_NAME = os.environ.get("CI_PROJECT_NAME")

deployment_config_toml = toml.loads(DEPLOYMENT_CONFIG_FILE)

repos = deployment_config_toml['client']['repos']

# Set root folder and app name
root_folder = [repo['root_folder'] for repo in repos if repo['name'] == CI_PROJECT_NAME]
print(f'export ROOT_FOLDER="{root_folder[0]}"')
app_name = [repo['app_name'] for repo in repos if repo['name'] == CI_PROJECT_NAME]
print(f'export APP_NAME="{app_name[0]}"')

environment_variables = [repo['env_vars'][0] for repo in repos if repo['name'] == CI_PROJECT_NAME]
# Check if environment_variables list is not empty
if environment_variables:
    for env, value in environment_variables[0].items():
        print(f'export {env}="{value}"')
