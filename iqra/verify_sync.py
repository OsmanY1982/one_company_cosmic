from core.cloud_sync import CloudSyncService

service = CloudSyncService()

# 获取本地同步状态
print('Local sync state:')
state = service.get_local_sync_state()
for item in state:
    print(f'  {item["table"]}: {item["local_count"]}')

# 获取云端摘要
print('\nCloud summary:')
summary = service.get_cloud_summary()
for table, count in summary.items():
    print(f'  {table}: {count}')
