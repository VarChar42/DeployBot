import os
import requests
import zipfile
import shutil
import platform
from utils.botconfig import init_config


def log(msg):
    print('\t | %s' % msg)


def run():
    config = init_config()
    config_settings = config['Settings']
    repos = config.items('Repos')

    target_folder = config_settings['TargetFolder']
    temp_folder = config_settings['TempFolder']
    token_file = config_settings['TokenFile']
    deployed_folder_permissions = config_settings['FilePermissions']

    try:
        github_username, github_token = open(token_file, 'r').readline().rstrip().split(sep=':', maxsplit=1)
    except ValueError:
        print('Invalid token config. Example: VarChar42:github_token')
        exit(1)

    gh_session = requests.Session()
    gh_session.auth = (github_username, github_token)

    print('Using GitHub account: %s' % github_username)

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    for project_name, repo in repos:
        owner, name = repo.split(sep='/', maxsplit=1)

        print('Deploying "%s"' % project_name)
        log('Downloading release for %s owned by %s' % (name, owner))

        result = gh_session.get(url='https://api.github.com/repos/%s/releases/latest' % repo).json()
        if 'message' in result and result['message'] == 'Not Found':
            log('Cant find release .. Skipping')
            continue

        if not 'name' in result:
            log('Something went wrong .. Skipping')
            log('Received message: %s' % result)
            continue

        log('Release found: %s' % result['name'])

        assets = result['assets']

        if len(assets) < 1:
            log('Release has no assets .. Skipping')
            continue

        asset = assets[0]
        log('Asset found: %s' % asset['name'])

        if not asset['name'].endswith('.zip'):
            log('Asset is not a zip file .. Skipping')
            continue

        dl_url = asset['url']
        dl_file = '%s/release_%s.zip' % (temp_folder, result['id'])

        log('Starting download ...')

        dl_data = gh_session.get(dl_url, headers={'Accept': 'application/octet-stream'})

        with open(dl_file, 'wb') as file:
            file.write(dl_data.content)

        log('Saved as: %s' % dl_file)
        log('Extracting archive ...')

        with zipfile.ZipFile(dl_file, 'r') as zip_ref:
            zip_ref.extractall(temp_folder)
            repo_folder = zip_ref.namelist()[0]

        log('Moving release into target folder ...')

        release_folder = '%s/%s/' % (target_folder, name)

        if os.path.exists(release_folder):
            log('Deleting existing folder ...')
            shutil.rmtree(release_folder)
        shutil.move('%s/%s' % (temp_folder, repo_folder), release_folder)

        if platform.system() == 'Linux':
            log('Applying file permissions ...')
            os.system('chmod -R %s %s' % (deployed_folder_permissions, release_folder))

        log('Cleanup ... ')

        os.remove(dl_file)

        log('Done! "%s" got deployed at %s' % (project_name, release_folder))


if __name__ == '__main__':
    run()
