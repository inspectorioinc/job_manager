import datetime
import os

from dateutil.tz import tzutc
from kubernetes import client, config


def main():
    number_days = int(os.getenv('NUMBER_DAYS', 7))
    namespace = os.getenv('NAMESPACE', 'default')
    is_cluster = bool(os.getenv('IS_CLUSTER', True))
    if is_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config()
    client_job = client.BatchV1Api()
    label_selector = 'app=migration'
    instances = client_job.list_namespaced_job(namespace=namespace, label_selector=label_selector)
    now = datetime.datetime.utcnow().replace(tzinfo=tzutc())
    for job in instances.items:
        job_name = job.metadata.name
        conditions = job.status.conditions
        if conditions:
            last_probe_time = conditions[0].last_probe_time
            if not is_lower_one_week(now=now,
                                     time=last_probe_time,
                                     number_days=number_days):
                try:
                    client_job.delete_namespaced_job(name=job_name, namespace=namespace)
                except Exception as e:
                    print(f'Delete job name {job_name} is failed due to {str(e)}')
                else:
                    print(f'Delete job name {job_name} is successful')


def is_lower_one_week(now, time, number_days):
    days = now - time
    if days.days < number_days:
        return True
    return False


if __name__ == '__main__':
    main()
