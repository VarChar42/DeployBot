import os
import requests
import zipfile
import shutil
import platform

target_folder = '.'
deployed_folder_permissions = ''
repos = ['VortexdataNET/vortexdata.net', 'VarChar42/filerift-windows', 'VortexdataNET/src.vortexdata.net',
         'VarChar42/vortexdata.net']


def log(msg):
    print('\t | %s' % msg)


github_username, github_token = open('token.cfg', 'r').readline().split(sep=':', maxsplit=1)

gh_session = requests.Session()
gh_session.auth = (github_username, github_token)

if not os.path.exists('temp'):
    os.makedirs('temp')

for repo in repos:
    owner, name = repo.split(sep='/', maxsplit=1)

    print('> Downloading release for %s owned by %s' % (name, owner))

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
    dl_file = 'temp/release_%s.zip' % result['id']

    log('Starting download ...')

    dl_data = gh_session.get(dl_url, headers={'Accept': 'application/octet-stream'})

    with open(dl_file, 'wb') as file:
        file.write(dl_data.content)

    log('Saved as: %s' % dl_file)
    log('Extracting archive ...')

    with zipfile.ZipFile(dl_file, 'r') as zip_ref:
        zip_ref.extractall('temp')
        repo_folder = zip_ref.namelist()[0]

    log('Moving release into target folder ...')

    if os.path.exists(name):
        log('Deleting existing folder ...')
        shutil.rmtree(name)
    shutil.move('temp/%s' % repo_folder, '%s/%s/' % (target_folder, name))

    if platform.system() == 'Linux':
        log('Applying file permissions ...')
        os.system('chmod -R %s %s', (deployed_folder_permissions, name))

    log('Cleanup ... ')

    os.remove(dl_file)

    log('Done!')
