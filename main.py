import datetime
import os

from dateutil.tz import tzutc
from kubernetes import client, config


def main():
    is_skip_all = True
    number_days = int(os.getenv('NUMBER_DAYS', 7))
    namespace = os.getenv('NAMESPACE', 'default')
    is_cluster = bool(os.getenv('IS_CLUSTER', True))
    label_selector = os.getenv('LABEL_SELECTOR', 'app=migration')
    propagation_policy = os.getenv('PROPAGATION_POLICY', 'Background')

    if is_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config()
    client_job = client.BatchV1Api()
    instances = client_job.list_namespaced_job(namespace=namespace, label_selector=label_selector)
    now = datetime.datetime.utcnow().replace(tzinfo=tzutc())

    for job in instances.items:
        job_name = job.metadata.name
        start_time = job.status.start_time

        if is_lower_one_week(now=now, time=start_time, number_days=number_days):
            continue

        conditions = job.status.conditions

        if conditions:
            check_time = conditions[0].last_probe_time
            if not is_lower_one_week(now=now,
                                     time=check_time,
                                     number_days=number_days):
                delete_job(job_name=job_name, namespace=namespace, propagation_policy=propagation_policy)
                is_skip_all = False
                continue
        else:
            label_selector_for_pod = f'job-name={job_name}'
            if not is_pod_running(namespace=namespace, label_selector=label_selector_for_pod):
                delete_job(job_name=job_name, namespace=namespace)
                is_skip_all = False
                continue
    if is_skip_all:
        print(f'Unable for finding jobs being larger than {number_days} days')


def delete_job(job_name, namespace, propagation_policy):
    try:
        client.BatchV1Api().delete_namespaced_job(name=job_name, namespace=namespace,
                                                  propagation_policy=propagation_policy)
    except Exception as e:
        print(f'Delete job name {job_name} is failed due to {str(e)}')
    else:
        print(f'Delete job name {job_name} is successful')


def is_pod_running(namespace, label_selector):
    res = client.CoreV1Api().list_namespaced_pod(
        namespace=namespace, label_selector=label_selector
    )
    container_statues = res.items[0].status.container_statuses
    for container_status in container_statues:
        if not container_status.state.running:
            return False
    return True


def is_lower_one_week(now, time, number_days):
    days = now - time
    if days.days < number_days:
        return True
    return False


if __name__ == '__main__':
    main()
