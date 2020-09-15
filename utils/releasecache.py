import os

cache_file = 'releasecache.dat'


def load_release_cache():
    cache = {}
    if os.path.isfile(cache_file):
        with open(cache_file, 'r') as file:
            content = file.readline().split(';')
            for item in content:
                key_value = item.split(':')
                if len(key_value) != 2:
                    continue
                cache[int(key_value[0])] = int(key_value[1])

    return cache


def save_release_cache(cache):
    with open(cache_file, 'w') as file:
        content = ';'.join(['%s:%s' % (key, value) for key, value in cache.items()])
        file.write(content)
