import os
import requests
import zipfile
import shutil
import platform
from datetime import datetime
from utils.botconfig import init_config
from utils.releasecache import save_release_cache, load_release_cache


def log(msg):
    print('\t | %s' % msg)


def print_rate_limit_info(gh_session):
    result = gh_session.get(url='https://api.github.com/rate_limit').json()

    if 'rate' in result:
        rate = result['rate']

        limit = rate['limit']
        used = rate['used']
        reset = rate['reset']
        remaining = limit - used

        human_reset_time = datetime.utcfromtimestamp(reset).strftime('%Y-%m-%d %H:%M:%S')

        print('Remaining GitHub api calls: %s (%s/%s) Last reset: %s' % (remaining, used, limit, human_reset_time))

        return remaining
    else:
        print('Could not fetch github api rate limit')
        return -1


def run():
    release_cache = load_release_cache()

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

    if print_rate_limit_info(gh_session) < len(repos) * 2:
        print('There are not enough api calls left! Aborting!')
        return

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    for project_name, repo in repos:
        owner, name = repo.split(sep='/', maxsplit=1)

        print('Deploying (%s)' % project_name)
        log('Downloading release for (%s) owned by (%s)' % (name, owner))

        release = gh_session.get(url='https://api.github.com/repos/%s/releases/latest' % repo).json()
        if 'message' in release and release['message'] == 'Not Found':
            log('Cant find release .. Skipping')
            continue

        if 'name' not in release:
            log('Something went wrong .. Skipping')
            log('Received message: %s' % release)
            continue

        assets = release['assets']
        is_zipball = False

        if len(assets) < 1:
            log('Release has no assets .. Using zipball instead')
            is_zipball = True

        release_id = release['id']

        if project_name in release_cache and release_cache[project_name] == release_id:
            log('Deployed release is already up to date')
            continue

        dl_headers = {}

        if not is_zipball:
            asset = assets[0]
            log('Using asset (%s) from release (%s)' % (asset['name'], release['name']))

            if not asset['name'].endswith('.zip'):
                log('Asset is not a zip file .. Skipping')
                continue

            dl_url = asset['url']
            dl_file = '%s/release_%s.zip' % (temp_folder, release_id)
            dl_headers = {'Accept': 'application/octet-stream'}
        else:
            dl_url = release['zipball_url']
            dl_file = '%s/release_%s.zip' % (temp_folder, 'zipball')

        log('Starting download ...')

        dl_data = gh_session.get(dl_url, headers=dl_headers)

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

        release_cache[project_name] = release_id

    save_release_cache(release_cache)


if __name__ == '__main__':
    run()
