import os

ES_INDEX = 'labonneboite_unit_test'
DB_HOST = '127.0.0.1'
DB_PORT = 3307
DB_NAME = os.environ.get('DB_NAME', 'lbb_test')
DB_USER = os.environ.get('DB_USER', 'lbb_test')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

ENABLE_TIMEIT_TIMERS = False
API_KEYS = {
    'labonneboite': 'dummykey',
    'emploi_store_dev': 'anotherdummykey',
}
