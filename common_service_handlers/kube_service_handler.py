import os
import random
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from kubernetes.client.models.v1_namespace import V1Namespace
import base64


class KubeService():
    def __init__(self, app):

        # Init Kubernetes
        try:
            self.app = app
            print("Attempting to connect to Kubernetes")
            self.app.logger.info("Attempting to connect to Kubernetes")
            self.__set_config()
            self.v1 = client.CoreV1Api()
            self.v1batch = client.BatchV1Api()
            self.v1net = client.NetworkingV1Api()
            self.v1apps = client.AppsV1Api()
            
            terms = client.models.V1NodeSelectorTerm(
                match_expressions=[
                    {
                        'key': 'kubernetes.io/hostname',
                        'operator': 'In',
                        'values': ["gpu"]
                    }
                ]
            )
            self.node_selector = client.models.V1NodeSelector(node_selector_terms=[terms])
            self.node_affinity = client.models.V1NodeAffinity(
                required_during_scheduling_ignored_during_execution=self.node_selector
            )
            self.affinity = client.models.V1Affinity(node_affinity=self.node_affinity)

            namespace = 'aiai-ml'
            # container_name = namespace + '-app'
            # pod_name = container_name + '-pod'
            # job_name = pod_name + '-job'
            # self.cleanup_finished_kube_jobs(namespace=namespace)
            job_names = self.list_kube_jobs(namespace=namespace)
            # if job_names is None or job_name not in job_names:
            #     self.launch_kube_job(
            #         namespace=namespace,
            #         image='quay.io/aiai/alai_test:latest',
            #         pull_policy='Always',
            #         job_name=job_name,
            #         pod_name=pod_name,
            #         container_name=container_name,
            #         container_args=["-rf"],
            #         # run_command=["python", "--version"]
            #         run_command=["cp", "/home/project/test.txt", "/home/project/dsgfds.txt"]
            #         # run_command=["ls", "/home/project"]

            #     )

            print("Kubernetes env connected")
            self.app.logger.info("Kubernetes env connected")
        except Exception as ex:
            self.app.logger.info(ex)
            self.app.logger.exception(ex)
            print(ex)
    
    def launch_kube_job(self, namespace, image, pull_policy, job_name, pod_name, container_name, host_path, mount_path, container_args, run_command):
        # namespace = self.__create_namespace('aiai')
        job = self.__create_job(
           job_name, self.__create_pod_template(
                pod_name, self.__create_container(
                    image, container_name, pull_policy, mount_path, container_args, run_command
                ), host_path
            )
        )
        self.v1batch.create_namespaced_job(namespace, job)

    def list_kube_jobs(self, namespace):
        # deleteoptions = client.V1DeleteOptions()
        job_details = {}
        try:
            jobs = self.v1batch.list_namespaced_job(namespace, pretty=True, timeout_seconds=60)
        except ApiException as e:
            self.app.logger.info("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)

        for job in jobs.items:
            if job.status.succeeded == 1:
                job_details[job.metadata.name] = 'succeeded'
            elif job.status.failed == 1: 
                job_details[job.metadata.name] = 'failed'
            else:
                job_details[job.metadata.name] = None

        return job_details
        
    def cleanup_finished_kube_jobs(self, namespace, state='Finished'):
        # deleteoptions = client.V1DeleteOptions()
        try:
            jobs = self.v1batch.list_namespaced_job(namespace, pretty=True, timeout_seconds=60)
        except ApiException as e:
            self.app.logger.info("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)
        
        for job in jobs.items:
            self.app.logger.info(job)
            jobname = job.metadata.name
            jobstatus = job.status.conditions
            if job.status.succeeded == 1 or job.status.failed == 1:
                self.app.logger.info("Cleaning up Job: {}. Finished at: {}".format(jobname, job.status.completion_time))
                try: 
                    api_response = self.v1batch.delete_namespaced_job(jobname, namespace, grace_period_seconds= 0, propagation_policy='Background')
                    self.app.logger.info(api_response)
                except ApiException as e:
                    self.app.logger.info("Exception when calling BatchV1Api->delete_namespaced_job: %s\n" % e)
            else:
                if jobstatus is None and job.status.active == 1:
                    jobstatus = 'active'
                self.app.logger.info("Job: {} not cleaned up. Current status: {}".format(jobname, jobstatus))

        # self.__kube_delete_empty_pods(self, namespace)

        return

    def __kube_delete_empty_pods(self, namespace, phase='Succeeded'):
        deleteoptions = client.V1DeleteOptions()
        try:
            pods = self.v1.list_namespaced_pod(namespace, pretty=True, timeout_seconds=60)
        except ApiException as e:
            self.app.logger.info("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

        for pod in pods.items:
            self.app.logger.info(pod)
            podname = pod.metadata.name
            try:
                if pod.status.phase == phase:
                    api_response = self.v1.delete_namespaced_pod(podname, namespace)
                    self.app.logger.info("Pod: {} deleted!".format(podname))
                    self.app.logger.info(api_response)
                else:
                    self.app.logger.info("Pod: {} still not done... Phase: {}".format(podname, pod.status.phase))
            except ApiException as e:
                self.app.logger.info("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

        return

    def __set_config(self):
        """ Consults the environment for namespace and configmap name
        to load for configuration.
        Returns
        -------
        config: dict{}
            A dictionary of key: values with userpod configuration
        """

        incluster = os.getenv("PODLIB_INCLUSTER")
        if incluster and incluster == "true":
            config.load_incluster_config()
        else:
            config.load_kube_config()

    def __create_namespace(self, namespace):
        namespaces = self.v1.list_namespace()
        all_namespaces = []
        for ns in namespaces.items:
            all_namespaces.append(ns.metadata.name)

        if namespace in all_namespaces:
            self.app.logger.info(f"Namespace {namespace} already exists. Reusing.")
        else:
            namespace_metadata = client.V1ObjectMeta(name=namespace)
            self.v1.create_namespace(
                client.V1Namespace(metadata=namespace_metadata)
            )
            self.app.logger.info(f"Created namespace {namespace}.")

        return namespace

    def __create_container(self, image, name, pull_policy, mount_path, args, command):
        container = client.V1Container(
            image=image,
            name=name,
            image_pull_policy=pull_policy,
            args=args,
            command=command,
            resources=client.V1ResourceRequirements(
                limits={"nvidia.com/gpu": "2"}
            ),
            volume_mounts=[
                client.V1VolumeMount(
                    name="project",
                    mount_path=mount_path
                )
            ],
        )

        self.app.logger.info(
            f"Created container with name: {container.name}, "
            f"image: {container.image} and args: {container.args}"
        )

        return container

    def __create_pod_template(self, pod_name, container, host_path):
        pod_template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(
                volumes=[client.V1Volume(
                        name="project",
                        host_path=client.V1HostPathVolumeSource(
                            path=host_path,
                            type="Directory"
                        )
                    )
                ],
                node_selector={"node": "gpu"},
                restart_policy="Never", containers=[container]
            ),
            metadata=client.V1ObjectMeta(name=pod_name, labels={"pod_name": pod_name}),
        )

        return pod_template

    def __create_job(self, job_name, pod_template):
        metadata = client.V1ObjectMeta(name=job_name, labels={"job_name": job_name})

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=metadata,
            spec=client.V1JobSpec(backoff_limit=0, template=pod_template),
        )

        return job

    # def open_pod(self, 
    #              cmd: list, 
    #              pod_name: str, 
    #              namespace: str='bots', 
    #              image: str=f'{repository}:{tag}', 
    #              restartPolicy: str='Never', 
    #              serviceAccountName: str='bots-service-account'
    #              ):
    #     '''
    #     This method launches a pod in kubernetes cluster according to command
    #     '''
        
    #     api_response = None
    #     try:
    #         api_response = self.core_v1.read_namespaced_pod(name=pod_name,
    #                                                         namespace=namespace)
    #     except ApiException as e:
    #         if e.status != 404:
    #             print("Unknown error: %s" % e)
    #             exit(1)

    #     if not api_response:
    #         print(f'From {os.path.basename(__file__)}: Pod {pod_name} does not exist. Creating it...')
    #         # Create pod manifest
    #         pod_manifest = {
    #             'apiVersion': 'v1',
    #             'kind': 'Pod',
    #             'metadata': {
    #                 'labels': {
    #                     'bot': current-bot
    #                 },
    #                 'name': pod_name
    #             },
    #             'spec': {
    #                 'containers': [{
    #                     'image': image,
    #                     'pod-running-timeout': '5m0s',
    #                     'name': f'container',
    #                     'args': cmd,
    #                     'env': [
    #                         {'name': 'env_variable', 'value': env_value},
    #                     ]
    #                 }],
    #                 # 'imagePullSecrets': client.V1LocalObjectReference(name='regcred'), # together with a service-account, allows to access private repository docker image
    #                 'restartPolicy': restartPolicy,
    #                 'serviceAccountName': bots-service-account
    #             }
    #         }
            
    #         print(f'POD MANIFEST:\n{pod_manifest}')

    #         api_response = self.core_v1.create_namespaced_pod(body=pod_manifest,                                                          namespace=namespace)

    #         while True:
    #             api_response = self.core_v1.read_namespaced_pod(name=pod_name,
    #                                                             namespace=namespace)
    #             if api_response.status.phase != 'Pending':
    #                 break
    #             time.sleep(0.01)
            
    #         print(f'From {os.path.basename(__file__)}: Pod {pod_name} in {namespace} created.')
    #         return pod_name