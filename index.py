import os
import wget
import requests 
import zipfile
import shutil

target_folder = "."
repos = ['VortexdataNET/vortexdata.net', 'VarChar42/filerift-windows']


token = open('token.cfg', 'r').readline()

print(token)
gh_session = requests.Session()
gh_session.auth = ('VarChar42', token)

if not os.path.exists('temp'):
	os.makedirs('temp')

for repo in repos:
	owner, name = repo.split(sep='/', maxsplit=1)
	
	print ('> Downloading release for %s owned by %s' % (name, owner))

	result = gh_session.get(url = 'https://api.github.com/repos/%s/releases/latest' % repo).json()
	if 'message' in result and result['message'] == 'Not Found':
		print ('\t | Cant find release .. Skipping')
		continue
	
	if not 'name' in result:
		print ('\t | Something went wrong .. Skipping')
		print ('\t | Received message: %s' % result)
		continue
	
	dl_url 	= result['zipball_url']
	dl_file = 'temp/release_%s.zip' % result['id']
	
	print("\t | Release found: %s" % result['name'])
	print("\t | Starting download ...")
	dl_data = gh_session.get(dl_url)
	
	with open(dl_file, 'wb') as file:
		file.write(dl_data.content)
	
	print("\t | Saved as: %s" % dl_file)
	print("\t | Extracting zipball ...")
	
	with zipfile.ZipFile(dl_file, 'r') as zip_ref:
		zip_ref.extractall('temp')
		repo_folder = zip_ref.namelist()[0]
		
		
	print("\t | Moving release into target folder ...")
	shutil.move('temp/%s' % repo_folder, '%s/%s' % (target_folder, name))
	
	print("\t | Cleanup ... ")
	
	os.remove(dl_file)
	
	print("\t | Done!")
	
	