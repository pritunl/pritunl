from pritunl.settings.group_mongo import SettingsGroupMongo

class SettingsMongo(SettingsGroupMongo):
    group = 'mongo'
    fields = {
        'tran_max_attempts': 6,
        'tran_ttl': 10,
        'queue_max_attempts': 3,
        'queue_ttl': 15,
        'task_max_attempts': 3,
        'task_ttl': 30,
    }
