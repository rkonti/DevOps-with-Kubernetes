# DevOps with Kubernetes

Submissions for the University of Helsinki course [DevOps with Kubernetes](https://devopswithkubernetes.com/).

## Exercises

### Chapter 2

* [1.1. Log output](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.1/log-output) — tag `1.1`
* [1.2. Todo app start](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.2/todo-app) — tag `1.2`
* [1.3. Declarative approach (log output)](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.3/log-output) — tag `1.3`
* [1.4. Declarative approach (todo app)](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.4/todo-app) — tag `1.4`
* [1.5. Todo app serves HTML](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.5/todo-app) — tag `1.5`
* [1.6. NodePort Service](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.6/todo-app) — tag `1.6`
* [1.7. External access with Ingress](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.7/log-output) — tag `1.7`
* [1.8. Todo app with Ingress](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.8/todo-app) — tag `1.8`
* [1.9. Ping-pong application](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.9/ping-pong) — tag `1.9`
* [1.10. Even more services](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.10/log-output) — tag `1.10`
* [1.11. Persisting data](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.11/volumes) — tag `1.11`
* [1.12. Project v0.6](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.12/todo-app) — tag `1.12`
* [1.13. Project v0.7](https://github.com/rkonti/DevOps-with-Kubernetes/tree/1.13/todo-app) — tag `1.13`

### Chapter 3

* [2.1. Connecting pods](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.1/log-output) — tag `2.1`
* [2.2. Project v1.0](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.2/todo-backend) — tag `2.2`
* [2.3. Keep them separated](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.3/namespaces) — tag `2.3`
* [2.4. Project v1.1](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.4/namespaces) — tag `2.4`
* [2.5. Documentation and ConfigMaps](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.5/log-output) — tag `2.5`
* [2.6. Project v1.2](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.6/todo-app) — tag `2.6`
* [2.7. Stateful applications](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.7/ping-pong) — tag `2.7`
* [2.8. Project v1.3](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.8/todo-backend) — tag `2.8`
* [2.9. Project v1.4](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.9/todo-backend) — tag `2.9`
* [2.10. Project v1.5](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.10/todo-backend) — tag `2.10` (monitoring stack in [monitoring](https://github.com/rkonti/DevOps-with-Kubernetes/tree/2.10/monitoring))

### Chapter 4

* [3.1. Pingpong GKE](https://github.com/rkonti/DevOps-with-Kubernetes/tree/3.1/ping-pong) — tag `3.1`
* [3.2. Back to Ingress](https://github.com/rkonti/DevOps-with-Kubernetes/tree/3.2/log-output) — tag `3.2`
* [3.3. To the Gateway](https://github.com/rkonti/DevOps-with-Kubernetes/tree/3.3/log-output) — tag `3.3`
* [3.4. Rewritten routing](https://github.com/rkonti/DevOps-with-Kubernetes/tree/3.4/ping-pong) — tag `3.4`
* [3.5. Project, step 14](https://github.com/rkonti/DevOps-with-Kubernetes/blob/3.5/kustomization.yaml) — tag `3.5`
* [3.6. Project, step 15](https://github.com/rkonti/DevOps-with-Kubernetes/blob/3.6/.github/workflows/main.yaml) — tag `3.6`
* [3.7. Project, step 16](https://github.com/rkonti/DevOps-with-Kubernetes/blob/3.7/.github/workflows/main.yaml) — tag `3.7`
* [3.8. Project, step 17](https://github.com/rkonti/DevOps-with-Kubernetes/blob/3.8/.github/workflows/delete.yaml) — tag `3.8`
* [3.9. DBaaS vs DIY](https://github.com/rkonti/DevOps-with-Kubernetes/tree/3.9#39-dbaas-vs-diy) — tag `3.9`
* [3.10. Project, step 18](https://github.com/rkonti/DevOps-with-Kubernetes/blob/3.10/todo-backend/manifests/backup-cronjob.yaml) — tag `3.10`


## 3.9 DBaaS vs DIY
Analyzing the pros and cons of DBaaS vs DIY:

| |DBaaS|DIY|
|---|---|---|
|Initial setup|Little work the provider does most of it you only need to enter secrets and tick boxes|A lot more work for setup|
|Cost|Higher longterm costs, even when idle|Lower long term costs as it runs on your own nodes|
|Maintenance|Provider handles all of the maintenance|All on you, you do all of the maintenance yourself|
|Backup|Automatic|You build them yourself|
|Ease of use|Easy but you have a lot less control|Harder but you maintain control|

TL;DR: DBaaS costs more but saves a lot of work, while DIY is cheaper but takes much more work.