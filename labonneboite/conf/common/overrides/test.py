import os

ES_INDEX = 'labonneboite_unit_test'
DB_NAME = os.environ.get('DB_NAME', 'lbb_test2')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'lbb_test')
DB_USER = os.environ.get('DB_USER', 'lbb_test')
ENABLE_TIMEIT_TIMERS = False
API_KEYS = {
    'labonneboite': 'dummykey',
    'emploi_store_dev': 'anotherdummykey',
}
